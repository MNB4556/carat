// Directory front end. No framework, no build step: open index.html and it runs.
(function () {
  "use strict";

  var data = window.JEWELLERS || [];
  var meta = window.DIRECTORY_META || { target: 40 };

  var $ = function (id) { return document.getElementById(id); };
  var grid = $("grid");
  var empty = $("empty");
  var resultLine = $("resultLine");
  var q = $("q");
  var regionSel = $("region");
  var specSel = $("spec");
  var sortSel = $("sort");
  var customOnly = $("customOnly");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function unique(values) {
    var seen = {};
    var out = [];
    values.forEach(function (v) {
      if (v && !seen[v]) { seen[v] = 1; out.push(v); }
    });
    return out.sort(function (a, b) { return a.localeCompare(b); });
  }

  function fillSelect(sel, values, allLabel) {
    sel.innerHTML = '<option value="">' + esc(allLabel) + "</option>" +
      values.map(function (v) {
        return '<option value="' + esc(v) + '">' + esc(v) + "</option>";
      }).join("");
  }

  // ---- filters, built from whatever data exists ----
  fillSelect(regionSel, unique(data.map(function (d) { return d.region; })), "All regions");
  fillSelect(specSel, unique(data.flatMap(function (d) { return d.specialisms || []; })), "Any specialism");

  // ---- progress: this is a research tracker as much as a directory ----
  var target = meta.target || 40;
  var listed = data.length;
  var sourced = data.filter(function (d) { return !d.sample; }).length;
  $("sourcedCount").textContent = String(sourced);
  $("target").textContent = String(target);
  $("listedCount").textContent = String(listed);
  $("bar").style.width = Math.min(100, Math.round((sourced / target) * 100)) + "%";
  $("sampleBanner").hidden = !data.some(function (d) { return d.sample; });
  $("footNote").textContent =
    "Last updated " + (meta.lastUpdated || "—") + ". " +
    sourced + " verified, " + (listed - sourced) + " sample. " +
    "Sample entries are placeholders, not real businesses.";

  function matches(d) {
    var text = [d.name, d.city, d.region, (d.specialisms || []).join(" "), d.notes]
      .join(" ").toLowerCase();
    var needle = q.value.trim().toLowerCase();
    if (needle && text.indexOf(needle) === -1) return false;
    if (regionSel.value && d.region !== regionSel.value) return false;
    if (specSel.value && (d.specialisms || []).indexOf(specSel.value) === -1) return false;
    if (customOnly.checked && !d.customWork) return false;
    return true;
  }

  function sortRows(rows) {
    var copy = rows.slice();
    var mode = sortSel.value;
    if (mode === "name") {
      copy.sort(function (a, b) { return a.name.localeCompare(b.name); });
    } else if (mode === "city") {
      copy.sort(function (a, b) { return String(a.city || "").localeCompare(String(b.city || "")); });
    } else {
      copy.sort(function (a, b) {
        return (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || a.name.localeCompare(b.name);
      });
    }
    return copy;
  }

  function card(d) {
    var badges = [];
    if (d.featured) badges.push('<span class="badge featured">Featured</span>');
    if (d.sample) badges.push('<span class="badge sample">Sample</span>');
    if (d.customWork) badges.push('<span class="badge">Custom work</span>');
    if (d.verified) badges.push('<span class="badge ok">Verified</span>');

    var specs = (d.specialisms || []).map(function (s) {
      return "<li>" + esc(s) + "</li>";
    }).join("");

    var contact = [];
    if (d.website) contact.push('<a href="' + esc(d.website) + '" target="_blank" rel="noopener nofollow">Website</a>');
    if (d.email) contact.push('<a href="mailto:' + esc(d.email) + '">Email</a>');
    if (d.phone) contact.push("<span>" + esc(d.phone) + "</span>");

    var where = esc(d.city);
    if (d.region) where += " · " + esc(d.region);
    if (d.priceBand) where += " · " + esc(d.priceBand);

    return '<article class="card' + (d.featured ? " is-featured" : "") + '">' +
      "<header>" +
        "<h3>" + esc(d.name) + "</h3>" +
        '<p class="where">' + where + "</p>" +
        (badges.length ? '<p class="badges">' + badges.join("") + "</p>" : "") +
      "</header>" +
      (specs ? '<ul class="specs">' + specs + "</ul>" : "") +
      (d.notes ? '<p class="notes">' + esc(d.notes) + "</p>" : "") +
      '<footer class="card-foot">' +
        '<p class="contact">' + contact.join("") + "</p>" +
        (d.lastChecked ? '<p class="checked">Checked ' + esc(d.lastChecked) + "</p>" : "") +
      "</footer>" +
    "</article>";
  }

  function render() {
    var rows = sortRows(data.filter(matches));
    grid.innerHTML = rows.map(card).join("");
    empty.hidden = rows.length !== 0;
    resultLine.textContent = rows.length
      ? "Showing " + rows.length + (rows.length === 1 ? " jeweller." : " jewellers.")
      : "No jewellers match those filters.";
  }

  [q, regionSel, specSel, sortSel, customOnly].forEach(function (elm) {
    elm.addEventListener("input", render);
    elm.addEventListener("change", render);
  });

  render();
})();
