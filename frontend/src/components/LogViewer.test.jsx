import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import LogViewer from "./LogViewer.jsx";
import * as api from "../api.js";

vi.mock("../api.js");

afterEach(() => {
  vi.restoreAllMocks();
});

describe("LogViewer", () => {
  it("shows fetched log content", async () => {
    api.fetchLogs.mockResolvedValue({ content: "line one\nline two" });

    render(<LogViewer />);

    const pre = await screen.findByText(/line one/);
    expect(pre.textContent).toBe("line one\nline two");
  });

  it("schedules a re-poll every 3 seconds", async () => {
    const setIntervalSpy = vi.spyOn(global, "setInterval");
    api.fetchLogs.mockResolvedValue({ content: "line one" });

    render(<LogViewer />);
    await screen.findByText("line one");

    expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 3000);
  });

  it("shows a failure message when loading fails", async () => {
    api.fetchLogs.mockRejectedValue(new Error("boom"));

    render(<LogViewer />);

    expect(await screen.findByText("Failed to load logs.")).toBeInTheDocument();
  });
});
