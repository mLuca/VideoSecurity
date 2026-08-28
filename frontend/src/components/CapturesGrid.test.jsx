import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import CapturesGrid from "./CapturesGrid.jsx";
import * as api from "../api.js";

vi.mock("../api.js");
vi.mock("./CaptureCard.jsx", () => ({
  default: ({ item, onDelete }) => (
    <div>
      {item.name}
      <button onClick={() => onDelete(item.name)}>delete-{item.name}</button>
    </div>
  ),
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("CapturesGrid", () => {
  it("renders captures returned by the API", async () => {
    api.fetchCaptures.mockResolvedValue([{ name: "event-1", has_video: true }]);

    render(<CapturesGrid />);

    expect(await screen.findByText("event-1")).toBeInTheDocument();
  });

  it("shows a placeholder when there are no captures", async () => {
    api.fetchCaptures.mockResolvedValue([]);

    render(<CapturesGrid />);

    expect(await screen.findByText("No captures yet.")).toBeInTheDocument();
  });

  it("shows an error message when loading fails", async () => {
    api.fetchCaptures.mockRejectedValue(new Error("boom"));

    render(<CapturesGrid />);

    expect(await screen.findByText("Failed to load captures.")).toBeInTheDocument();
  });

  it("schedules a re-poll every 5 seconds", async () => {
    const setIntervalSpy = vi.spyOn(global, "setInterval");
    api.fetchCaptures.mockResolvedValue([]);

    render(<CapturesGrid />);
    await screen.findByText("No captures yet.");

    expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 5000);
  });

  it("removes a capture from the list once deleted", async () => {
    api.fetchCaptures.mockResolvedValue([{ name: "event-1", has_video: true }]);
    api.deleteCapture.mockResolvedValue();
    const user = userEvent.setup();

    render(<CapturesGrid />);
    await screen.findByText("event-1");

    await user.click(screen.getByText("delete-event-1"));

    expect(api.deleteCapture).toHaveBeenCalledWith("event-1");
    expect(await screen.findByText("No captures yet.")).toBeInTheDocument();
  });

  it("shows an error when deletion fails", async () => {
    api.fetchCaptures.mockResolvedValue([{ name: "event-1", has_video: true }]);
    api.deleteCapture.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();

    render(<CapturesGrid />);
    await screen.findByText("event-1");

    await user.click(screen.getByText("delete-event-1"));

    expect(await screen.findByText("Failed to delete capture.")).toBeInTheDocument();
  });
});
