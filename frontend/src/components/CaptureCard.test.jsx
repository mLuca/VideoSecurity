import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CaptureCard from "./CaptureCard.jsx";

const item = { name: "event-1", has_video: true };

beforeEach(() => {
  window.HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  Element.prototype.requestFullscreen = vi.fn().mockResolvedValue(undefined);
  document.exitFullscreen = vi.fn().mockResolvedValue(undefined);
  vi.spyOn(window, "confirm");
});

afterEach(() => {
  vi.restoreAllMocks();
  Object.defineProperty(document, "fullscreenElement", {
    value: null,
    configurable: true,
  });
});

describe("CaptureCard", () => {
  it("disables the play button when there is no video", () => {
    render(<CaptureCard item={{ ...item, has_video: false }} onDelete={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Play capture event-1" })).toBeDisabled();
  });

  it("opens the video player when play is clicked", async () => {
    const user = userEvent.setup();
    render(<CaptureCard item={item} onDelete={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Play capture event-1" }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(window.HTMLMediaElement.prototype.play).toHaveBeenCalled();
  });

  it("only deletes after the user confirms", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    window.confirm.mockReturnValue(false);

    render(<CaptureCard item={item} onDelete={onDelete} />);
    await user.click(screen.getByRole("button", { name: "Delete capture event-1" }));
    expect(onDelete).not.toHaveBeenCalled();

    window.confirm.mockReturnValue(true);
    await user.click(screen.getByRole("button", { name: "Delete capture event-1" }));
    expect(onDelete).toHaveBeenCalledWith("event-1");
  });

  it("exits fullscreen when the player is closed while fullscreen", async () => {
    Object.defineProperty(document, "fullscreenElement", {
      value: document.createElement("div"),
      configurable: true,
    });
    const user = userEvent.setup();
    render(<CaptureCard item={item} onDelete={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Play capture event-1" }));
    await user.click(screen.getByRole("button", { name: "Close" }));

    expect(document.exitFullscreen).toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
