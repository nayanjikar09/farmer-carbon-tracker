async function loadFarmers() {
  const list = await apiGet("/farmers");
  const tbody = document.getElementById("farmer-rows");
  tbody.innerHTML = "";
  list.forEach((f) => {
    tbody.innerHTML += `
      <tr>
        <td>${f.id}</td>
        <td>${f.name}</td>
        <td>${f.village}</td>
        <td>${f.acres}</td>
        <td>${f.crop}</td>
        <td>${f.gps_lat ?? "-"}, ${f.gps_lng ?? "-"}</td>
      </tr>`;
  });
  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#6b7280">No farmers yet</td></tr>`;
  }
}

document.getElementById("farmer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  await apiPost("/farmers", {
    name: f.name.value,
    village: f.village.value,
    acres: parseFloat(f.acres.value),
    crop: f.crop.value,
    gps_lat: f.gps_lat.value ? parseFloat(f.gps_lat.value) : null,
    gps_lng: f.gps_lng.value ? parseFloat(f.gps_lng.value) : null,
  });
  f.reset();
  loadFarmers();
});

loadFarmers();