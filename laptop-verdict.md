# Can the laptop handle it?

*Measured, not guessed. Everything below was run on this machine.*

---

## The machine

| | |
|---|---|
| CPU | AMD Ryzen 3 3250U — 2 cores / 4 threads, 2.6 GHz |
| RAM | 5.9 GB total, **0.9 GB free** |
| GPU | AMD Radeon (Vega 3, `gcn-5`), 2 GB shared, driver 31.0.21923.14000 |
| Disk | **19.2 GB free** of 221 GB |
| OS | Windows 10 Home, build 19045 (22H2) |
| Browsers | Chrome 154, Edge 155 — both modern |

It is a 2020 budget laptop. Two cores. The RAM, not the GPU, is what will bite you.

---

## The decisive test: WebGPU works

This mattered more than anything else, because the whole project family leans on it.

- `navigator.gpu` is available, secure context confirmed.
- Adapter: `amd` / `gcn-5`. Device requested in ~20–30 ms.
- Usable features include `shader-f16`, `timestamp-query`, `subgroups`,
  `float32-filterable`, `texture-compression-bc`.

Raw throughput, two independent measurements that agree:

| Test | Result |
|---|---|
| Compute, 4M elements × 2000 dependent FMAs | **73.8 GFLOPS**, results verified correct |
| Fragment, 2048² target, 200 ops/pixel | **71.8 Mpix/s** (58 ms/frame) |

Two different tests landing in the same place means the number is real.

**Verdict: yes, WebGPU runs here.** It is slow, but it is not broken, and that
is the difference between "build it" and "give up".

---

## What that means on the actual renderer

Measured with the renderer itself, timing the GPU directly. These figures are
for the **65-facet brilliant** (the fuller cut, added later) at 6 wavelengths,
3 internal bounces and no AA:

| Internal resolution | Pixels | ms/frame (median of 5) | fps |
|---|---|---|---|
| 500 × 350 | 175 k | 12.7 | 79 |
| **912 × 638 (full pane)** | **582 k** | **36** | **28** |
| 2000 × 1400 | 2.8 M | 73 | 14 |

The prism preset does 912 × 638 in 15 ms — 68 fps.

> **Read the spread, not the digit.** Repeated runs of the *same* 912 × 638
> brilliant setting gave 44.5, 35.5, 36.3, 36.7 and 36.3 ms — a 25% spread, and
> an earlier reading of that identical setting was 21 ms. A single number from
> an integrated GPU inside a browser is not reproducible to two digits. Budget
> from the median and expect ±30%. The 16.9 ms figures from the earlier 25-facet
> build are subject to the same caveat; the fuller cut also does ~2.6× the plane
> intersections, so some of the increase is real work.

> **Correction.** My first version of this table showed 288 ms at 912×678 —
> roughly 17× worse. Those numbers came from the build with the entry-slab bug,
> where every pixel traced a full path through the stone instead of most of them
> missing it. The figures above are from the fixed shader. I am leaving this note
> in because a benchmark from a broken build is worse than no benchmark.

Cost scales as you would expect:

| Knob | Effect at 912 × 678 |
|---|---|
| wavelengths 3 → 24 | 12 → 57 ms |
| bounces 1 → 8 | 12.5 → 32 ms (sublinear — paths die out early) |
| AA 1 → 2 → 4 samples/pixel | 16 → 45 → 90 ms |

Wavelengths are the dominant cost: dispersion is where the time goes.

### The design decision this actually forces

Full-resolution interactive rendering **is** achievable here at sensible
settings — around 28 fps at full pane with 6 wavelengths and 3 bounces. The top
end (20 wavelengths, 6 bounces, 2× AA) measures 248 ms, i.e. 4 fps: that is a
still, not a turntable.

Refinement is therefore implemented, not merely recommended. Once the view has
been still for 600 ms the renderer re-draws itself once at 4× AA and 16
wavelengths, then **stops submitting work entirely** until something changes.
That last part is the point: a refined frame costs ~140 ms, so repeating it every
frame would be a permanent stutter rather than a settle, and would keep the GPU
busy forever on a page nobody is touching. Grabbing the stone also stops the
turntable, so letting go is what settles it.

---

## Project by project

| Project | On this laptop? |
|---|---|
| **Prism** (engine) | Yes. Full-resolution interactive at sane settings — this is the whole bet, and it clears. |
| **Carat** (jeweller page) | Yes. It is Prism plus sliders. |
| **The Directory** | Yes — **built**. Static pages, no server, no build step. |
| **Shade** | Yes. Small and cheap. |
| **Sparkle Card** | Yes, but exports take seconds at quality. Make it a batch job, not live. |
| **Facet** (gem design) | Yes — same engine as Prism. |
| **Reverb** (acoustics) | **No.** Wave simulation is far heavier than ray tracing. Prototype only; plan for cloud or a real GPU. |
| Anything ML / LLM locally | **No.** |

### The real bottleneck is RAM

0.9 GB free out of 5.9 GB is the headline risk, worse than the GPU. Node, the
editor, Electron and Edge were already holding ~1.5 GB between them. So:

- Close Edge while developing. It was holding ~670 MB across four processes.
- Keep dependencies tiny. Prefer plain ES modules and a hand-written static
  server over Vite/webpack/Next. A single `node_modules` can be several GB, and
  you have 19 GB of disk.
- One dev server and one browser tab, not six.

---

## What is now in the repo

```
prism/
  reference/optics.py     validated physics reference (numpy), 8 checks pass
  web/gem.html            WebGPU spectral renderer: orbit, sliders, PNG export
  renders/                exported frames
directory/
  index.html              searchable, filterable listing
  app.js                  filtering and rendering (no framework)
  styles.css              all styling
  data/jewellers.js       the data — the file you edit
  README.md               how to fill it, host it, and charge for it
probe/gpu-probe.html      hardware capability probe (WebGPU + benchmarks)
laptop-verdict.md         this file
```

`prism/web/gem.html` runs standalone — open it in Chrome. Drag to orbit, wheel
to zoom. Sliders for internal resolution, wavelengths, bounces, dispersion,
exposure, AA. Two presets: prism and 65-facet brilliant. "export png" writes a
frame. `window.__prism` exposes `stats`, `configure`, `bench`, `tick`,
`capture`, `exportPng`, `info`, `setCamera`.

`directory/index.html` also runs standalone — open it, no server needed. The
data is a `<script>` rather than JSON on purpose: `fetch()` of a local JSON file
is blocked off disk, a `<script src>` is not.

---

## Five bugs, and what each one taught

1. **Probe asked for 65,536 workgroups**, one over the 65,535 limit. The
   dispatch was invalid and the benchmark cheerfully reported a number anyway.
   *Validate GPU results, don't just time them.*
2. **`intersectEntry` computed only the entry slab.** A ray that misses a
   convex solid still reports a positive entry, because any plane it violates
   from outside yields positive `t`. Every ray "hit", so the stone filled the
   entire screen. *Ray-vs-polyhedron needs both slabs.*
3. **FPS read 0 because the tab was hidden.** Chrome throttles
   `requestAnimationFrame` to nothing on a background tab. *Time the GPU
   directly; never trust rAF for a benchmark.*
4. **A single central ray was degenerate** — it landed exactly on the culet,
   where two facets meet. *Fire a bundle across the table instead.*
5. **One of my own test expectations was wrong.** I wrote diamond's
   normal-incidence reflectance as 1.5%; it is 17.2%. Diamond throws a sixth of
   the light straight back at you, which is precisely why it out-sparkles
   glass. The code was right; my arithmetic was not.

---

## Session 2: three more, and one thing I cannot test

6. **The `res` option took a fraction, not pixels.** I passed `res: 912` meaning
   "912 px wide". The renderer read it as "912× the canvas", asked the device for
   a 1.2-million-pixel texture, failed validation, and then poisoned *every*
   later GPU call with "invalid due to a previous error". Through all of it the
   benchmark reported a cheerful **63.5 fps** — because a pipeline that submits
   nothing is extremely fast. Now clamped to 0.05–2.0. *An invalid pipeline
   benchmarks beautifully. Validate the output, not just the speed.*
7. **The star facets were a guess, and the guess was wrong.** I picked the star
   ring's plane distance by eye; the resulting cone sat below the table, so it
   swallowed the entire crown and the "brilliant" rendered as a smooth dome with
   a pinhead table. The star plane has to pass through the **midpoint of a table
   edge** — derived rather than guessed, the star triangles appear immediately.
   *Facet geometry is a derivation, not a vibe.*
8. **Two cones that share a rim are nested.** The 16 upper-girdle facets were
   mathematically present and completely invisible: a shallower cone always
   hides a steeper one touching the same circle. Pulling the girdle-facet planes
   3% inside the girdle circle is what makes them bind and show.

And one honest limitation: **`requestAnimationFrame` never fires in a background
tab** — measured, 0 frames in 1.5 s. So the live draw loop (auto-refine, the
turntable, the FPS readout) cannot be exercised headlessly at all. Everything
actually verified above was driven through the API instead. I added a `tick()`
hook for exactly this reason, and used it to confirm the settle sequence: draft
(AA 1) → one refined frame (AA 4, 16 wavelengths) → then it stops drawing, and
the turntable correctly keeps drawing instead of resting.

---

## Session 3: the preset that was diamond, and proof the gap is real

9. **The `prism` preset was made of diamond.** Both presets shared one material,
   `n = 2.38 + 0.0115/λ²` — diamond — and for a *prism* that is wrong in a way
   that destroys the only thing the preset exists to show. At n = 2.38 the
   critical angle is 24.8°, so nearly every ray total-internally-reflected and
   almost nothing transmitted through the far face to carry a spectrum out. The
   preset named "prism" rendered as a grey wedge. It now has its own BK7-ish
   glass constants (`1.5046 + 0.0042/λ²`), and the material is chosen inside
   `setPreset` next to the geometry, so the two cannot drift apart again.

One deliberate design change, recorded because the whole portfolio design now
depends on it: the backdrop became a **flat constant** instead of
`env(rd) * 0.05`. An exported frame therefore has exactly one background colour,
`#222326`, which is what lets the case-study page use that same colour and show
the hero frame with no visible edge at all — the stone sits on the page instead
of inside a picture.

And one negative result, which is the useful part. Fixing the material did make
the prism transmit properly — and it still renders **grey, not rainbow**. That is
not a bug, it is the environment. Dispersion is only *visible* when the source is
small relative to the angular spread it causes: a broad softbox reflected in a
facet is a broad white patch, and the wavelength-dependent bend is smeared
straight back into white. Four much tighter, much brighter illuminants made the
glints on the brilliant slightly harder and brighter and *still* produced no
colour, so that change was reverted rather than kept on a hunch.

So "you can compute dispersion perfectly and still have nothing to refract" is
now something measured rather than assumed. The HDRI is not a nice-to-have; it
is the difference between a correct renderer and a convincing one.

---

## Session 4: the renderer that would not say why

This one arrived as a bug report rather than a measurement. Loading the deployed
page from GitHub Pages on this machine printed:

```
init failed: No WebGPU adapter found.
```

True, and useless. `navigator.gpu` existed, so WebGPU was present; the adapter
simply never answered. The old code asked exactly once, and asked specifically:

```js
const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
if (!adapter) throw new Error("No WebGPU adapter found.");
```

Two faults in three lines.

**It asked for the fast GPU and never fell back.** A `high-performance` hint is
not a promise: on some systems the request is refused outright rather than
answered with the only GPU the machine has. It now makes four requests in order
— high-performance, plain, low-power, software — and reports which one answered,
so a software adapter can no longer pass itself off as a real one in the readout.

**It named the symptom and not the cause.** "No adapter" covers three unrelated
problems with three unrelated remedies: hardware acceleration switched off, the
GPU on the WebGPU blocklist, or the GPU busy or short of memory. The message now
says so, in the order worth checking, instead of leaving the reader to guess.

This is deliberately **not** counted among the nine. All nine of those produced a
*plausible number from a broken renderer* — a confident frame rate from a
pipeline that drew nothing. This one produced no number at all: a milder and
quite different failure. The lesson still rhymes, though, because the output was
never validated against the machine it would really run on.

**Resolved the same day, and the machine was never at fault.** Chromium on this
laptop had been getting a real adapter all along — `amd gcn-5`, from a plain
launch carrying no GPU flags — while Edge reported *every* accelerated feature
disabled: WebGL, rasterisation, video decode and encode, GPU compositing, 2D
canvas and WebGPU together. That whole set going dark is the signature of
acceleration switched off for the browser, not of a blocklist contending with one
feature; a WebGPU-only entry disables WebGPU and nothing else. The cause was
`hardware_acceleration_mode.enabled = false`, which lives in the browser's
`Local State`, *not* in the per-profile `Preferences` file where the first search
looked — which is why the first answer was wrong. Restoring the setting made the
renderer run.

The transferable lesson is not about browsers. **A failure that names its symptom
and not its cause hands the whole investigation to whoever reads it.** Four words
sent the diagnosis down two wrong paths before the right one turned up.

---

## Honest status of the renderer

It works, it is physically motivated, and it now draws a real **65-facet
brilliant** — table, 8 stars, 8 bezels, 16 upper-girdle, a girdle band, 16
lower-girdle and 8 pavilion mains, at the real angles. The star facets were the
hard part; see item 7 above.

It is still not *dazzling*. The "fire" (dispersion) is computed, correct, and
barely visible, because a synthetic studio environment does not have the sharp
bright-against-dark structure that makes facets flash. On a dark backdrop the
stone now at least reads as a stone rather than a grey rock, but the coloured
flashes a photograph shows are not there yet.

The encouraging part is that closing that gap is now one well-defined job — a
real HDRI — rather than a list of unknowns.

Do not read that as a failure. It is a correct engine that needs art direction,
which is a completely different problem from "does the physics work" — and the
physics working is the part that is hard to copy.

## The reference model has a real limitation

`light_return()` sweeps pavilion angle and produces a sensible-looking curve
for crown glass — near zero until the critical angle (41.1°), then high, then
falling off. For diamond it peaks at ~45° and **does not** reproduce the
textbook ~40.75° optimum, because it is a 2-D cross-section with no crown
geometry.

That limitation lines up with your own rule in the Carat plan: **no grading
claims, ever.** This model is a mechanism, not a grade. Keep it that way.

---

## If I were doing the next session

1. **A real HDRI.** This is now the single biggest visual win, and the only one
   left that matters. Bright softboxes against a dark surround, as a texture
   instead of an analytic function. Cheap: one extra binding and a generated
   equirect image.
2. **Look at the material.** Everything is a pure dielectric with a Cauchy
   index, so nothing can ever read as *coloured* stone. Real gems absorb.
3. **A proper tonemap** (ACES or similar) instead of raw Reinhard, which
   flattens exactly the highlights a gem is supposed to flash with.
4. **The Directory, filled in.** The site is built and works; it is full of
   placeholders. The ten real jewellers are still the actual bottleneck.
5. Only then go back to the jeweller in the Carat plan. The engine exists now;
   the sale is still the unproven part.
