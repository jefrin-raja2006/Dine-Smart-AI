import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/api", () => ({
  getRestaurant: vi.fn(),
  getInsights: vi.fn(),
  getReviews: vi.fn(),
  submitReview: vi.fn(),
  deleteMyReview: vi.fn(),
  getFavorites: vi.fn().mockResolvedValue({ favorites: [] }),
  addFavorite: vi.fn(),
  removeFavorite: vi.fn(),
}));

import * as api from "../services/api";
import { saveSession } from "../services/session";
import RestaurantDetails from "./RestaurantDetails";

const restaurant = {
  id: 3, name: "Green Bowl", cuisine: "Vegetarian", address: "MG Road", rating: 4.5,
  review_count: 2, diet_tags: [{ name: "Vegetarian", level: "verified", note: "" }],
  diet_evidence: [{ name: "Vegetarian", level: "verified", note: "Listed on OSM" }, { name: "Jain", level: "unknown", note: "No dietary information available" }],
  menu_items: [], ai_match: 88, match_reasons: ["Vegetarian: Listed on OSM"], note: null,
  latitude: 13.0, longitude: 80.0,
};

const insights = {
  review_count: 2, confidence: "low", message: "Only 2 reviews so far - these insights are indicative, not conclusive.",
  sentiment: { positive_pct: 87, label: "positive", distribution: {} },
  trust: { score: 92, label: "high", low_trust_reviews: 0 },
  dishes: [{ name: "biryani", mentions: 2, positive_pct: 100, label: "positive" }],
  aspects: [], best_dish: { name: "biryani", positive_pct: 100, mentions: 2 },
};

const review = {
  id: 1, user_name: "Priya K", rating: 5, text: "Loved the biryani", created_at: "2026-09-01T10:00:00Z",
  sentiment: "positive", trust_label: "high", trust_reasons: ["Short review"], trust_strengths: ["Mentions specific dishes"],
  mentions: [{ name: "biryani", kind: "dish", label: "positive" }], is_mine: false,
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/restaurant/3"]}>
      <Routes><Route path="/restaurant/:id" element={<RestaurantDetails />} /></Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  api.getFavorites.mockResolvedValue({ favorites: [] });
  saveSession({ access_token: "t", user: { id: 1, name: "Me", dietary_preferences: [] } });
  api.getRestaurant.mockResolvedValue(restaurant);
  api.getInsights.mockResolvedValue(insights);
  api.getReviews.mockResolvedValue({ total: 1, reviews: [review] });
});

describe("RestaurantDetails", () => {
  it("renders real restaurant, AI match, insights and reviews", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Green Bowl" })).toBeInTheDocument();
    expect(screen.getByText("88%")).toBeInTheDocument();
    expect(screen.getByText("87%")).toBeInTheDocument();
    expect(screen.getByText(/indicative, not conclusive/)).toBeInTheDocument();
    expect(screen.getByText(/"Loved the biryani"/)).toBeInTheDocument();
    expect(screen.getByText("Listed on OSM")).toBeInTheDocument();
  });

  it("explains a review's trust level on demand", async () => {
    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: /high trust/i }));
    expect(screen.getByText("Mentions specific dishes")).toBeInTheDocument();
    expect(screen.getByText("Short review")).toBeInTheDocument();
  });

  it("validates the review form before calling the API", async () => {
    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: /post review/i }));
    expect(screen.getByText(/choose a star rating/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("radio", { name: "4 stars" }));
    await userEvent.click(screen.getByRole("button", { name: /post review/i }));
    expect(screen.getByText(/write at least a few words/i)).toBeInTheDocument();
    expect(api.submitReview).not.toHaveBeenCalled();
  });

  it("submits a review and refreshes the data", async () => {
    api.submitReview.mockResolvedValue({});
    renderPage();
    await screen.findByRole("heading", { name: "Green Bowl" });

    await userEvent.click(screen.getByRole("radio", { name: "5 stars" }));
    await userEvent.type(screen.getByLabelText("Your review"), "Fantastic dosa and friendly staff");
    await userEvent.click(screen.getByRole("button", { name: /post review/i }));

    await waitFor(() => expect(api.submitReview).toHaveBeenCalledWith(3, 5, "Fantastic dosa and friendly staff"));
    await waitFor(() => expect(api.getInsights).toHaveBeenCalledTimes(2)); // reloaded
  });

  it("shows the server's error if posting fails", async () => {
    api.submitReview.mockRejectedValue(new Error("Rate limited"));
    renderPage();
    await screen.findByRole("heading", { name: "Green Bowl" });
    await userEvent.click(screen.getByRole("radio", { name: "5 stars" }));
    await userEvent.type(screen.getByLabelText("Your review"), "Fantastic dosa and friendly staff");
    await userEvent.click(screen.getByRole("button", { name: /post review/i }));
    expect(await screen.findByText("Rate limited")).toBeInTheDocument();
  });

  it("shows an empty state when there are no reviews", async () => {
    api.getInsights.mockResolvedValue({ review_count: 0, message: "No reviews yet - be the first to share your experience.", dishes: [], aspects: [] });
    api.getReviews.mockResolvedValue({ total: 0, reviews: [] });
    renderPage();
    expect(await screen.findByText(/be the first to share/i)).toBeInTheDocument();
  });

  it("lets the author delete their own review", async () => {
    api.getReviews.mockResolvedValue({ total: 1, reviews: [{ ...review, is_mine: true }] });
    api.deleteMyReview.mockResolvedValue({});
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: /delete my review/i }));
    await waitFor(() => expect(api.deleteMyReview).toHaveBeenCalledWith("3"));
  });

  it("shows an error page for a missing restaurant", async () => {
    api.getRestaurant.mockRejectedValue(new Error("Restaurant not found"));
    renderPage();
    expect(await screen.findByText("Restaurant not found")).toBeInTheDocument();
  });
});
