import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/api", () => ({
  getNearbyRestaurants: vi.fn(),
  getRecommendations: vi.fn(),
  getFavorites: vi.fn(),
  addFavorite: vi.fn(),
  removeFavorite: vi.fn(),
  updatePreferences: vi.fn(),
  getMe: vi.fn(),
  updateName: vi.fn(),
  changePassword: vi.fn(),
}));

import * as api from "../services/api";
import { getUser, saveSession } from "../services/session";
import Home from "./Home";
import Profile from "./Profile";
import Restaurants from "./Restaurants";

const veg = { id: 1, name: "Green Bowl", cuisine: "Vegetarian", address: "MG Road", rating: 4.6, review_count: 5,
  distance_km: 0.4, amenity: "restaurant", diet_tags: [{ name: "Vegetarian", level: "verified", note: "" }] };
const steak = { id: 2, name: "Steak Palace", cuisine: "Steak House", address: "Beach Rd", rating: null, review_count: 0,
  distance_km: 1.2, amenity: "restaurant", diet_tags: [] };

const at = (ui, url = "/") => render(<MemoryRouter initialEntries={[url]}>{ui}</MemoryRouter>);

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.setItem("lastLocation", JSON.stringify({ latitude: 13.08, longitude: 80.27 }));
  saveSession({ access_token: "t", user: { id: 1, name: "Asha Rao", dietary_preferences: ["Vegetarian"] } });
  api.getFavorites.mockResolvedValue({ favorites: [] });
  api.getNearbyRestaurants.mockResolvedValue({ restaurants: [veg, steak], message: null });
  api.getRecommendations.mockResolvedValue({
    recommendations: [{ ...veg, ai_match: 90, match_reasons: ["Vegetarian: verified"], confidence: "high" }],
    message: null, disclaimer: "Not medical advice.",
  });
});

describe("Restaurants (Discover) page", () => {
  it("lists nearby restaurants from the API", async () => {
    at(<Restaurants />, "/restaurants");
    expect(await screen.findByText("Green Bowl")).toBeInTheDocument();
    expect(screen.getByText("Steak Palace")).toBeInTheDocument();
    expect(api.getNearbyRestaurants).toHaveBeenCalledWith(13.08, 80.27, 15000);
    expect(screen.getByText(/restaurants found/)).toBeInTheDocument();
  });

  it("the dietary filter really filters", async () => {
    at(<Restaurants />, "/restaurants");
    await screen.findByText("Steak Palace");
    await userEvent.click(screen.getByRole("button", { name: "Vegetarian" }));
    expect(screen.getByText("Green Bowl")).toBeInTheDocument();
    expect(screen.queryByText("Steak Palace")).not.toBeInTheDocument();
    expect(screen.getByText(/verified or likely/)).toBeInTheDocument();
  });

  it("search box filters by name", async () => {
    at(<Restaurants />, "/restaurants");
    await screen.findByText("Steak Palace");
    await userEvent.type(screen.getByLabelText("Search restaurants"), "steak");
    expect(screen.queryByText("Green Bowl")).not.toBeInTheDocument();
  });

  it("uses the recommender in AI mode and shows the disclaimer", async () => {
    at(<Restaurants />, "/restaurants?mode=ai");
    expect(await screen.findByText(/90% MATCH/)).toBeInTheDocument();
    expect(api.getRecommendations).toHaveBeenCalled();
    expect(api.getNearbyRestaurants).not.toHaveBeenCalled();
    expect(screen.getByText("Not medical advice.")).toBeInTheDocument();
  });

  it("shows the API error with a retry", async () => {
    api.getNearbyRestaurants.mockRejectedValueOnce(new Error("OpenStreetMap unavailable"));
    at(<Restaurants />, "/restaurants");
    expect(await screen.findByText(/OpenStreetMap unavailable/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(await screen.findByText("Green Bowl")).toBeInTheDocument();
  });

  it("toggling a heart calls the favorites API", async () => {
    api.addFavorite.mockResolvedValue({});
    at(<Restaurants />, "/restaurants");
    const card = (await screen.findByText("Green Bowl")).closest("article");
    await userEvent.click(within(card).getByRole("button", { name: /add to favorites/i }));
    await waitFor(() => expect(api.addFavorite).toHaveBeenCalledWith(1));
    expect(await within(card).findByRole("button", { name: /remove from favorites/i })).toBeInTheDocument();
  });
});

describe("Home page", () => {
  it("shows real AI picks and the top match", async () => {
    at(<Home />, "/home");
    expect(await screen.findAllByText("Green Bowl")).not.toHaveLength(0);
    expect(screen.getByText("90%")).toBeInTheDocument();
    expect(api.getRecommendations).toHaveBeenCalledWith(
      expect.objectContaining({ latitude: 13.08, preferences: "Vegetarian" })
    );
  });

  it("saves preference changes to the server and to the session", async () => {
    api.updatePreferences.mockResolvedValue({ dietary_preferences: ["Vegetarian", "Vegan"] });
    at(<Home />, "/home");
    await screen.findAllByText("Green Bowl");
    await userEvent.click(screen.getByRole("button", { name: /^Vegan$/, pressed: false }));
    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledWith(["Vegetarian", "Vegan"]));
    expect(getUser().dietary_preferences).toEqual(["Vegetarian", "Vegan"]);
  });

  it("rolls back a preference if saving fails", async () => {
    api.updatePreferences.mockRejectedValue(new Error("Failed to save preferences"));
    at(<Home />, "/home");
    await screen.findAllByText("Green Bowl");
    await userEvent.click(screen.getByRole("button", { name: /^Vegan$/, pressed: false }));
    expect(await screen.findByText("Failed to save preferences")).toBeInTheDocument();
    // rolled back: the Vegan toggle is un-pressed again
    expect(screen.getByRole("button", { name: /^Vegan$/, pressed: false })).toBeInTheDocument();
  });

  it("shows an empty state when there are no picks", async () => {
    api.getRecommendations.mockResolvedValue({ recommendations: [], message: null });
    at(<Home />, "/home");
    expect(await screen.findByText("No picks yet")).toBeInTheDocument();
  });
});

describe("Profile page", () => {
  const me = { id: 1, name: "Asha Rao", email: "asha@example.com", dietary_preferences: ["Vegetarian"],
    member_since: "2026-09-01T00:00:00Z", stats: { favorites: 1, reviews: 2, average_rating_given: 4.5 } };

  beforeEach(() => {
    api.getMe.mockResolvedValue(me);
    api.getFavorites.mockResolvedValue({ favorites: [veg] });
  });

  it("renders real profile data and stats", async () => {
    at(<Profile />, "/profile");
    expect(await screen.findByRole("heading", { name: "Asha Rao" })).toBeInTheDocument();
    expect(screen.getByText("asha@example.com")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
    expect(screen.getByText("Green Bowl")).toBeInTheDocument();
  });

  it("edits and saves dietary preferences", async () => {
    api.updatePreferences.mockResolvedValue({ ...me, dietary_preferences: ["Vegetarian", "Jain"] });
    at(<Profile />, "/profile");
    await userEvent.click(await screen.findByRole("button", { name: /edit/i }));
    await userEvent.click(screen.getByRole("button", { name: "Jain" }));
    await userEvent.click(screen.getByRole("button", { name: /save preferences/i }));
    await waitFor(() => expect(api.updatePreferences).toHaveBeenCalledWith(["Vegetarian", "Jain"]));
    expect(getUser().dietary_preferences).toEqual(["Vegetarian", "Jain"]);
  });

  it("removing a saved restaurant updates the list and count", async () => {
    api.removeFavorite.mockResolvedValue({});
    at(<Profile />, "/profile");
    await userEvent.click(await screen.findByRole("button", { name: /remove from favorites/i }));
    await waitFor(() => expect(api.removeFavorite).toHaveBeenCalledWith(1));
    expect(await screen.findByText(/haven't saved any/)).toBeInTheDocument();
  });

  it("changes the password and reports API errors", async () => {
    api.changePassword.mockRejectedValueOnce(new Error("Current password is incorrect"));
    at(<Profile />, "/profile");
    await screen.findByRole("heading", { name: "Asha Rao" });
    await userEvent.type(screen.getByLabelText(/current password/i), "wrongpass1");
    await userEvent.type(screen.getByLabelText(/new password/i), "newpassword1");
    await userEvent.click(screen.getByRole("button", { name: /change password/i }));
    expect(await screen.findByText("Current password is incorrect")).toBeInTheDocument();
  });
});
