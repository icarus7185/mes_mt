const REFRESH_INTERVAL_MS = 2000;

function formatNumber(value) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

function applyStatusBadge(el, success) {
  if (success === true) {
    el.className = "status-badge status-badge--success";
    el.textContent = "Thành công";
  } else if (success === false) {
    el.className = "status-badge status-badge--failure";
    el.textContent = "Thất bại";
  } else {
    el.className = "status-badge";
    el.textContent = "--";
  }
}

function renderStatusBadge(success) {
  const badge = document.createElement("span");
  applyStatusBadge(badge, success);
  return badge;
}

function renderRecords(records) {
  const body = document.getElementById("records-body");
  body.innerHTML = "";
  for (const record of records) {
    const row = document.createElement("tr");
    const cells = [
      { value: record.added_at ?? "--" },
      { badge: record.send_success },
      { value: formatNumber(record["Lagging_Current_Reactive.Power_kVarh"]) },
      { value: formatNumber(record.Leading_Current_Reactive_Power_kVarh) },
      { value: formatNumber(record["CO2(tCO2)"]) },
      { value: formatNumber(record.Lagging_Current_Power_Factor) },
      { value: formatNumber(record.Leading_Current_Power_Factor) },
      { value: record.NSM ?? "--" },
      { value: record.Load_Type ?? "--" },
    ];
    for (const cell of cells) {
      const td = document.createElement("td");
      if ("badge" in cell) {
        td.appendChild(renderStatusBadge(cell.badge));
      } else {
        td.textContent = cell.value;
      }
      row.appendChild(td);
    }
    body.appendChild(row);
  }
}

async function refresh() {
  const timestamp = Date.now();
  document.getElementById("sent-image").src = `/api/image/latest?t=${timestamp}`;

  try {
    const response = await fetch(`/api/image/meta?t=${timestamp}`);
    const meta = await response.json();
    document.getElementById("sent-at").textContent = meta.sent_at ?? "--:--:--";
    applyStatusBadge(document.getElementById("sent-status"), meta.success);
  } catch (err) {
    // Ignore transient fetch errors; the next tick will retry.
  }

  try {
    const response = await fetch(`/api/records?t=${timestamp}`);
    const data = await response.json();
    renderRecords(data.records);
  } catch (err) {
    // Ignore transient fetch errors; the next tick will retry.
  }
}

setInterval(refresh, REFRESH_INTERVAL_MS);
refresh();
