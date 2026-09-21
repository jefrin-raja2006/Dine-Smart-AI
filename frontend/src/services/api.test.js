import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getRecommendations, loginUser, request, submitReview } from "./api";
import { SESSION_EXPIRED_EVENT, saveSession } from "./session";

function mockFetch(status, body) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

beforeEach(() => saveSession({ access_token: "tok", user: { id: 1 } }));
afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("sends the bearer token on protected calls", async () => {
    const fetchMock = mockFetch(200, { ok: true });
    await request("/users/me");
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer tok");
  });

  it("does not send a token on login", async () => {
    const fetchMock = mockFetch(200, { access_token: "x" });
    await loginUser({ email: "a@b.co", password: "12345678" });
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
  });

  it("serialises the review payload", async () => {
    const fetchMock = mockFetch(201, {});
    await submitReview(7, 4, "Great dosa");
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain("/restaurants/7/reviews");
    expect(JSON.parse(options.body)).toEqual({ rating: 4, text: "Great dosa" });
  });

  it("builds a query string and skips empty values", async () => {
    const fetchMock = mockFetch(200, {});
    await getRecommendations({ latitude: 13.1, longitude: 80.2, preferences: "", limit: 6 });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toContain("latitude=13.1");
    expect(url).toContain("limit=6");
    expect(url).not.toContain("preferences");
  });

  it("uses the API's error message", async () => {
    mockFetch(400, { detail: "Email already registered" });
    await expect(request("/x", { method: "POST", body: {} })).rejects.toThrow("Email already registered");
  });

  it("formats validation errors from FastAPI", async () => {
    mockFetch(422, { detail: [{ loc: ["body", "text"], msg: "String too short" }] });
    await expect(request("/x")).rejects.toThrow("text: String too short");
  });

  it("logs the user out and notifies the app on 401", async () => {
    mockFetch(401, { detail: "Session expired" });
    const listener = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, listener);

    await expect(request("/users/me")).rejects.toMatchObject({ status: 401 });

    expect(listener).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem("token")).toBeNull();
    window.removeEventListener(SESSION_EXPIRED_EVENT, listener);
  });

  it("a failed login (401) does not trigger the logout flow", async () => {
    mockFetch(401, { detail: "Invalid email or password" });
    const listener = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, listener);
    await expect(loginUser({ email: "a@b.co", password: "x" })).rejects.toThrow("Invalid email or password");
    expect(listener).not.toHaveBeenCalled();
    window.removeEventListener(SESSION_EXPIRED_EVENT, listener);
  });

  it("explains network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(request("/x")).rejects.toThrow(/Cannot reach the server/);
  });
});
