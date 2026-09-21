import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Check,
  Heart,
  Leaf,
  Lock,
  MessageSquare,
  Pencil,
  Star,
  User as UserIcon,
} from "lucide-react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import RestaurantCard from "../components/RestaurantCard";
import {
  changePassword,
  getFavorites,
  getMe,
  removeFavorite,
  updateName,
  updatePreferences,
} from "../services/api";
import { clearSession, updateStoredUser } from "../services/session";
import { DIET_OPTIONS, formatDate } from "../utils/format";

export default function Profile() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editingPrefs, setEditingPrefs] = useState(false);
  const [draftPrefs, setDraftPrefs] = useState([]);
  const [name, setName] = useState("");
  const [nameMessage, setNameMessage] = useState("");

  const [passwords, setPasswords] = useState({ current: "", next: "" });
  const [passwordMessage, setPasswordMessage] = useState({ type: "", text: "" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const [me, favs] = await Promise.all([getMe(), getFavorites()]);
    setProfile(me);
    setName(me.name);
    setFavorites(favs.favorites || []);
    updateStoredUser({ name: me.name, dietary_preferences: me.dietary_preferences });
  }, []);

  useEffect(() => {
    let cancelled = false;

    load()
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [load]);

  const savePreferences = async () => {
    setSaving(true);
    try {
      const updated = await updatePreferences(draftPrefs);
      setProfile(updated);
      updateStoredUser({ dietary_preferences: updated.dietary_preferences });
      setEditingPrefs(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const saveName = async (event) => {
    event.preventDefault();
    setNameMessage("");
    try {
      const updated = await updateName(name);
      setProfile(updated);
      updateStoredUser({ name: updated.name });
      setNameMessage("Name updated.");
    } catch (err) {
      setNameMessage(err.message);
    }
  };

  const savePassword = async (event) => {
    event.preventDefault();
    setPasswordMessage({ type: "", text: "" });
    try {
      await changePassword(passwords.current, passwords.next);
      setPasswords({ current: "", next: "" });
      setPasswordMessage({ type: "ok", text: "Password updated." });
    } catch (err) {
      setPasswordMessage({ type: "error", text: err.message });
    }
  };

  const handleRemoveFavorite = async (restaurant) => {
    try {
      await removeFavorite(restaurant.id);
      setFavorites((current) => current.filter((f) => f.id !== restaurant.id));
      setProfile((current) => ({
        ...current,
        stats: { ...current.stats, favorites: Math.max(0, current.stats.favorites - 1) },
      }));
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <Navbar />
        <main className="profile-page">
          <div className="loading">Loading your profile…</div>
        </main>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="app">
        <Navbar />
        <main className="profile-page">
          <div className="error">{error || "Unable to load your profile."}</div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <Navbar />

      <main className="profile-page">
        <section className="profile-header">
          <div className="profile-avatar">{profile.name?.[0]?.toUpperCase()}</div>

          <div>
            <span className="eyebrow">YOUR ACCOUNT</span>
            <h1>{profile.name}</h1>
            <p>{profile.email}</p>
            {profile.member_since && <small>Member since {formatDate(profile.member_since)}</small>}
          </div>
        </section>

        {error && <div className="error">{error}</div>}

        <section className="profile-stats">
          <div className="stat-card">
            <Heart size={20} />
            <strong>{profile.stats.favorites}</strong>
            <span>Saved restaurants</span>
          </div>
          <div className="stat-card">
            <MessageSquare size={20} />
            <strong>{profile.stats.reviews}</strong>
            <span>Reviews written</span>
          </div>
          <div className="stat-card">
            <Star size={20} />
            <strong>{profile.stats.average_rating_given ?? "—"}</strong>
            <span>Average rating given</span>
          </div>
        </section>

        {/* DIETARY PREFERENCES */}
        <section className="profile-card">
          <div className="profile-card-header">
            <div>
              <h2>Dietary preferences</h2>
              <p>These shape every AI recommendation you see.</p>
            </div>

            {!editingPrefs && (
              <button
                className="secondary-button"
                onClick={() => {
                  setDraftPrefs(profile.dietary_preferences);
                  setEditingPrefs(true);
                }}
              >
                <Pencil size={14} />
                Edit
              </button>
            )}
          </div>

          {!editingPrefs ? (
            <div className="profile-tags">
              {profile.dietary_preferences.length > 0 ? (
                profile.dietary_preferences.map((pref) => (
                  <span key={pref} className="diet-tag verified">
                    <Leaf size={12} />
                    {pref}
                  </span>
                ))
              ) : (
                <p className="muted">No preferences set yet.</p>
              )}
            </div>
          ) : (
            <>
              <div className="profile-tags editing">
                {DIET_OPTIONS.map((option) => {
                  const active = draftPrefs.includes(option);
                  return (
                    <button
                      key={option}
                      className={`filter ${active ? "active" : ""}`}
                      aria-pressed={active}
                      onClick={() =>
                        setDraftPrefs((current) =>
                          active ? current.filter((x) => x !== option) : [...current, option]
                        )
                      }
                    >
                      {active && <Check size={13} />}
                      {option}
                    </button>
                  );
                })}
              </div>

              <div className="profile-actions">
                <button className="primary-button" onClick={savePreferences} disabled={saving}>
                  {saving ? "Saving…" : "Save preferences"}
                </button>
                <button className="secondary-button" onClick={() => setEditingPrefs(false)}>
                  Cancel
                </button>
              </div>
            </>
          )}
        </section>

        {/* FAVORITES */}
        <section className="profile-card">
          <div className="profile-card-header">
            <div>
              <h2>Saved restaurants</h2>
              <p>Places you've saved also teach the AI what you like.</p>
            </div>
          </div>

          {favorites.length === 0 ? (
            <div className="no-results">
              <Heart size={28} />
              <p>You haven't saved any restaurants yet.</p>
              <Link className="primary-button" to="/restaurants">
                Discover restaurants
              </Link>
            </div>
          ) : (
            <div className="restaurant-grid">
              {favorites.map((restaurant) => (
                <RestaurantCard
                  key={restaurant.id}
                  restaurant={restaurant}
                  isFavorite
                  onToggleFavorite={handleRemoveFavorite}
                />
              ))}
            </div>
          )}
        </section>

        {/* ACCOUNT SETTINGS */}
        <section className="profile-card">
          <div className="profile-card-header">
            <div>
              <h2>Account settings</h2>
              <p>Update your name or change your password.</p>
            </div>
          </div>

          <div className="settings-grid">
            <form onSubmit={saveName} className="settings-form">
              <label>
                <span>
                  <UserIcon size={14} /> Display name
                </span>
                <input value={name} onChange={(e) => setName(e.target.value)} maxLength={100} required />
              </label>
              <button className="secondary-button" type="submit">
                Save name
              </button>
              {nameMessage && <small className="muted">{nameMessage}</small>}
            </form>

            <form onSubmit={savePassword} className="settings-form">
              <label>
                <span>
                  <Lock size={14} /> Current password
                </span>
                <input
                  type="password"
                  autoComplete="current-password"
                  value={passwords.current}
                  onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                  required
                />
              </label>
              <label>
                <span>New password (min 8 characters)</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  value={passwords.next}
                  onChange={(e) => setPasswords({ ...passwords, next: e.target.value })}
                  minLength={8}
                  required
                />
              </label>
              <button className="secondary-button" type="submit">
                Change password
              </button>
              {passwordMessage.text && (
                <small className={passwordMessage.type === "error" ? "form-error" : "muted"}>
                  {passwordMessage.text}
                </small>
              )}
            </form>
          </div>
        </section>

        <button
          className="secondary-button logout-wide"
          onClick={() => {
            clearSession();
            navigate("/");
          }}
        >
          Log out
        </button>
      </main>

      <Footer />
    </div>
  );
}
