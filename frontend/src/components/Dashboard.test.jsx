import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import Dashboard from "./Dashboard.jsx";
import * as api from "../api.js";

vi.mock("../api.js");
vi.mock("./CapturesGrid.jsx", () => ({
  default: () => <div>mock-captures</div>,
}));
vi.mock("./LogViewer.jsx", () => ({ default: () => <div>mock-logs</div> }));
vi.mock("./LiveStreamView.jsx", () => ({
  default: () => <div>mock-livestream</div>,
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Dashboard", () => {
  it("mounts only the captures panel by default", () => {
    render(<Dashboard onLoggedOut={vi.fn()} />);

    expect(screen.getByText("mock-captures")).toBeInTheDocument();
    expect(screen.queryByText("mock-logs")).not.toBeInTheDocument();
    expect(screen.queryByText("mock-livestream")).not.toBeInTheDocument();
  });

  it("mounts only the selected tab's panel when switching tabs", async () => {
    const user = userEvent.setup();
    render(<Dashboard onLoggedOut={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Live Stream" }));

    expect(screen.getByText("mock-livestream")).toBeInTheDocument();
    expect(screen.queryByText("mock-captures")).not.toBeInTheDocument();
    expect(screen.queryByText("mock-logs")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Logs" }));

    expect(screen.getByText("mock-logs")).toBeInTheDocument();
    expect(screen.queryByText("mock-livestream")).not.toBeInTheDocument();
  });

  it("logs out via the API and calls onLoggedOut", async () => {
    api.logout.mockResolvedValue();
    const onLoggedOut = vi.fn();
    const user = userEvent.setup();

    render(<Dashboard onLoggedOut={onLoggedOut} />);
    await user.click(screen.getByRole("button", { name: "Log out" }));

    expect(api.logout).toHaveBeenCalled();
    expect(onLoggedOut).toHaveBeenCalled();
  });
});
