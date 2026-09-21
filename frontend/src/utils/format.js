// Small presentation helpers shared by several pages.

export const DIET_OPTIONS = ["Vegetarian", "Vegan", "Jain", "Gluten-Free", "Dairy-Free"];

// The same four food photos the app already used; picked deterministically per
// restaurant so cards look varied instead of all showing the same picture.
const PLACEHOLDERS = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80",
];

export function placeholderImage(restaurant) {
  if (restaurant?.image_url) return restaurant.image_url;
  const seed = Number(restaurant?.id) || 0;
  return PLACEHOLDERS[Math.abs(seed) % PLACEHOLDERS.length];
}

export function formatDistance(km) {
  if (km === null || km === undefined) return null;
  if (km < 1) return `${Math.max(10, Math.round(km * 100) * 10)} m`;
  return `${km.toFixed(1)} km`;
}

export function capitalize(text) {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// A restaurant "supports" a diet when the backend found verified or likely evidence.
export function supportsDiet(restaurant, diet) {
  if (!diet || diet === "All") return true;
  return (restaurant.diet_tags || []).some((tag) => tag.name === diet);
}

export function matchesSearch(restaurant, query) {
  const text = query.trim().toLowerCase();
  if (!text) return true;

  return `${restaurant.name || ""} ${restaurant.cuisine || ""} ${restaurant.address || ""}`
    .toLowerCase()
    .includes(text);
}
