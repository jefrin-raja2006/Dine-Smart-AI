const API_URL = "http://127.0.0.1:8000";

// ==========================================
// REGISTER
// ==========================================

export async function registerUser(data) {
  const response = await fetch(
    `${API_URL}/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail || "Registration failed"
    );
  }

  return result;
}


// ==========================================
// LOGIN
// ==========================================

export async function loginUser(data) {
  const response = await fetch(
    `${API_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail || "Login failed"
    );
  }

  return result;
}


// ==========================================
// GET ALL RESTAURANTS
// ==========================================

export async function getRestaurants() {
  const response = await fetch(
    `${API_URL}/restaurants/`
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail ||
        "Failed to load restaurants"
    );
  }

  return result;
}


// ==========================================
// GET SINGLE RESTAURANT
// ==========================================

export async function getRestaurant(id) {
  const response = await fetch(
    `${API_URL}/restaurants/${id}`
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail ||
        "Failed to load restaurant"
    );
  }

  return result;
}


// ==========================================
// GET NEARBY RESTAURANTS
// ==========================================

export async function getNearbyRestaurants(
  latitude,
  longitude,
  radius = 10000
) {
  const url =
    `${API_URL}/restaurants/nearby` +
    `?latitude=${encodeURIComponent(latitude)}` +
    `&longitude=${encodeURIComponent(longitude)}` +
    `&radius=${encodeURIComponent(radius)}`;

  console.log(
    "Nearby restaurant API:",
    url
  );

  const response = await fetch(url);

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail ||
        "Failed to load nearby restaurants"
    );
  }

  return result;
}