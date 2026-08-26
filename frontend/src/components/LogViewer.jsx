import { useEffect, useRef, useState } from "react";
import { fetchLogs } from "../api.js";

export default function LogViewer() {
  const [content, setContent] = useState("Loading...");
  const preRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchLogs();
        if (cancelled) return;
        const pre = preRef.current;
        const atBottom =
          pre && pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 20;
        setContent(data.content);
        if (pre && atBottom) {
          requestAnimationFrame(() => {
            pre.scrollTop = pre.scrollHeight;
          });
        }
      } catch {
        if (!cancelled) setContent("Failed to load logs.");
      }
    }

    load();
    const id = setInterval(load, 3000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <pre ref={preRef} className="logs-view">
      {content}
    </pre>
  );
}
