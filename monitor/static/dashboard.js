const REFRESH_INTERVAL_MS = 2000;

const CHART_WIDTH = 640;
const CHART_HEIGHT = 220;
const CHART_MARGIN = { top: 16, right: 16, bottom: 24, left: 44 };

const chartState = { points: [] };
let lastTopRecordKey = null;
let lastNewRecordAt = null;
let latestImageInfo = { filename: null, receivedAt: null };

const LOAD_BADGE_CLASS = {
  Light_Load: "load-badge--light",
  Medium_Load: "load-badge--medium",
  Maximum_Load: "load-badge--maximum",
};

function setupImagePlaceholder() {
  const img = document.getElementById("processed-image");
  const placeholder = document.getElementById("image-placeholder");
  img.addEventListener("error", () => {
    img.hidden = true;
    placeholder.hidden = false;
  });
  img.addEventListener("load", () => {
    img.hidden = false;
    placeholder.hidden = true;
  });
}

function setupImageZoom() {
  const img = document.getElementById("processed-image");

  const openProcessedImage = () => {
    if (img.hidden) {
      return;
    }
    const caption = latestImageInfo.filename
      ? `${latestImageInfo.filename} — ${latestImageInfo.receivedAt ?? "--:--:--"}`
      : "Processed image";
    openLightbox(img.src, caption);
  };

  img.addEventListener("click", openProcessedImage);
  img.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openProcessedImage();
    }
  });
}

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
    img.title = "Click to enlarge";

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
  records.forEach((record, index) => {
    const row = document.createElement("tr");
    const cells = [
      { value: record.date ?? "--" },
      { value: formatNumber(record["Lagging_Current_Reactive.Power_kVarh"]) },
      { value: formatNumber(record.Leading_Current_Reactive_Power_kVarh) },
      { value: formatNumber(record["CO2(tCO2)"]) },
      { value: formatNumber(record.Lagging_Current_Power_Factor) },
      { value: formatNumber(record.Leading_Current_Power_Factor) },
      { value: record.NSM ?? "--" },
      { value: record.Load_Type ?? "--", badge: true },
      { value: formatNumber(record.Usage_kWh), highlight: true },
    ];
    for (const { value, highlight, badge } of cells) {
      const cell = document.createElement("td");
      if (badge) {
        const pill = document.createElement("span");
        pill.className = `load-badge ${LOAD_BADGE_CLASS[value] ?? ""}`;
        pill.textContent = value;
        cell.appendChild(pill);
      } else {
        cell.textContent = value;
      }
      if (highlight) {
        cell.classList.add("usage-kwh-cell");
      }
      row.appendChild(cell);
    }

    if (index === 0) {
      const topKey = `${record.date ?? ""}|${record.NSM ?? ""}`;
      if (topKey !== lastTopRecordKey) {
        if (lastTopRecordKey !== null) {
          row.classList.add("row-flash");
        }
        lastTopRecordKey = topKey;
        lastNewRecordAt = Date.now();
      }
    }

    body.appendChild(row);
  });
}

function setStatTone(el, tone) {
  el.classList.remove("stat-value--good", "stat-value--warning", "stat-value--critical", "stat-value--accent");
  if (tone) {
    el.classList.add(`stat-value--${tone}`);
  }
}

function updateAverageStat(records) {
  const el = document.getElementById("stat-average");
  const values = records.slice(0, 20).map((r) => r.Usage_kWh).filter((v) => typeof v === "number");
  if (values.length === 0) {
    el.textContent = "--";
    return;
  }
  const average = values.reduce((sum, v) => sum + v, 0) / values.length;
  el.textContent = `${formatNumber(average)} kWh`;
}

function updateTrendStat(records) {
  const el = document.getElementById("stat-trend");
  const latest = records[0];
  const previous = records[1];
  if (!latest || !previous || typeof latest.Usage_kWh !== "number" || typeof previous.Usage_kWh !== "number") {
    setStatTone(el, null);
    el.textContent = "--";
    return;
  }
  const delta = latest.Usage_kWh - previous.Usage_kWh;
  const arrow = delta >= 0 ? "▲" : "▼";
  const sign = delta >= 0 ? "+" : "";
  el.textContent = `${arrow} ${sign}${formatNumber(delta)} kWh`;
  setStatTone(el, "accent");
}

function updateHeavyLoadStat(records) {
  const el = document.getElementById("stat-heavyload");
  const withLoadType = records.filter((r) => typeof r.Load_Type === "string");
  if (withLoadType.length === 0) {
    setStatTone(el, null);
    el.textContent = "--";
    return;
  }
  const maxCount = withLoadType.filter((r) => r.Load_Type === "Maximum_Load").length;
  const pct = Math.round((maxCount / withLoadType.length) * 100);
  el.textContent = `${pct}%`;
  if (pct < 20) {
    setStatTone(el, "good");
  } else if (pct < 50) {
    setStatTone(el, "warning");
  } else {
    setStatTone(el, "critical");
  }
}

function formatElapsed(elapsedMs) {
  const totalSeconds = Math.max(0, Math.floor(elapsedMs / 1000));
  if (totalSeconds < 60) {
    return `${totalSeconds}s ago`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s ago`;
}

function updateFreshnessStat() {
  const el = document.getElementById("stat-freshness");
  if (lastNewRecordAt === null) {
    setStatTone(el, null);
    el.textContent = "--";
    return;
  }
  const elapsedMs = Date.now() - lastNewRecordAt;
  el.textContent = formatElapsed(elapsedMs);
  if (elapsedMs <= 60000) {
    setStatTone(el, "good");
  } else if (elapsedMs <= 180000) {
    setStatTone(el, "warning");
  } else {
    setStatTone(el, "critical");
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
    latestImageInfo = { filename: meta.filename ?? null, receivedAt: meta.received_at ?? null };
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
    updateAverageStat(data.records);
    updateTrendStat(data.records);
    updateHeavyLoadStat(data.records);
  } catch (err) {
    // Ignore transient fetch errors; the next tick will retry.
  }
}

setupImagePlaceholder();
setupImageZoom();

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
setInterval(updateFreshnessStat, 1000);
refresh();
