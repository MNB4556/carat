# The Directory

Independent jewellers who take on custom work. Static site, no build step, no dependencies,
no server required.

Open `index.html` in a browser. That is the whole deployment.

## Why this exists (two jobs, one file)

1. **A public directory.** People search "bespoke jeweller Leeds" and land here.
2. **The Carat lead list.** Every real, verified entry is a workshop you can ring about Carat.
   This replaces most of the "find ten jewellers" week in the Carat plan.

The progress bar at the top counts *verified* entries, so the page is also your research tracker.
Source 40, verify them one at a time, and the bar fills in.

## Files

```
directory/
  index.html            the page
  styles.css            all styling
  app.js                filtering, sorting, rendering
  data/jewellers.js     the data — this is the file you edit
  README.md             you are here
```

`data/jewellers.js` is a plain script that sets `window.JEWELLERS`. It is a script rather than a
JSON file on purpose: a `fetch()` of a local JSON file is blocked by browsers when you open the page
straight off disk, but a `<script src>` always works. So the site runs from `file://` with no server.

## Filling it in

Copy one block in `data/jewellers.js` and edit it:

```js
{
  id: "harbourside-bench",              // unique; lowercase, no spaces
  name: "Harbourside Bench",
  city: "Bristol",
  region: "South West",                 // must match an existing region to group cleanly
  website: "https://example.co.uk",
  email: "studio@example.co.uk",
  phone: "+44 117 000 0000",            // optional
  specialisms: ["Bespoke engagement rings", "Remodelling"],
  customWork: true,
  priceBand: "££",                      // £ / ££ / £££, optional
  notes: "One line on what they are good at, or what they lose sales on.",
  featured: false,                      // paid placement — see below
  verified: true,                       // you have checked this is real
  sample: false,                        // false for real entries
  lastChecked: "2026-10-16"             // the date you last confirmed the details
}
```

Rules I would hold to:

- **`sample: true` on anything you have not checked.** The page renders a loud SAMPLE badge and the
  banner stays up. Delete the flag only when you have confirmed the business is real and the contact
  details work.
- **`verified` is about accuracy, `sample` is about provenance.** A real business whose email you
  have not tested is `verified: true, sample: false`, with `lastChecked` set.
- **Never invent a business.** A directory of plausible-looking fake jewellers would mean you email
  strangers about a product they have never heard of, from a page that misrepresents them. The six
  entries shipped here are deliberately, visibly fake for exactly this reason.

The `region` and `specialism` dropdowns populate themselves from the data, so you never edit the HTML.

## Hosting

Any of these, free, in a few minutes:

- **GitHub Pages.** Put the `directory` folder in a repo, enable Pages, done.
- **Netlify / Cloudflare Pages.** Drag the folder onto the dashboard.
- **Any static host.** There is nothing to build; upload the four files.

Because it is static, it costs nothing to run and cannot fall over.

## Making money from it

The honest sequencing, given you have no audience yet:

1. **Nothing, at first.** Publish with real entries and no ads. The page's only job early on is to
   exist and rank for a few long-tail searches, and to be the thing you link when you email a
   workshop.
2. **Once it gets traffic, sell placement.** "Featured" puts a workshop at the top of its region.
   Local trade directories charge £10–£60/month for this sort of slot. Even three paying listings is
   a real, recurring £50–£150/month for a page you do not have to touch.
3. **Then it becomes a lead source for the actual product.** A jeweller who takes a listing is a
   jeweller already paying for visibility. That is a far warmer conversation about Carat than a
   cold email.

The `featured` flag in the data file is the entire mechanism for step 2. Nothing else is needed.

## What this deliberately is not

- Not a booking system, not a marketplace, not a CMS.
- No analytics, no cookies, no third-party scripts.
- No server, so no hosting bill and no outage to apologise for.

If it ever needs to grow past that, it will need a backend and a database, which is a different
project with a different budget. This one is sized to be finishable this week.
