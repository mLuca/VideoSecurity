import { useState } from "react";
import CapturesGrid from "./CapturesGrid.jsx";
import LogViewer from "./LogViewer.jsx";
import LiveStreamView from "./LiveStreamView.jsx";
import { logout } from "../api.js";

export default function Dashboard({ onLoggedOut }) {
  const [activeTab, setActiveTab] = useState("captures");

  async function handleLogout() {
    await logout();
    onLoggedOut();
  }

  return (
    <>
      <header className="topbar">
        <h1>Muelltonnen Security</h1>
        <button className="logout-link" onClick={handleLogout}>
          Log out
        </button>
      </header>

      <nav className="tabs">
        <button
          className={`tab-button ${activeTab === "captures" ? "active" : ""}`}
          onClick={() => setActiveTab("captures")}
        >
          Captures
        </button>
        <button
          className={`tab-button ${activeTab === "logs" ? "active" : ""}`}
          onClick={() => setActiveTab("logs")}
        >
          Logs
        </button>
        <button
          className={`tab-button ${activeTab === "livestream" ? "active" : ""}`}
          onClick={() => setActiveTab("livestream")}
        >
          Live Stream
        </button>
      </nav>

      <main>
        <section
          className={`tab-panel ${activeTab === "captures" ? "active" : ""}`}
        >
          <CapturesGrid />
        </section>
        <section
          className={`tab-panel ${activeTab === "logs" ? "active" : ""}`}
        >
          <LogViewer />
        </section>
        <section
          className={`tab-panel ${activeTab === "livestream" ? "active" : ""}`}
        >
          {/* Mounted only while selected so the stream connection opens/closes with the tab. */}
          {activeTab === "livestream" && <LiveStreamView />}
        </section>
      </main>
    </>
  );
}
