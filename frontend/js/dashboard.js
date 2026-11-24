async function loadDashboard() {
  const d = await apiGet("/dashboard");

  document.getElementById("s-farmers").textContent = d.farmers_registered;
  document.getElementById("s-biomass").textContent = d.biomass_collected_t + " t";
  document.getElementById("s-biochar").textContent = d.biochar_produced_t + " t";
  document.getElementById("s-carbon").textContent = d.estimated_gross_carbon_t + " t";

  const tbody = document.getElementById("collection-rows");
  tbody.innerHTML = "";
  d.collection_records.forEach((r) => {
    const cls = r.status === "Received" ? "received" : "pending";
    tbody.innerHTML += `
      <tr>
        <td>${r.village}</td>
        <td>${r.biomass_t} t</td>
        <td><span class="badge ${cls}">${r.status}</span></td>
      </tr>`;
  });
  if (!d.collection_records.length) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:#6b7280">No records yet</td></tr>`;
  }

  document.getElementById("p-biomass").textContent = d.production.biomass_processed_t + " tonnes";
  document.getElementById("p-biochar").textContent = d.production.biochar_produced_t + " tonnes";
  document.getElementById("carbon-status").textContent = d.carbon_monitoring;
}
loadDashboard();