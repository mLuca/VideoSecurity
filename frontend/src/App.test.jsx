import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App.jsx";
import * as api from "./api.js";

vi.mock("./api.js");
vi.mock("./components/LoginPage.jsx", () => ({
  default: ({ onLoggedIn }) => (
    <button onClick={onLoggedIn}>mock-login</button>
  ),
}));
vi.mock("./components/Dashboard.jsx", () => ({
  default: () => <div>mock-dashboard</div>,
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("shows a loading state before the session check resolves", () => {
    api.checkSession.mockReturnValue(new Promise(() => {}));

    render(<App />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders the login page when unauthenticated", async () => {
    api.checkSession.mockResolvedValue(false);

    render(<App />);

    expect(await screen.findByText("mock-login")).toBeInTheDocument();
  });

  it("renders the dashboard when authenticated", async () => {
    api.checkSession.mockResolvedValue(true);

    render(<App />);

    expect(await screen.findByText("mock-dashboard")).toBeInTheDocument();
  });

  it("switches from login to dashboard once logged in", async () => {
    api.checkSession.mockResolvedValue(false);
    const user = userEvent.setup();

    render(<App />);
    await user.click(await screen.findByText("mock-login"));

    expect(await screen.findByText("mock-dashboard")).toBeInTheDocument();
  });
});
