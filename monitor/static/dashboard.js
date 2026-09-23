const REFRESH_INTERVAL_MS = 2000;

function renderAlbum(images) {
  const album = document.getElementById("album");
  album.innerHTML = "";
  for (const image of images) {
    const figure = document.createElement("figure");

    const img = document.createElement("img");
    img.src = `/api/hist/${encodeURIComponent(image.filename)}`;
    img.alt = image.filename;

    const caption = document.createElement("figcaption");
    caption.textContent = image.received_at;

    figure.appendChild(img);
    figure.appendChild(caption);
    album.appendChild(figure);
  }
}

function formatNumber(value) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

function renderRecords(records) {
  const body = document.getElementById("records-body");
  body.innerHTML = "";
  for (const record of records) {
    const row = document.createElement("tr");
    const cells = [
      { value: record.date ?? "--" },
      { value: formatNumber(record["Lagging_Current_Reactive.Power_kVarh"]) },
      { value: formatNumber(record.Leading_Current_Reactive_Power_kVarh) },
      { value: formatNumber(record["CO2(tCO2)"]) },
      { value: formatNumber(record.Lagging_Current_Power_Factor) },
      { value: formatNumber(record.Leading_Current_Power_Factor) },
      { value: record.NSM ?? "--" },
      { value: record.Load_Type ?? "--" },
      { value: formatNumber(record.Usage_kWh), highlight: true },
    ];
    for (const { value, highlight } of cells) {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (highlight) {
        cell.classList.add("usage-kwh-cell");
      }
      row.appendChild(cell);
    }
    body.appendChild(row);
  }
}

async function refresh() {
  const timestamp = Date.now();
  document.getElementById("processed-image").src = `/api/image/latest?t=${timestamp}`;

  try {
    const response = await fetch(`/api/image/meta?t=${timestamp}`);
    const meta = await response.json();
    document.getElementById("received-at").textContent = meta.received_at ?? "--:--:--";
  } catch (err) {
    // Ignore transient fetch errors; the next tick will retry.
  }

  try {
    const response = await fetch(`/api/hist?t=${timestamp}`);
    const hist = await response.json();
    renderAlbum(hist.images);
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
