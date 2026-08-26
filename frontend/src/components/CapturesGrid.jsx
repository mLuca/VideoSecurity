import { useEffect, useState } from "react";
import { fetchCaptures } from "../api.js";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CapturesGrid() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchCaptures();
        if (!cancelled) {
          setItems(data);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Failed to load captures.");
      }
    }

    load();
    const id = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (error) return <p>{error}</p>;
  if (items.length === 0) return <p>No captures yet.</p>;

  return (
    <div className="captures-grid">
      {items.map((item) => (
        <div className="capture-card" key={item.name}>
          {item.type === "video" ? (
            <video
              controls
              src={`/captures/${encodeURIComponent(item.name)}`}
            />
          ) : (
            <img
              loading="lazy"
              src={`/captures/${encodeURIComponent(item.name)}`}
              alt={item.name}
            />
          )}
          <div className="capture-meta">
            {item.name}
            <br />
            {new Date(item.modified * 1000).toLocaleString()} -{" "}
            {formatBytes(item.size)}
          </div>
        </div>
      ))}
    </div>
  );
}
