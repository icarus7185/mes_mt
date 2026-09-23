const REFRESH_INTERVAL_MS = 2000;

const CHART_WIDTH = 640;
const CHART_HEIGHT = 220;
const CHART_MARGIN = { top: 16, right: 16, bottom: 24, left: 44 };

const chartState = { points: [] };

function openLightbox(src, caption) {
  const lightbox = document.getElementById("lightbox");
  const image = document.getElementById("lightbox-image");
  const captionEl = document.getElementById("lightbox-caption");
  image.src = src;
  image.alt = caption;
  captionEl.textContent = caption;
  lightbox.hidden = false;
}

function closeLightbox() {
  const lightbox = document.getElementById("lightbox");
  if (lightbox.hidden) {
    return;
  }
  lightbox.hidden = true;
  document.getElementById("lightbox-image").src = "";
}

function renderAlbum(images) {
  const album = document.getElementById("album");
  album.innerHTML = "";
  for (const image of images) {
    const figure = document.createElement("figure");

    const img = document.createElement("img");
    img.src = `/api/hist/${encodeURIComponent(image.filename)}`;
    img.alt = image.filename;
    img.tabIndex = 0;
    img.setAttribute("role", "button");
    img.title = "Nhấn để phóng to";

    const caption = document.createElement("figcaption");
    caption.textContent = image.received_at;

    const openThisImage = () => openLightbox(img.src, `${image.filename} — ${image.received_at}`);
    img.addEventListener("click", openThisImage);
    img.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openThisImage();
      }
    });

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

function niceTicks(min, max, count) {
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const step = (max - min) / (count - 1);
  return Array.from({ length: count }, (_, i) => min + step * i);
}

function svgEl(tag, attrs) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, value);
  }
  return el;
}

function renderChart(records) {
  const svg = document.getElementById("usage-chart");
  const emptyEl = document.getElementById("chart-empty");
  const tooltip = document.getElementById("chart-tooltip");

  const chronological = records
    .filter((record) => typeof record.Usage_kWh === "number")
    .slice()
    .reverse();

  svg.innerHTML = "";
  chartState.points = [];

  if (chronological.length < 2) {
    emptyEl.hidden = false;
    tooltip.hidden = true;
    return;
  }
  emptyEl.hidden = true;

  const innerLeft = CHART_MARGIN.left;
  const innerRight = CHART_WIDTH - CHART_MARGIN.right;
  const innerTop = CHART_MARGIN.top;
  const innerBottom = CHART_HEIGHT - CHART_MARGIN.bottom;
  const innerWidth = innerRight - innerLeft;
  const innerHeight = innerBottom - innerTop;

  const values = chronological.map((record) => record.Usage_kWh);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const padding = (rawMax - rawMin) * 0.1 || 1;
  const yMin = rawMin - padding;
  const yMax = rawMax + padding;

  const xForIndex = (i) => innerLeft + (i / (chronological.length - 1)) * innerWidth;
  const yForValue = (v) => innerBottom - ((v - yMin) / (yMax - yMin)) * innerHeight;

  const points = chronological.map((record, i) => ({
    x: xForIndex(i),
    y: yForValue(record.Usage_kWh),
    date: record.date,
    value: record.Usage_kWh,
  }));
  chartState.points = points;

  for (const tick of niceTicks(yMin, yMax, 4)) {
    const y = yForValue(tick);
    svg.appendChild(svgEl("line", { class: "chart-gridline", x1: innerLeft, x2: innerRight, y1: y, y2: y }));
    const label = svgEl("text", { class: "chart-tick", x: innerLeft - 8, y: y + 3, "text-anchor": "end" });
    label.textContent = tick.toFixed(1);
    svg.appendChild(label);
  }

  svg.appendChild(
    svgEl("line", { class: "chart-baseline", x1: innerLeft, x2: innerRight, y1: innerBottom, y2: innerBottom })
  );

  const lastIndex = points.length - 1;
  const midIndex = Math.floor(lastIndex / 2);
  for (const i of new Set([0, midIndex, lastIndex])) {
    const anchor = i === 0 ? "start" : i === lastIndex ? "end" : "middle";
    const label = svgEl("text", { class: "chart-tick", x: points[i].x, y: innerBottom + 16, "text-anchor": anchor });
    label.textContent = points[i].date;
    svg.appendChild(label);
  }

  const areaPath = [
    `M ${points[0].x} ${innerBottom}`,
    ...points.map((p) => `L ${p.x} ${p.y}`),
    `L ${points[lastIndex].x} ${innerBottom}`,
    "Z",
  ].join(" ");
  svg.appendChild(svgEl("path", { class: "chart-area", d: areaPath }));

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  svg.appendChild(svgEl("path", { class: "chart-line", d: linePath }));

  const last = points[lastIndex];
  svg.appendChild(svgEl("circle", { class: "chart-end-dot", cx: last.x, cy: last.y, r: 4 }));
  const endLabel = svgEl("text", {
    class: "chart-end-label",
    x: Math.min(last.x, innerRight - 4),
    y: last.y - 10,
    "text-anchor": "end",
  });
  endLabel.textContent = formatNumber(last.value);
  svg.appendChild(endLabel);

  const crosshair = svgEl("line", { class: "chart-crosshair", x1: last.x, x2: last.x, y1: innerTop, y2: innerBottom });
  crosshair.style.display = "none";
  const hoverDot = svgEl("circle", { class: "chart-hover-dot", cx: last.x, cy: last.y, r: 4 });
  hoverDot.style.display = "none";
  svg.appendChild(crosshair);
  svg.appendChild(hoverDot);

  const hitLayer = svgEl("rect", {
    class: "chart-hit-layer",
    x: innerLeft,
    y: innerTop,
    width: innerWidth,
    height: innerHeight,
  });
  svg.appendChild(hitLayer);

  const showTooltip = (nearest, scaleX) => {
    crosshair.setAttribute("x1", nearest.x);
    crosshair.setAttribute("x2", nearest.x);
    crosshair.style.display = "";
    hoverDot.setAttribute("cx", nearest.x);
    hoverDot.setAttribute("cy", nearest.y);
    hoverDot.style.display = "";

    tooltip.style.left = `${nearest.x * scaleX}px`;
    tooltip.style.top = `${nearest.y}px`;
    tooltip.innerHTML = "";
    const dateEl = document.createElement("div");
    dateEl.textContent = nearest.date;
    const valueEl = document.createElement("div");
    valueEl.className = "tooltip-value";
    valueEl.textContent = `${formatNumber(nearest.value)} kWh`;
    tooltip.appendChild(dateEl);
    tooltip.appendChild(valueEl);
    tooltip.hidden = false;
  };

  const nearestPoint = (pointerX) => {
    let nearest = chartState.points[0];
    let nearestDist = Infinity;
    for (const p of chartState.points) {
      const dist = Math.abs(p.x - pointerX);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = p;
      }
    }
    return nearest;
  };

  hitLayer.addEventListener("pointermove", (event) => {
    const rect = svg.getBoundingClientRect();
    const scaleX = rect.width / CHART_WIDTH;
    const pointerX = (event.clientX - rect.left) / scaleX;
    showTooltip(nearestPoint(pointerX), scaleX);
  });

  hitLayer.addEventListener("pointerleave", () => {
    crosshair.style.display = "none";
    hoverDot.style.display = "none";
    tooltip.hidden = true;
  });
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
    renderChart(data.records);
  } catch (err) {
    // Ignore transient fetch errors; the next tick will retry.
  }
}

document.getElementById("lightbox-close").addEventListener("click", closeLightbox);
document.getElementById("lightbox").addEventListener("click", (event) => {
  if (event.target.id === "lightbox") {
    closeLightbox();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeLightbox();
  }
});

setInterval(refresh, REFRESH_INTERVAL_MS);
refresh();
