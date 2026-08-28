import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import LoginPage from "./LoginPage.jsx";
import * as api from "../api.js";

vi.mock("../api.js");

afterEach(() => {
  vi.restoreAllMocks();
});

describe("LoginPage", () => {
  it("submits the typed password and reports success", async () => {
    api.login.mockResolvedValue({ ok: true });
    const onLoggedIn = vi.fn();
    const user = userEvent.setup();

    render(<LoginPage onLoggedIn={onLoggedIn} />);
    await user.type(screen.getByLabelText("Password"), "hunter2");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    await waitFor(() => expect(onLoggedIn).toHaveBeenCalled());
    expect(api.login).toHaveBeenCalledWith("hunter2");
  });

  it("shows the server error and does not log in on failure", async () => {
    api.login.mockResolvedValue({ ok: false, error: "Invalid password." });
    const onLoggedIn = vi.fn();
    const user = userEvent.setup();

    render(<LoginPage onLoggedIn={onLoggedIn} />);
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Invalid password.")).toBeInTheDocument();
    expect(onLoggedIn).not.toHaveBeenCalled();
  });

  it("disables the submit button while submitting", async () => {
    let resolveLogin;
    api.login.mockReturnValue(
      new Promise((resolve) => {
        resolveLogin = resolve;
      }),
    );
    const user = userEvent.setup();

    render(<LoginPage onLoggedIn={vi.fn()} />);
    await user.type(screen.getByLabelText("Password"), "hunter2");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    const button = screen.getByRole("button", { name: "Logging in..." });
    expect(button).toBeDisabled();

    resolveLogin({ ok: true });
  });
});
