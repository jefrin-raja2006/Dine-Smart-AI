// =========================================================
// SESSION (logged-in user + JWT access token)
// =========================================================
// The token is kept in localStorage so a refresh keeps you logged in.
// (For higher-security deployments, move it to an httpOnly cookie.)

const USER_KEY = "user";
const TOKEN_KEY = "token";

export const SESSION_EXPIRED_EVENT = "dinesmart:session-expired";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  return Boolean(getToken() && getUser());
}

export function saveSession({ access_token, user }) {
  localStorage.setItem(TOKEN_KEY, access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function updateStoredUser(partial) {
  const current = getUser();
  if (!current) return null;

  const updated = { ...current, ...partial };
  localStorage.setItem(USER_KEY, JSON.stringify(updated));
  return updated;
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  // legacy key from the first version of the app
  localStorage.removeItem("dietaryPreferences");
}
