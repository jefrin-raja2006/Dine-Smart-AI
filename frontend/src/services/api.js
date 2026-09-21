import { clearSession, getToken, SESSION_EXPIRED_EVENT } from "./session";

export const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

// =========================================================
// CORE REQUEST HELPER
// =========================================================

function errorMessage(result, fallback) {
  const detail = result?.detail;

  if (typeof detail === "string") return detail;

  // FastAPI validation errors: [{ loc, msg, ... }]
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : "";
    return field ? `${field}: ${first.msg}` : first.msg;
  }

  return fallback;
}

export async function request(path, { method = "GET", body, auth = true } = {}, fallback = "Request failed") {
  const headers = {};

  if (body !== undefined) headers["Content-Type"] = "application/json";

  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Check your connection and try again.");
  }

  let result = null;
  try {
    result = await response.json();
  } catch {
    // empty / non-JSON body
  }

  if (!response.ok) {
    // An expired or invalid token on a protected call: log the user out.
    if (response.status === 401 && auth && token) {
      clearSession();
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }

    const error = new Error(errorMessage(result, fallback));
    error.status = response.status;
    throw error;
  }

  return result;
}

const qs = (params) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, value);
    }
  });
  const text = search.toString();
  return text ? `?${text}` : "";
};

// =========================================================
// AUTH
// =========================================================

export const registerUser = (data) =>
  request("/auth/register", { method: "POST", body: data, auth: false }, "Registration failed");

export const loginUser = (data) =>
  request("/auth/login", { method: "POST", body: data, auth: false }, "Login failed");

// =========================================================
// USER PROFILE
// =========================================================

export const getMe = () => request("/users/me", {}, "Failed to load profile");

export const updateName = (name) =>
  request("/users/me", { method: "PUT", body: { name } }, "Failed to update name");

export const updatePreferences = (dietary_preferences) =>
  request(
    "/users/me/preferences",
    { method: "PUT", body: { dietary_preferences } },
    "Failed to save preferences"
  );

export const changePassword = (current_password, new_password) =>
  request(
    "/users/me/password",
    { method: "POST", body: { current_password, new_password } },
    "Failed to change password"
  );

// =========================================================
// RESTAURANTS
// =========================================================

export const getRestaurants = (params = {}) =>
  request(`/restaurants/${qs(params)}`, { auth: false }, "Failed to load restaurants");

export const getRestaurant = (id, location) =>
  request(
    `/restaurants/${id}${qs({ latitude: location?.latitude, longitude: location?.longitude })}`,
    {},
    "Failed to load restaurant"
  );

export const getNearbyRestaurants = (latitude, longitude, radius = 10000) =>
  request(
    `/restaurants/nearby${qs({ latitude, longitude, radius })}`,
    { auth: false },
    "Failed to load nearby restaurants"
  );

// =========================================================
// REVIEWS & AI INSIGHTS
// =========================================================

export const getReviews = (restaurantId, params = {}) =>
  request(`/restaurants/${restaurantId}/reviews${qs(params)}`, {}, "Failed to load reviews");

export const getInsights = (restaurantId) =>
  request(`/restaurants/${restaurantId}/insights`, { auth: false }, "Failed to load insights");

export const submitReview = (restaurantId, rating, text) =>
  request(
    `/restaurants/${restaurantId}/reviews`,
    { method: "POST", body: { rating, text } },
    "Failed to submit review"
  );

export const deleteMyReview = (restaurantId) =>
  request(
    `/restaurants/${restaurantId}/reviews/mine`,
    { method: "DELETE" },
    "Failed to delete review"
  );

// =========================================================
// FAVORITES
// =========================================================

export const getFavorites = () => request("/favorites", {}, "Failed to load favorites");

export const addFavorite = (restaurantId) =>
  request(`/favorites/${restaurantId}`, { method: "POST" }, "Failed to add favorite");

export const removeFavorite = (restaurantId) =>
  request(`/favorites/${restaurantId}`, { method: "DELETE" }, "Failed to remove favorite");

// =========================================================
// AI RECOMMENDATIONS
// =========================================================

export const getRecommendations = ({ latitude, longitude, radius, preferences, limit } = {}) =>
  request(
    `/recommendations/me${qs({ latitude, longitude, radius, preferences, limit })}`,
    {},
    "Failed to load recommendations"
  );
