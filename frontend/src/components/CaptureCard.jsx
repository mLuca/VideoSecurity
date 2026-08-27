import { useEffect, useRef, useState } from "react";

export default function CaptureCard({ item, onDelete }) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(false);

  const baseUrl = `/captures/${encodeURIComponent(item.name)}`;
  const triggerUrl = `${baseUrl}/trigger.jpeg`;
  const videoUrl = `${baseUrl}/video.mp4`;

  useEffect(() => {
    if (!playing || !videoRef.current) return;

    const video = videoRef.current;
    video.play().catch(() => setPlaying(false));
    video.requestFullscreen?.().catch(() => {});
  }, [playing]);

  function closePlayer() {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    setPlaying(false);
  }

  function handleDelete() {
    if (window.confirm(`Delete capture ${item.name}?`)) onDelete(item.name);
  }

  return (
    <article className="capture-card">
      <img
        loading="lazy"
        src={triggerUrl}
        alt={`Trigger frame from ${item.name}`}
      />
      <div className="capture-actions">
        <button
          type="button"
          className="play-button"
          onClick={() => setPlaying(true)}
          disabled={!item.has_video}
          aria-label={`Play capture ${item.name}`}
          title="Play capture"
        >
          ▶
        </button>
        <button
          type="button"
          onClick={handleDelete}
          className="danger-button"
          aria-label={`Delete capture ${item.name}`}
          title="Delete capture"
        >
          🗑
        </button>
      </div>
      <div className="capture-meta">{item.name}</div>

      {playing && (
        <div
          className="video-player"
          role="dialog"
          aria-label={`Video capture ${item.name}`}
        >
          <video ref={videoRef} controls src={videoUrl} onEnded={closePlayer} />
          <button type="button" onClick={closePlayer}>
            Close
          </button>
        </div>
      )}
    </article>
  );
}
