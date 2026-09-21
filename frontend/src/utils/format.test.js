import { describe, expect, it } from "vitest";
import { capitalize, formatDistance, matchesSearch, placeholderImage, supportsDiet } from "./format";

describe("format helpers", () => {
  it("formats distances", () => {
    expect(formatDistance(null)).toBeNull();
    expect(formatDistance(0.43)).toBe("430 m");
    expect(formatDistance(2.345)).toBe("2.3 km");
  });

  it("chooses a stable placeholder image per restaurant", () => {
    expect(placeholderImage({ id: 5 })).toBe(placeholderImage({ id: 5 }));
    expect(placeholderImage({ id: 1 })).not.toBe(placeholderImage({ id: 2 }));
    expect(placeholderImage({ id: 1, image_url: "http://x/y.jpg" })).toBe("http://x/y.jpg");
  });

  it("filters by dietary tag", () => {
    const r = { diet_tags: [{ name: "Vegan", level: "likely" }] };
    expect(supportsDiet(r, "Vegan")).toBe(true);
    expect(supportsDiet(r, "Jain")).toBe(false);
    expect(supportsDiet(r, "All")).toBe(true);
    expect(supportsDiet({}, "Vegan")).toBe(false);
  });

  it("searches name, cuisine and address case-insensitively", () => {
    const r = { name: "Udupi Bhavan", cuisine: "South Indian", address: "Anna Nagar" };
    expect(matchesSearch(r, "  ANNA ")).toBe(true);
    expect(matchesSearch(r, "pizza")).toBe(false);
    expect(matchesSearch(r, "")).toBe(true);
  });

  it("capitalizes", () => {
    expect(capitalize("dosa")).toBe("Dosa");
    expect(capitalize("")).toBe("");
  });
});
