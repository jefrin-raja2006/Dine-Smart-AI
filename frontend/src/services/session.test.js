import { describe, expect, it } from "vitest";
import {
  clearSession,
  getToken,
  getUser,
  isLoggedIn,
  saveSession,
  updateStoredUser,
} from "./session";

const session = { access_token: "abc", user: { id: 1, name: "Asha", dietary_preferences: [] } };

describe("session", () => {
  it("starts logged out", () => {
    expect(isLoggedIn()).toBe(false);
    expect(getUser()).toBeNull();
  });

  it("saves and reads a session", () => {
    saveSession(session);
    expect(getToken()).toBe("abc");
    expect(getUser().name).toBe("Asha");
    expect(isLoggedIn()).toBe(true);
  });

  it("requires a token, not just a user (old sessions must re-login)", () => {
    localStorage.setItem("user", JSON.stringify(session.user));
    expect(isLoggedIn()).toBe(false);
  });

  it("merges updates into the stored user", () => {
    saveSession(session);
    updateStoredUser({ dietary_preferences: ["Vegan"] });
    expect(getUser()).toMatchObject({ name: "Asha", dietary_preferences: ["Vegan"] });
  });

  it("survives corrupted storage", () => {
    localStorage.setItem("user", "{not json");
    expect(getUser()).toBeNull();
  });

  it("clears everything on logout", () => {
    saveSession(session);
    localStorage.setItem("dietaryPreferences", "[]");
    clearSession();
    expect(getToken()).toBeNull();
    expect(getUser()).toBeNull();
    expect(localStorage.getItem("dietaryPreferences")).toBeNull();
  });
});
