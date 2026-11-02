# The Directory

Independent jewellers who take on custom work. A static site: no build step, no
dependencies, no server.

Open `index.html` in a browser. That is the whole deployment.

## What it is for

1. A public directory, for people searching for a bespoke jeweller in their area.
2. A lead list. Every verified entry is a workshop I can approach about Carat.

The progress bar at the top counts verified entries, so the page doubles as the
research tracker. Add forty entries, verify them one at a time, and the bar
fills in.

## Files

```
directory/
  index.html            the page
  styles.css            all styling
  app.js                filtering, sorting, rendering
  data/jewellers.js     the data; this is the file you edit
  README.md             you are here
```

`data/jewellers.js` is a plain script that sets `window.JEWELLERS` rather than a
JSON file. A local `fetch()` is blocked when the page is opened from disk, while
a `<script src>` always works, so the site runs from `file://` with no server.

## Adding an entry

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
  featured: false,                      // paid placement, see below
  verified: true,                       // the business is real and the details were checked
  sample: false,                        // false for real entries
  lastChecked: "2026-10-16"
}
```

Three rules:

- Set `sample: true` on anything not yet checked. The page shows a SAMPLE badge
  and keeps the banner up until it is removed.
- `verified` and `sample` are different things. `verified` means the details have
  been checked; `sample` means the entry is a placeholder. A real entry can still
  be incomplete, so leave `verified: false` until the details are confirmed.
- Never invent a business. A directory of plausible fakes means emailing strangers
  about a product they have never heard of, from a page that misrepresents them.
  The six entries shipped here are fake on purpose.

The region and specialism dropdowns populate themselves from the data, so the
HTML is never edited by hand.

## Hosting

Any of these, free, in a few minutes:

- GitHub Pages: put the folder in a repo, enable Pages.
- Netlify or Cloudflare Pages: drag the folder onto the dashboard.
- Any static host: upload the four files.

There is nothing to build, so it costs nothing to run.

## Making money from it

There is no audience yet, so the order matters.

1. Publish with real entries and no ads. Early on the page only has to exist, rank
   for a few long-tail searches, and be the link in an email to a workshop.
2. Once there is traffic, sell placement. Featured puts a workshop at the top of
   its region. Local trade directories charge £10 to £60 a month for that slot,
   so three paying listings is a recurring £50 to £150 for a page that never
   changes.
3. Use it as a lead source for the product. A jeweller who buys a listing is
   already paying for visibility, which is a warmer conversation about Carat than
   a cold email.

The `featured` flag is the whole mechanism for step 2.

## Limits

- Not a booking system, a marketplace or a CMS.
- No analytics, cookies or third-party scripts.
- No server, so no hosting bill and no outage to apologise for.

Anything bigger needs a backend and a database, which is a different project with
a different budget. This one is sized to be finished this week.
