import { useState } from "react";

export default function LiveStreamView() {
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [src, setSrc] = useState(() => `/api/stream?t=${Date.now()}`);

  function retry() {
    setStatus("loading");
    setSrc(`/api/stream?t=${Date.now()}`);
  }

  return (
    <div className="livestream-view">
      {status !== "ready" && (
        <p className={`livestream-status ${status === "error" ? "error" : ""}`}>
          {status === "error" ? (
            <>
              Live stream unavailable.{" "}
              <button className="link-button" onClick={retry}>
                Retry
              </button>
            </>
          ) : (
            "Loading live stream…"
          )}
        </p>
      )}
      <img
        className="livestream-image"
        src={src}
        alt="Live annotated camera feed"
        style={{ display: status === "ready" ? "block" : "none" }}
        onLoad={() => setStatus("ready")}
        onError={() => setStatus("error")}
      />
    </div>
  );
}
