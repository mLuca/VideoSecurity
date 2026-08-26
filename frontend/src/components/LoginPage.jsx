import { useState } from "react";
import { login } from "../api.js";

export default function LoginPage({ onLoggedIn }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const result = await login(password);
    setSubmitting(false);
    if (result.ok) {
      onLoggedIn();
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="login-wrapper">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Muelltonnen Security</h1>
        {error && <p className="error">{error}</p>}
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoFocus
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Logging in..." : "Log in"}
        </button>
      </form>
    </div>
  );
}
