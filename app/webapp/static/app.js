const tabButtons = document.querySelectorAll(".tab-button");
const panels = document.querySelectorAll(".tab-panel");

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    panels.forEach((p) => p.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.tab).classList.add("active");
  });
});

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function loadCaptures() {
  const container = document.getElementById("captures-list");
  try {
    const response = await fetch("/api/captures");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    const items = await response.json();
    if (items.length === 0) {
      container.innerHTML = "<p>No captures yet.</p>";
      return;
    }
    container.innerHTML = items
      .map((item) => {
        const media =
          item.type === "video"
            ? `<video controls src="/captures/${encodeURIComponent(item.name)}"></video>`
            : `<img loading="lazy" src="/captures/${encodeURIComponent(item.name)}" alt="${item.name}" />`;
        const date = new Date(item.modified * 1000).toLocaleString();
        return `<div class="capture-card">${media}<div class="capture-meta">${item.name}<br>${date} - ${formatBytes(item.size)}</div></div>`;
      })
      .join("");
  } catch (err) {
    container.innerHTML = "<p>Failed to load captures.</p>";
  }
}

async function loadLogs() {
  const pre = document.getElementById("logs-content");
  try {
    const response = await fetch("/api/logs");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    const data = await response.json();
    const atBottom =
      pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 20;
    pre.textContent = data.content;
    if (atBottom) {
      pre.scrollTop = pre.scrollHeight;
    }
  } catch (err) {
    pre.textContent = "Failed to load logs.";
  }
}

loadCaptures();
loadLogs();
setInterval(loadCaptures, 5000);
setInterval(loadLogs, 3000);
