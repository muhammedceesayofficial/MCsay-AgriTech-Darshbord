/*
  FRONTEND JAVASCRIPT
  ===================
  DATA FLOW:
    Page load  ->  GET  /api/harvests
    Submit     ->  POST /api/harvests  { field, crop, yield, date, location }
    Advice btn ->  POST /api/ai-advice  (no body; Python reads SQLite)
*/

const API_URL = "/api/harvests";
const ADVICE_URL = "/api/ai-advice";

const form = document.getElementById("harvest-form");
const tbody = document.getElementById("harvest-rows");
const emptyState = document.getElementById("empty-state");
const statusEl = document.getElementById("form-status");
const submitBtn = document.getElementById("submit-btn");
const adviceBtn = document.getElementById("advice-btn");
const adviceOutput = document.getElementById("advice-output");
const adviceStatus = document.getElementById("advice-status");

const dateInput = form.elements.harvest_date;
dateInput.value = new Date().toISOString().slice(0, 10);

function setStatus(message, kind) {
  statusEl.textContent = message;
  statusEl.className = "status " + (kind || "");
}

function errorMessage(errorBody, fallback) {
  const detail = errorBody && errorBody.detail;
  if (typeof detail === "string") {
    return detail;
  }
  return fallback;
}

function formatKg(value) {
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }) + " kg";
}

function formatDate(isoDate) {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

function updateStats(rows) {
  const count = rows.length;
  const total = rows.reduce((sum, row) => sum + Number(row.yield_kg), 0);
  const avg = count ? total / count : 0;

  document.getElementById("stat-count").textContent = String(count);
  document.getElementById("stat-total").textContent = formatKg(total);
  document.getElementById("stat-avg").textContent = formatKg(avg);
}

function renderTable(rows) {
  tbody.innerHTML = "";
  emptyState.classList.toggle("visible", rows.length === 0);
  updateStats(rows);

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(row.field_name)}</td>
      <td><span class="crop-pill">${escapeHtml(row.crop_type)}</span></td>
      <td><span class="location-pill">${escapeHtml(row.location || "—")}</span></td>
      <td>${formatKg(row.yield_kg)}</td>
      <td>${formatDate(row.harvest_date)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderAdvice(data) {
  const sections = (data.sections || [])
    .map(
      (section) => `
        <article class="advice-card">
          <header>
            <span class="advice-kicker">${escapeHtml(section.kicker)}</span>
          </header>
          <h3>${escapeHtml(section.location)}</h3>
          <p class="advice-fields">${escapeHtml(section.headline)}</p>
          <p class="advice-fields">Fields: ${escapeHtml(section.fields)}</p>
          <ul>
            ${(section.bullets || [])
              .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
              .join("")}
          </ul>
        </article>
      `
    )
    .join("");

  adviceOutput.innerHTML = `
    <p class="advice-summary">${escapeHtml(data.summary || "")}</p>
    <div class="advice-grid">${sections}</div>
  `;
}

async function loadHarvests() {
  const response = await fetch(API_URL);
  if (!response.ok) {
    throw new Error("Could not load harvests from the server.");
  }
  const rows = await response.json();
  renderTable(rows);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("");

  const payload = {
    field_name: form.elements.field_name.value.trim(),
    crop_type: form.elements.crop_type.value,
    yield_kg: Number(form.elements.yield_kg.value),
    harvest_date: form.elements.harvest_date.value,
    location: form.elements.location.value,
  };

  submitBtn.disabled = true;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorMessage(errorBody, "Save failed. Check the form values."));
    }

    form.reset();
    dateInput.value = new Date().toISOString().slice(0, 10);
    setStatus("Harvest saved to the database.", "ok");
    await loadHarvests();
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    submitBtn.disabled = false;
  }
});

adviceBtn.addEventListener("click", async () => {
  adviceStatus.textContent = "";
  adviceStatus.className = "status";
  adviceBtn.disabled = true;

  try {
    const response = await fetch(ADVICE_URL, { method: "POST" });
    if (!response.ok) {
      throw new Error("The agronomist endpoint did not respond.");
    }
    const data = await response.json();
    renderAdvice(data);
  } catch (error) {
    adviceStatus.textContent = error.message;
    adviceStatus.className = "status error";
  } finally {
    adviceBtn.disabled = false;
  }
});

loadHarvests().catch((error) => {
  setStatus(error.message, "error");
});
