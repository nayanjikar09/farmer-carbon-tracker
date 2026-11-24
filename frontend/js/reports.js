// Safe number formatter — handles null / undefined / NaN
function fmtNum(n, decimals = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return "0";
  return Number(n).toFixed(decimals).replace(/\.?0+$/, "");
}

function fmtRupees(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "0";
  return Number(n).toLocaleString("en-IN");
}

// ---------- FARMER PAYMENT REPORT ----------
async function loadPaymentReport() {
  const list = await apiGet("/farmers/payments");
  const tbody = document.getElementById("payment-rows");
  tbody.innerHTML = "";

  if (!Array.isArray(list) || list.length === 0) {
    tbody.innerHTML = `
      <tr><td colspan="8" style="text-align:center;color:#6b7280;padding:16px">
        No farmers registered yet.
      </td></tr>`;
    return;
  }

  list.forEach((f) => {
    tbody.innerHTML += `
      <tr>
        <td>${f.id}</td>
        <td>${f.name}</td>
        <td>${f.village}</td>
        <td>${f.acres}</td>
        <td>${f.collections_count}</td>
        <td>${fmtNum(f.delivered_tonnes)} t</td>
        <td><strong>₹${fmtRupees(f.total_payment_inr)}</strong></td>
        <td>
          <a href="/collections.html?farmer_id=${f.id}" class="btn-link">View</a>
        </td>
      </tr>`;
  });
}

// ---------- PRODUCTION REPORT ----------
async function loadProductionReport() {
  const data = await apiGet("/production/report");

  const totals = data?.totals ?? { biomass: 0, biochar: 0, carbon: 0 };
  document.getElementById("r-biomass").textContent = fmtNum(totals.biomass) + " t";
  document.getElementById("r-biochar").textContent = fmtNum(totals.biochar) + " t";
  document.getElementById("r-carbon").textContent  = fmtNum(totals.carbon)  + " t";

  const tbody = document.getElementById("batch-rows");
  tbody.innerHTML = "";

  const batches = data?.batches ?? [];
  if (batches.length === 0) {
    tbody.innerHTML = `
      <tr><td colspan="7" style="text-align:center;color:#6b7280;padding:16px">
        No production batches recorded yet.
      </td></tr>`;
    return;
  }

  batches.forEach((b) => {
    tbody.innerHTML += `
      <tr>
        <td>${b.id}</td>
        <td>${b.batch_date ?? "-"}</td>
        <td>${b.farmer_name ?? "-"}</td>
        <td>${b.village ?? "-"}</td>
        <td>${fmtNum(b.biomass_input_tonnes)} t</td>
        <td>${fmtNum(b.biochar_output_tonnes)} t</td>
        <td>${fmtNum(b.carbon_stored_tonnes)} t</td>
      </tr>`;
  });
}

// ---------- CSV EXPORT HELPERS (Gap 3) ----------
function downloadCSV(csvContent, filename) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function toCSVRow(arr) {
  return arr.map(v => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    return s.includes(",") || s.includes('"') || s.includes("\n")
      ? `"${s.replace(/"/g, '""')}"`
      : s;
  }).join(",");
}

async function downloadPaymentsCSV() {
  const list = await apiGet("/farmers/payments");
  if (!Array.isArray(list) || !list.length) {
    alert("No data to export.");
    return;
  }

  const headers = ["ID", "Name", "Village", "Acres", "Collections", "Delivered (t)", "Total Payment (INR)"];
  const rows = list.map(f => [
    f.id, f.name, f.village, f.acres, f.collections_count,
    fmtNum(f.delivered_tonnes), fmtRupees(f.total_payment_inr)
  ]);

  const csv = [toCSVRow(headers), ...rows.map(toCSVRow)].join("\n");
  downloadCSV(csv, `farmer_payments_${new Date().toISOString().slice(0,10)}.csv`);
}

async function downloadProductionCSV() {
  const data = await apiGet("/production/report");
  if (!data?.batches?.length) {
    alert("No data to export.");
    return;
  }

  const headers = ["Batch ID", "Date", "Farmer", "Village", "Biomass (t)", "Biochar (t)", "Carbon (t)"];
  const rows = data.batches.map(b => [
    b.id, b.batch_date, b.farmer_name ?? "-", b.village ?? "-",
    fmtNum(b.biomass_input_tonnes),
    fmtNum(b.biochar_output_tonnes),
    fmtNum(b.carbon_stored_tonnes)
  ]);

  const csv = [toCSVRow(headers), ...rows.map(toCSVRow)].join("\n");
  downloadCSV(csv, `production_report_${new Date().toISOString().slice(0,10)}.csv`);
}

// ---------- INIT ----------
loadPaymentReport();
loadProductionReport();