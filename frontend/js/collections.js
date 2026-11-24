// Safe rupee formatter — handles null, undefined, NaN
function fmtRupees(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "0";
  return Number(n).toLocaleString("en-IN");
}

// Safe tonne formatter
function fmtTonnes(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return n + " t";
}

// ---------- FARMER DROPDOWN ----------
async function loadFarmerOptions() {
  const farmers = await apiGet("/farmers");
  const sel = document.getElementById("farmer-select");
  sel.innerHTML = farmers
    .map((f) => `<option value="${f.id}">${f.name} — ${f.village}</option>`)
    .join("");
}

// ---------- COLLECTION TABLE ----------
async function loadCollections() {
  const list = await apiGet("/collections");
  const tbody = document.getElementById("collection-rows");
  tbody.innerHTML = "";

  if (!Array.isArray(list) || list.length === 0) {
    tbody.innerHTML = `
      <tr><td colspan="9" style="text-align:center;color:#6b7280;padding:16px">
        No collections yet. Add one above.
      </td></tr>`;
    return;
  }

  list.forEach((c) => {
    const cls = c.status === "Received" ? "received" : "pending";
    const action =
      c.status === "Pending"
        ? `<button class="small" onclick="receive(${c.id})">Mark Received</button>`
        : "-";

    tbody.innerHTML += `
      <tr>
        <td>${c.id}</td>
        <td>${c.farmer_name}</td>
        <td>${c.village}</td>
        <td>${fmtTonnes(c.waste_quantity_tonnes)}</td>
        <td>${c.actual_weight_tonnes != null ? fmtTonnes(c.actual_weight_tonnes) : "-"}</td>
        <td>₹${fmtRupees(c.estimated_cost_inr)}</td>
        <td>₹${fmtRupees(c.payment_inr)}</td>
        <td><span class="badge ${cls}">${c.status}</span></td>
        <td>${action}</td>
      </tr>`;
  });
}

// ---------- MARK RECEIVED ----------
async function receive(id) {
  const w = prompt("Enter actual weight received at factory (tonnes):");
  if (!w) return;
  const num = parseFloat(w);
  if (Number.isNaN(num) || num <= 0) {
    alert("Please enter a valid positive number.");
    return;
  }
  await apiPatch(`/collections/${id}/receive`, {
    actual_weight_tonnes: num,
  });
  loadCollections();
}

// ---------- FORM SUBMIT ----------
document.getElementById("collection-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  await apiPost("/collections", {
    farmer_id: parseInt(f.farmer_id.value),
    waste_quantity_tonnes: parseFloat(f.waste_quantity_tonnes.value),
    collection_date: f.collection_date.value,
  });
  f.reset();
  loadCollections();
});

// ---------- INIT ----------
loadFarmerOptions();
loadCollections();