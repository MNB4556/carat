// The directory data. One file, no build step, no server needed.
//
// Two jobs in one place:
//   1. It is the public-facing directory.
//   2. It is the lead list for the Carat pilot. Every real entry here is a
//      jeweller you can ring.
//
// The six below are SAMPLES. They are not real businesses. Replace them.
// Delete the `sample: true` flag only when the entry is a real, verified
// business you have actually checked.

window.DIRECTORY_META = {
  target: 40,              // how many you intend to source
  lastUpdated: "2026-10-16",
};

window.JEWELLERS = [
  {
    id: "sample-bristol",
    name: "Sample — Harbourside Bench",
    city: "Bristol",
    region: "South West",
    website: "https://example.com",
    email: "hello@example.com",
    specialisms: ["Bespoke engagement rings", "Remodelling"],
    customWork: true,
    priceBand: "££",
    notes: "Replace with a real jeweller. Note here what they lose sales on.",
    featured: false,
    verified: false,
    sample: true,
    lastChecked: null,
  },
  {
    id: "sample-manchester",
    name: "Sample — North Quarter Gold",
    city: "Manchester",
    region: "North West",
    website: "https://example.com",
    email: "hello@example.com",
    specialisms: ["Bespoke", "Repairs", "Ethical / recycled gold"],
    customWork: true,
    priceBand: "££",
    notes: "Replace with a real jeweller.",
    featured: false,
    verified: false,
    sample: true,
    lastChecked: null,
  },
  {
    id: "sample-edinburgh",
    name: "Sample — Ash & Facet",
    city: "Edinburgh",
    region: "Scotland",
    website: "https://example.com",
    email: "hello@example.com",
    specialisms: ["Bespoke", "CAD / 3D design"],
    customWork: true,
    priceBand: "£££",
    notes: "Good fit for a Carat pilot: already shows clients 3D previews.",
    featured: false,
    verified: false,
    sample: true,
    lastChecked: null,
  },
  {
    id: "sample-norwich",
    name: "Sample — The Quiet Forge",
    city: "Norwich",
    region: "East of England",
    website: "https://example.com",
    email: "hello@example.com",
    specialisms: ["Remodelling", "Heirloom work", "Repairs"],
    customWork: true,
    priceBand: "£",
    notes: "Replace with a real jeweller.",
    featured: false,
    verified: false,
    sample: true,
    lastChecked: null,
  },
  {
    id: "sample-london",
    name: "Sample — Greenwich Stoneworks",
    city: "London",
    region: "London",
    website: "https://example.com",
    email: "hello@example.com",
    specialisms: ["Bespoke", "Coloured gemstones"],
    customWork: true,
    priceBand: "£££",
    notes: "Coloured stones mean dispersion matters more than usual.",
    featured: true,
    verified: false,
    sample: true,
    lastChecked: null,
  },
  {
    id: "sample-leeds",
    name: "Sample — Cobble Lane Jewellery",
    city: "Leeds",
    region: "Yorkshire",
    website: "https://example.com",
    email: "hello@example.com",
    specialisms: ["Bespoke", "Wedding bands"],
    customWork: true,
    priceBand: "££",
    notes: "Replace with a real jeweller.",
    featured: false,
    verified: false,
    sample: true,
    lastChecked: null,
  },
];
