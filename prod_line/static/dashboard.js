const REFRESH_INTERVAL_MS = 2000;

function formatNumber(value) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

function renderRecords(records) {
  const body = document.getElementById("records-body");
  body.innerHTML = "";
  for (const record of records) {
    const row = document.createElement("tr");
    const cells = [
      formatNumber(record["Lagging_Current_Reactive.Power_kVarh"]),
      formatNumber(record.Leading_Current_Reactive_Power_kVarh),
      formatNumber(record["CO2(tCO2)"]),
      formatNumber(record.Lagging_Current_Power_Factor),
      formatNumber(record.Leading_Current_Power_Factor),
      record.NSM ?? "--",
      record.Load_Type ?? "--",
    ];
    for (const value of cells) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
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
