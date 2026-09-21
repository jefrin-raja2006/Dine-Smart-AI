import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import RestaurantCard from "./RestaurantCard";

const base = {
  id: 7, name: "Udupi Bhavan", cuisine: "South Indian", address: "Anna Nagar",
  rating: 4.5, review_count: 12, distance_km: 0.8, amenity: "restaurant",
  diet_tags: [{ name: "Vegetarian", level: "verified", note: "n" }],
};

const renderCard = (props) =>
  render(<MemoryRouter><RestaurantCard restaurant={{ ...base, ...props.restaurant }} {...props} /></MemoryRouter>);

describe("RestaurantCard", () => {
  it("shows the real data and links to the details page", () => {
    renderCard({});
    expect(screen.getByText("Udupi Bhavan")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
    expect(screen.getByText("800 m")).toBeInTheDocument();
    expect(screen.getByText(/12 reviews/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view restaurant/i })).toHaveAttribute("href", "/restaurant/7");
  });

  it("labels inferred dietary info as 'likely'", () => {
    renderCard({ restaurant: { diet_tags: [{ name: "Vegan", level: "likely" }] } });
    expect(screen.getByText(/Vegan · likely/)).toBeInTheDocument();
  });

  it("shows 'New' and 'No reviews yet' for unreviewed places", () => {
    renderCard({ restaurant: { rating: null, review_count: 0 } });
    expect(screen.getByText("New")).toBeInTheDocument();
    expect(screen.getByText("No reviews yet")).toBeInTheDocument();
  });

  it("shows AI match, reasons and note when present", () => {
    renderCard({ restaurant: { ai_match: 91, match_reasons: ["Only 0.8 km away"], note: "Confirm with restaurant", recommended_dish: "dosa" } });
    expect(screen.getByText(/91% MATCH/)).toBeInTheDocument();
    expect(screen.getByText("Only 0.8 km away")).toBeInTheDocument();
    expect(screen.getByText("Confirm with restaurant")).toBeInTheDocument();
    expect(screen.getByText("dosa")).toBeInTheDocument();
  });

  it("toggles favorite", async () => {
    const onToggle = vi.fn();
    renderCard({ onToggleFavorite: onToggle });
    await userEvent.click(screen.getByRole("button", { name: /add to favorites/i }));
    expect(onToggle).toHaveBeenCalledWith(expect.objectContaining({ id: 7 }));
  });

  it("reflects favorite state accessibly", () => {
    renderCard({ isFavorite: true, onToggleFavorite: () => {} });
    expect(screen.getByRole("button", { name: /remove from favorites/i })).toHaveAttribute("aria-pressed", "true");
  });
});
