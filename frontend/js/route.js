async function loadRoute() {
  const data = await apiGet("/collections/route");
  const tbody = document.getElementById("route-rows");
  tbody.innerHTML = "";

  if (!data.route.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#6b7280">
      No pending collections — all villages cleared ✅</td></tr>`;
    return;
  }

  data.route.forEach((v) => {
    tbody.innerHTML += `
      <tr>
        <td><strong>${v.visit_order}</strong></td>
        <td>${v.village}</td>
        <td>${v.pending_count}</td>
        <td>${v.total_tonnes} t</td>
        <td>₹${v.total_cost.toLocaleString()}</td>
        <td>${v.priority_score.toLocaleString()}</td>
      </tr>`;
  });
}

loadRoute();