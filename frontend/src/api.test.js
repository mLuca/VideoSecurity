import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  checkSession,
  deleteCapture,
  fetchCaptures,
  fetchLogs,
  login,
  logout,
} from "./api.js";

function jsonResponse(body, { ok = true } = {}) {
  return { ok, json: () => Promise.resolve(body) };
}

beforeEach(() => {
  global.fetch = vi.fn();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("checkSession", () => {
  it("returns the authenticated flag on success", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ authenticated: true }));

    await expect(checkSession()).resolves.toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/session",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("returns false when the response is not ok", async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false }));

    await expect(checkSession()).resolves.toBe(false);
  });
});

describe("login", () => {
  it("sends the password and reports ok on success", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ ok: true }));

    const result = await login("hunter2");

    expect(result).toEqual({ ok: true });
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/login",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: "hunter2" }),
        credentials: "include",
      }),
    );
  });

  it("returns the server error message on failure", async () => {
    global.fetch.mockResolvedValue(
      jsonResponse({ error: "Invalid password." }, { ok: false }),
    );

    await expect(login("wrong")).resolves.toEqual({
      ok: false,
      error: "Invalid password.",
    });
  });

  it("falls back to a default error message when the body can't be parsed", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      json: () => Promise.reject(new Error("bad json")),
    });

    await expect(login("wrong")).resolves.toEqual({
      ok: false,
      error: "Login failed.",
    });
  });
});

describe("logout", () => {
  it("posts to /api/logout", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ ok: true }));

    await logout();

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/logout",
      expect.objectContaining({ method: "POST" }),
    );
  });
});

describe("fetchCaptures", () => {
  it("returns the parsed list on success", async () => {
    const items = [{ name: "a" }];
    global.fetch.mockResolvedValue(jsonResponse(items));

    await expect(fetchCaptures()).resolves.toEqual(items);
  });

  it("throws when the response is not ok", async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false }));

    await expect(fetchCaptures()).rejects.toThrow("Failed to load captures.");
  });
});

describe("deleteCapture", () => {
  it("sends a DELETE request with the URL-encoded name", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ ok: true }));

    await deleteCapture("event with spaces");

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/captures/event%20with%20spaces",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("throws when the response is not ok", async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false }));

    await expect(deleteCapture("x")).rejects.toThrow("Failed to delete capture.");
  });
});

describe("fetchLogs", () => {
  it("returns the parsed content on success", async () => {
    global.fetch.mockResolvedValue(jsonResponse({ content: "log lines" }));

    await expect(fetchLogs()).resolves.toEqual({ content: "log lines" });
  });

  it("throws when the response is not ok", async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false }));

    await expect(fetchLogs()).rejects.toThrow("Failed to load logs.");
  });
});
