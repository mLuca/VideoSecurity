import { useEffect, useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import Dashboard from "./components/Dashboard.jsx";
import { checkSession } from "./api.js";
import "./styles.css";

export default function App() {
  const [authenticated, setAuthenticated] = useState(null); // null = still checking

  useEffect(() => {
    checkSession().then(setAuthenticated);
  }, []);

  if (authenticated === null) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!authenticated) {
    return <LoginPage onLoggedIn={() => setAuthenticated(true)} />;
  }

  return <Dashboard onLoggedOut={() => setAuthenticated(false)} />;
}
