const REFRESH_INTERVAL_MS = 2000;

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
}

setInterval(refresh, REFRESH_INTERVAL_MS);
refresh();
