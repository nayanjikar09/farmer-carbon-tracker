// Load Received collections into the dropdown
async function loadCollectionOptions() {
  const collections = await apiGet("/collections");
  const sel = document.getElementById("collection-select");
  
  // Filter only Received collections with actual weight
  const received = collections.filter(c => c.status === "Received" && c.actual_weight_tonnes != null);
  
  if (received.length === 0) {
    sel.innerHTML = `<option value="">No Received collections available</option>`;
    return;
  }

  sel.innerHTML = received.map(c => 
    `<option value="${c.id}">
      #${c.id} — ${c.farmer_name} (${c.village}) — ${c.actual_weight_tonnes} t
    </option>`
  ).join("");
}

// Load table
async function loadBatches() {
  const list = await apiGet("/production");
  const tbody = document.getElementById("batch-rows");
  tbody.innerHTML = "";

  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#6b7280">No batches yet</td></tr>`;
    return;
  }

  list.forEach((b) => {
    tbody.innerHTML += `
      <tr>
        <td>${b.id}</td>
        <td>${b.batch_date}</td>
        <td>${b.collection_id ?? "-"}</td>
        <td>${b.biomass_input_tonnes} t</td>
        <td>${b.biochar_output_tonnes} t</td>
        <td>${b.carbon_stored_tonnes} t</td>
      </tr>`;
  });
}

// Form submit
document.getElementById("production-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  
  const colId = f.collection_id.value;
  if (!colId) {
    alert("Please select a collection first.");
    return;
  }

  await apiPost("/production", {
    collection_id: parseInt(colId),
    biomass_input_tonnes: parseFloat(f.biomass_input_tonnes.value),
    batch_date: f.batch_date.value,
  });
  
  f.reset();
  loadBatches();
  loadCollectionOptions(); // Refresh options in case a collection was used
});

// Init
loadCollectionOptions();
loadBatches();