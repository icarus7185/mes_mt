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
}

setInterval(refresh, REFRESH_INTERVAL_MS);
refresh();
