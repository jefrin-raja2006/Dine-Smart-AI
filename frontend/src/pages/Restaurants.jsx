import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { MapPin, Navigation, Search, ShieldCheck, Sparkles } from "lucide-react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import RestaurantCard from "../components/RestaurantCard";
import useFavorites from "../hooks/useFavorites";
import useLocation from "../hooks/useLocation";
import { getNearbyRestaurants, getRecommendations } from "../services/api";
import { DIET_OPTIONS, matchesSearch, supportsDiet } from "../utils/format";

const SEARCH_RADIUS = 15000;

export default function Restaurants() {
  const [params, setParams] = useSearchParams();

  // "AI mode" ranks by personal match; normal mode lists the nearest places.
  const preferencesParam = params.get("preferences") || "";
  const mode = params.get("mode") === "ai" || preferencesParam ? "ai" : "nearby";

  const [search, setSearch] = useState(params.get("search") || "");
  const [diet, setDiet] = useState("All");

  const [restaurants, setRestaurants] = useState([]);
  const [message, setMessage] = useState("");
  const [disclaimer, setDisclaimer] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  const { location, loading: locating, error: locationError, locate } = useLocation();
  const favorites = useFavorites();
  const requestId = useRef(0);

  // ---------------------------------------------------------
  // Load restaurants for the current location + mode
  // ---------------------------------------------------------
  useEffect(() => {
    if (!location) return;

    const current = ++requestId.current;

    const load =
      mode === "ai"
        ? getRecommendations({
            latitude: location.latitude,
            longitude: location.longitude,
            radius: SEARCH_RADIUS,
            limit: 60,
            preferences: preferencesParam || undefined,
          }).then((result) => ({
            list: result.recommendations || [],
            message: result.message || "",
            disclaimer: result.disclaimer || "",
          }))
        : getNearbyRestaurants(location.latitude, location.longitude, SEARCH_RADIUS).then(
            (result) => ({
              list: result.restaurants || [],
              message: result.message || "",
              disclaimer: "",
            })
          );

    setLoading(true);
    setError("");

    load
      .then((result) => {
        if (current !== requestId.current) return;
        setRestaurants(result.list);
        setMessage(result.message);
        setDisclaimer(result.disclaimer);
      })
      .catch((err) => {
        if (current !== requestId.current) return;
        setError(err.message || "Unable to load restaurants.");
      })
      .finally(() => {
        if (current === requestId.current) setLoading(false);
      });
  }, [location, mode, preferencesParam, reloadKey]);

  const setMode = (next) => {
    const updated = new URLSearchParams(params);
    updated.delete("preferences");
    if (next === "ai") updated.set("mode", "ai");
    else updated.delete("mode");
    setParams(updated);
  };

  const filtered = useMemo(
    () =>
      restaurants.filter(
        (restaurant) => matchesSearch(restaurant, search) && supportsDiet(restaurant, diet)
      ),
    [restaurants, search, diet]
  );

  const busy = locating || loading;
  const shownError = error || (!location && !locating ? locationError : "");

  return (
    <div className="app">
      <Navbar />

      <main className="listing-page">
        <div className="listing-heading">
          <span className="eyebrow">
            {mode === "ai" ? "AI PICKS FOR YOU" : "DISCOVER NEAR YOU"}
          </span>

          <h1>{mode === "ai" ? "Restaurants that fit you." : "Find your next favorite place."}</h1>

          <p>
            {mode === "ai"
              ? "Ranked by your dietary preferences, saved places, reviews and distance."
              : "Real restaurants discovered around your current location."}
          </p>
        </div>

        {/* LOCATION */}
        <div className="location-status">
          <MapPin size={18} />

          <div>
            <strong>Your current location</strong>
            <span>
              {location
                ? `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`
                : locating
                  ? "Detecting…"
                  : "Not available"}
            </span>
          </div>

          <button
            onClick={() => {
              locate();
              setReloadKey((k) => k + 1);
            }}
            disabled={busy}
          >
            <Navigation size={15} />
            {busy ? "Finding…" : "Refresh location"}
          </button>
        </div>

        {/* MODE + SEARCH + DIET FILTER */}
        <div className="mode-switch" role="tablist" aria-label="Sort restaurants">
          <button
            role="tab"
            aria-selected={mode === "nearby"}
            className={mode === "nearby" ? "active" : ""}
            onClick={() => setMode("nearby")}
          >
            <MapPin size={15} />
            Nearest
          </button>
          <button
            role="tab"
            aria-selected={mode === "ai"}
            className={mode === "ai" ? "active" : ""}
            onClick={() => setMode("ai")}
          >
            <Sparkles size={15} />
            AI picks
          </button>
        </div>

        <div className="listing-controls">
          <div className="listing-search">
            <Search size={19} />
            <input
              placeholder="Search restaurants, cuisines, areas..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search restaurants"
            />
          </div>

          {["All", ...DIET_OPTIONS].map((item) => (
            <button
              key={item}
              className={diet === item ? "filter active" : "filter"}
              onClick={() => setDiet(item)}
              aria-pressed={diet === item}
            >
              {item}
            </button>
          ))}
        </div>

        {diet !== "All" && (
          <p className="filter-hint">
            Showing places with verified or likely <b>{diet}</b> options. "Likely" is
            inferred (e.g. from cuisine) - please confirm with the restaurant.
          </p>
        )}

        {message && <div className="info-banner">{message}</div>}
        {favorites.error && <div className="inline-error">{favorites.error}</div>}

        {busy && (
          <div className="loading">
            <MapPin size={20} />
            Finding restaurants near you…
          </div>
        )}

        {!busy && shownError && (
          <div className="error">
            {shownError}
            <button className="link-button" onClick={location ? () => setReloadKey((k) => k + 1) : locate}>
              Try again
            </button>
          </div>
        )}

        {!busy && !shownError && location && (
          <>
            <div className="nearby-count">
              <strong>{filtered.length}</strong> {filtered.length === 1 ? "restaurant" : "restaurants"} found
            </div>

            <div className="restaurant-grid">
              {filtered.map((restaurant) => (
                <RestaurantCard
                  key={restaurant.id}
                  restaurant={restaurant}
                  isFavorite={favorites.isFavorite(restaurant.id)}
                  favoriteBusy={favorites.isBusy(restaurant.id)}
                  onToggleFavorite={favorites.toggle}
                />
              ))}
            </div>

            {filtered.length === 0 && (
              <div className="no-results">
                <Search size={30} />
                <h3>No restaurants found</h3>
                <p>Try a different search or dietary filter.</p>
              </div>
            )}

            {disclaimer && (
              <div className="disclaimer">
                <ShieldCheck size={18} />
                <p>{disclaimer}</p>
              </div>
            )}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}
