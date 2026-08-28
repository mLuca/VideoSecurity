import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import LiveStreamView from "./LiveStreamView.jsx";

describe("LiveStreamView", () => {
  it("starts in the loading state", () => {
    render(<LiveStreamView />);

    expect(screen.getByText("Loading live stream…")).toBeInTheDocument();
    expect(screen.getByAltText("Live annotated camera feed")).not.toBeVisible();
  });

  it("shows the image once it loads", () => {
    render(<LiveStreamView />);

    fireEvent.load(screen.getByAltText("Live annotated camera feed"));

    expect(screen.queryByText("Loading live stream…")).not.toBeInTheDocument();
    expect(screen.getByAltText("Live annotated camera feed")).toBeVisible();
  });

  it("shows a retry option on error and reloads on click", async () => {
    const user = userEvent.setup();
    render(<LiveStreamView />);
    const img = screen.getByAltText("Live annotated camera feed");
    const initialSrc = img.src;

    fireEvent.error(img);

    expect(screen.getByText("Live stream unavailable.", { exact: false })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(screen.getByText("Loading live stream…")).toBeInTheDocument();
    expect(img.src).not.toBe(initialSrc);
  });
});
