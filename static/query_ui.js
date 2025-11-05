const endpointSpec = {
  "GET /movie/:title": { path: [{ key: "title", label: "Title" }] },
  "GET /movies": { path: [] },
  "GET /movie/:title/reviews": { path: [{ key: "title", label: "Title" }] },
  "GET /movies/director/:fullname": { path: [{ key: "fullname", label: "Director full name" }] },
  "GET /movies/actor/:fullname": { path: [{ key: "fullname", label: "Actor full name" }] },
  "GET /movies/genre/:genre": { path: [{ key: "genre", label: "Genre" }] },
  "GET /user/:username": { path: [{ key: "username", label: "Username" }] },
  "GET /user/:username/watchlist": { path: [{ key: "username", label: "Username" }] },
  "GET /user/:username/reviews": { path: [{ key: "username", label: "Username" }] },
  "GET /user/:username/friends": { path: [{ key: "username", label: "Username" }] },
  "GET /user/:username/friends/network/:degree": {
    path: [
      { key: "username", label: "Username" },
      { key: "degree", label: "Degree (1–5)" }
    ]
  },
  "GET /user/:username/movies/hottest": { path: [{ key: "username", label: "Username" }] },
  "GET /user/:username/movies/recommendations": { path: [{ key: "username", label: "Username" }] },
  "GET /reviews/:keyword": { path: [{ key: "keyword", label: "Keyword" }] },

  "POST /movie/new": {
    path: [],
    body: [
      { key: "movieId", label: "movieId (e.g., tt2395427)" },
      { key: "title", label: "title" },
      { key: "releaseYear", label: "releaseYear (int)" }
    ]
  },
  "POST /movie/genres/new": {
    path: [],
    body: [
      { key: "title", label: "title" },
      { key: "genres", label: "genres (comma-separated)", list: true }
    ]
  },
  "POST /friends/new": {
    path: [],
    body: [
      { key: "username1", label: "username1" },
      { key: "username2", label: "username2" }
    ]
  }
};

const endpointSel = document.getElementById("endpoint");
const paramForm = document.getElementById("paramForm");
const bodyForm = document.getElementById("bodyForm");
const tableWrap = document.getElementById("tableWrap");
const baseUrlEl = document.getElementById("baseUrl");
const reqPreview = document.getElementById("reqPreview");

function buildPath(template, params) {
  return template.replace(/:([a-zA-Z_]+)/g, (_, k) => encodeURIComponent(params[k] || ""));
}

function readFields(container, spec) {
  const obj = {};
  (spec || []).forEach(f => {
    const v = (container.querySelector(`#f_${f.key}`)?.value || "").trim();
    obj[f.key] = f.list ? (v ? v.split(",").map(s => s.trim()).filter(Boolean) : []) : v;
  });
  return obj;
}

function renderForms() {
  const ep = endpointSel.value;
  const spec = endpointSpec[ep] || {};
  paramForm.innerHTML = "";
  (spec.path || []).forEach(f => {
    const div = document.createElement("div");
    div.innerHTML = `<label>${f.label}</label><input id="f_${f.key}" type="text">`;
    paramForm.appendChild(div);
  });

  if (ep.startsWith("POST ")) {
    bodyForm.style.display = "block";
    bodyForm.innerHTML = "<strong>POST Body</strong>";
    (spec.body || []).forEach(f => {
      const div = document.createElement("div");
      div.innerHTML = `<label>${f.label}</label><input id="f_${f.key}" type="text">`;
      bodyForm.appendChild(div);
    });
  } else {
    bodyForm.style.display = "none";
    bodyForm.innerHTML = "";
  }
}

endpointSel.addEventListener("change", renderForms);
renderForms();

document.getElementById("runBtn").addEventListener("click", async () => {
  tableWrap.innerHTML = "";
  tableWrap.style.display = "none";
  const ep = endpointSel.value;
  const [method, pathTpl] = ep.split(" ");
  const spec = endpointSpec[ep] || {};
  const pathParams = readFields(paramForm, spec.path);
  const url = baseUrlEl.value.replace(/\/$/, "") + buildPath(pathTpl, pathParams);
  let fetchOpts = { method, headers: {} };

  if (method === "POST") {
    const bodyObj = readFields(bodyForm, spec.body);
    fetchOpts.headers["Content-Type"] = "application/json";
    fetchOpts.body = JSON.stringify(bodyObj);
  }

  reqPreview.textContent = `${method} ${url}` + (fetchOpts.body ? ` BODY: ${fetchOpts.body}` : "");

  try {
    const res = await fetch(url, fetchOpts);
    const data = await res.json();
    renderTable(data);
  } catch (e) {
    reqPreview.textContent = "Error: " + (e?.message || e);
  }
});

// --- helpers ---
const KNOWN_PREFIXES = [
  "movie.", "review.", "person.", "user.",
  "top_movie.", "recommendation."
];

function stripKnownPrefix(key) {
  for (const p of KNOWN_PREFIXES) {
    if (key.startsWith(p)) return key.slice(p.length);
  }
  return key;
}

function humanizeKey(key) {
  return key
    .replace(/\./g, " ")                  // dots -> spaces
    .replace(/([a-z])([A-Z])/g, "$1 $2")  // camelCase -> spaced
    .replace(/_/g, " ")
    .replace(/\buserName\b/i, "Username")
    .replace(/\bmovieId\b/i, "Movie ID")
    .replace(/\breleaseYear\b/i, "Release Year")
    .replace(/\breviewId\b/i, "Review ID")
    .replace(/\breview_date\b/i, "Review Date")
    .replace(/\bid\b/i, "ID")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase()); // capitalize each word
}

function buildHeaderLabels(keys) {
  const stripped = keys.map(stripKnownPrefix);
  const seen = new Map();
  const labels = new Array(keys.length);

  stripped.forEach((s, i) => {
    if (seen.has(s)) {
      const prev = seen.get(s);
      labels[prev] = humanizeKey(keys[prev]); // keep original for dupes
      labels[i] = humanizeKey(keys[i]);
    } else {
      seen.set(s, i);
      labels[i] = humanizeKey(s);
    }
  });
  return labels;
}

function flattenObject(obj, prefix = "") {
  const flat = {};
  for (const key in obj) {
    const val = obj[key];
    const full = prefix ? `${prefix}.${key}` : key;

    if (val === null || val === undefined) {
      flat[full] = "";
    } else if (Array.isArray(val)) {
      // Arrays:
      // - primitives -> join
      // - objects -> join using a readable label when possible
      const items = val.map(v => (typeof v === "object" ? pickLabel(v) : String(v)));
      flat[full] = items.join(", ");
    } else if (typeof val === "object") {
      Object.assign(flat, flattenObject(val, full));
    } else {
      flat[full] = val;
    }
  }
  return flat;
}

// Normalize API shapes into an array of row objects
function normalizeToRows(data) {
  // 1) Already an array of objects
  if (Array.isArray(data)) {
    // Sometimes Neo4j returns: [ { movies: [ {...}, {...} ] } ]
    if (
      data.length === 1 &&
      typeof data[0] === "object" &&
      data[0] !== null
    ) {
      const keys = Object.keys(data[0]);
      if (
        keys.length === 1 &&
        Array.isArray(data[0][keys[0]]) &&
        data[0][keys[0]].length &&
        typeof data[0][keys[0]][0] === "object"
      ) {
        return data[0][keys[0]]; // unwrap inner array
      }
    }
    return data;
  }

  // 2) Object with a single key that is an array of objects
  if (data && typeof data === "object") {
    const keys = Object.keys(data);
    if (
      keys.length === 1 &&
      Array.isArray(data[keys[0]]) &&
      data[keys[0]].length &&
      typeof data[keys[0]][0] === "object"
    ) {
      return data[keys[0]]; // unwrap { movies: [...] }, { reviews: [...] }, etc.
    }

    // 3) Object with `results: [...]`
    if (Array.isArray(data.results)) {
      return data.results;
    }

    // 4) Single object -> make it one row
    return [data];
  }

  // Fallback: nothing to render
  return [];
}

function renderTable(data) {
  const rows = normalizeToRows(data);

  if (!rows.length || typeof rows[0] !== "object") {
    tableWrap.innerHTML = "<div>No data found.</div>";
    tableWrap.style.display = "block";
    return;
  }

  // Flatten rows for stable columns
  const flatRows = rows.map(r => flattenObject(r));
  const columns = Array.from(
    flatRows.reduce((set, r) => {
      Object.keys(r).forEach(k => set.add(k));
      return set;
    }, new Set())
  );

// Build table
const table = document.createElement("table");
const thead = document.createElement("thead");
const trh = document.createElement("tr");

const headerLabels = buildHeaderLabels(columns);
headerLabels.forEach(label => {
  const th = document.createElement("th");
  th.textContent = label;
  trh.appendChild(th);
});

thead.appendChild(trh);
table.appendChild(thead);

  const tbody = document.createElement("tbody");
  flatRows.forEach(r => {
    const tr = document.createElement("tr");
    columns.forEach(col => {
      const td = document.createElement("td");
      td.textContent = r[col] ?? "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  tableWrap.innerHTML = "";
  tableWrap.appendChild(table);
  tableWrap.style.display = "block";
}

