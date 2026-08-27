import { useEffect, useState } from "react";
import { deleteCapture, fetchCaptures } from "../api.js";
import CaptureCard from "./CaptureCard.jsx";

export default function CapturesGrid() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);

  async function handleDelete(name) {
    try {
      await deleteCapture(name);
      setItems((current) => current.filter((item) => item.name !== name));
    } catch {
      setError("Failed to delete capture.");
    }
  }

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
        <CaptureCard item={item} onDelete={handleDelete} key={item.name} />
      ))}
    </div>
  );
}
