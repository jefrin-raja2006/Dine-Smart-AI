import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Check,
  Leaf,
  MapPin,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Wheat,
} from "lucide-react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import RestaurantCard from "../components/RestaurantCard";
import useFavorites from "../hooks/useFavorites";
import useLocation from "../hooks/useLocation";
import { getRecommendations, updatePreferences } from "../services/api";
import { getUser, updateStoredUser } from "../services/session";

const preferenceOptions = [
  { name: "Vegetarian", icon: Leaf },
  { name: "Vegan", icon: Leaf },
  { name: "Jain", icon: Sparkles },
  { name: "Gluten-Free", icon: Wheat },
  { name: "Dairy-Free", icon: Leaf },
];

export default function Home() {
  const navigate = useNavigate();
  const user = getUser();

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(user?.dietary_preferences || []);
  const [prefError, setPrefError] = useState("");

  const [picks, setPicks] = useState([]);
  const [picksLoading, setPicksLoading] = useState(true);
  const [picksError, setPicksError] = useState("");
  const [picksMessage, setPicksMessage] = useState("");

  const { location, loading: locating, error: locationError, locate } = useLocation();
  const favorites = useFavorites();
  const requestId = useRef(0);

  // ---------------------------------------------------------
  // Load AI picks whenever location or saved preferences change.
  // If location is unavailable we still show picks from saved restaurants.
  // ---------------------------------------------------------
  const preferenceKey = selected.join(",");

  useEffect(() => {
    if (locating) return;

    const current = ++requestId.current;

    getRecommendations({
      latitude: location?.latitude,
      longitude: location?.longitude,
      radius: 10000,
      limit: 6,
      preferences: preferenceKey || undefined,
    })
      .then((result) => {
        if (current !== requestId.current) return;
        setPicks(result.recommendations || []);
        setPicksMessage(result.message || "");
        setPicksError("");
      })
      .catch((err) => {
        if (current !== requestId.current) return;
        setPicksError(err.message);
      })
      .finally(() => {
        if (current === requestId.current) setPicksLoading(false);
      });
  }, [location, locating, preferenceKey]);

  // ---------------------------------------------------------
  // Preferences (saved to the server so they follow the user)
  // ---------------------------------------------------------
  const togglePreference = async (name) => {
    const previous = selected;
    const updated = selected.includes(name)
      ? selected.filter((item) => item !== name)
      : [...selected, name];

    setSelected(updated);
    setPicksLoading(true);
    setPrefError("");

    try {
      const profile = await updatePreferences(updated);
      updateStoredUser({ dietary_preferences: profile.dietary_preferences });
    } catch (err) {
      setSelected(previous);
      setPrefError(err.message);
    }
  };

  const handleSearch = (value = search) => {
    const text = value.trim();
    navigate(text ? `/restaurants?search=${encodeURIComponent(text)}` : "/restaurants");
  };

  const openPersonalizedRestaurants = () => navigate("/restaurants?mode=ai");

  const topMatch = picks[0]?.ai_match;

  return (
    <div className="app">
      <Navbar />

      <main>
        {/* HERO */}
        <section className="hero">
          <div className="hero-content">
            <div className="hero-label">
              <Sparkles size={15} />
              AI-powered food discovery
            </div>

            <h1>
              Find food
              <br />
              <span>that fits you.</span>
            </h1>

            <p>
              Discover restaurants and dishes that match your dietary preferences,
              powered by intelligent review insights.
            </p>

            <div className="search-panel">
              <div className="search-field">
                <Search size={20} />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Restaurant, dish or cuisine..."
                  aria-label="Search restaurants"
                />
              </div>

              <button
                className="location-field"
                onClick={locate}
                disabled={locating}
                title="Refresh my location"
              >
                <MapPin size={19} />
                {locating ? "Locating…" : location ? "Near you" : "Use my location"}
              </button>

              <button className="search-button" onClick={() => handleSearch()}>
                Search
                <ArrowRight size={17} />
              </button>
            </div>

            <div className="quick-text">
              Popular:
              {["South Indian", "Vegan", "Cafe"].map((term) => (
                <button key={term} onClick={() => handleSearch(term)}>
                  {term}
                </button>
              ))}
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-photo">
              <img
                src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1100&q=85"
                alt="Food"
              />

              {topMatch !== undefined && (
                <div className="match-card">
                  <div className="match-icon">
                    <Sparkles size={19} />
                  </div>
                  <div>
                    <span>YOUR TOP MATCH</span>
                    <strong>{topMatch}%</strong>
                    <small>{picks[0].name}</small>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* PREFERENCES */}
        <section className="preferences-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">PERSONALIZE</span>
              <h2>What matters to you?</h2>
            </div>
            <p>Your choices are saved to your account and shape every recommendation.</p>
          </div>

          <div className="preference-grid">
            {preferenceOptions.map(({ name, icon: Icon }) => {
              const active = selected.includes(name);

              return (
                <button
                  className={`preference-card ${active ? "active" : ""}`}
                  key={name}
                  onClick={() => togglePreference(name)}
                  aria-pressed={active}
                >
                  <span className="preference-icon">
                    <Icon size={22} />
                  </span>
                  <span className="preference-name">{name}</span>
                  <span className="check-circle">{active && <Check size={14} />}</span>
                </button>
              );
            })}
          </div>

          {prefError && <div className="inline-error">{prefError}</div>}

          {selected.length > 0 && (
            <>
              <p className="selected-text">Selected: {selected.join(", ")}</p>

              <button className="primary-button" onClick={openPersonalizedRestaurants}>
                Show personalized restaurants
                <ArrowRight size={18} />
              </button>
            </>
          )}
        </section>

        {/* AI PICKS */}
        <section className="restaurant-section" id="recommendations">
          <div className="section-heading">
            <div>
              <span className="eyebrow">PERSONALIZED FOR YOU</span>
              <h2>AI picks you might love</h2>
            </div>

            <Link className="text-button" to="/restaurants?mode=ai">
              View all
              <ArrowRight size={17} />
            </Link>
          </div>

          {picksMessage && <div className="info-banner">{picksMessage}</div>}

          {locationError && !location && (
            <div className="info-banner">
              {locationError}{" "}
              <button className="link-button" onClick={locate}>
                Try again
              </button>
            </div>
          )}

          {picksLoading && (
            <div className="loading">
              <MapPin size={20} />
              Finding restaurants that fit you…
            </div>
          )}

          {!picksLoading && picksError && <div className="error">{picksError}</div>}

          {!picksLoading && !picksError && (
            <div className="restaurant-grid">
              {picks.length > 0 ? (
                picks.map((restaurant) => (
                  <RestaurantCard
                    key={restaurant.id}
                    restaurant={restaurant}
                    isFavorite={favorites.isFavorite(restaurant.id)}
                    favoriteBusy={favorites.isBusy(restaurant.id)}
                    onToggleFavorite={favorites.toggle}
                  />
                ))
              ) : (
                <div className="no-results">
                  <Search size={30} />
                  <h3>No picks yet</h3>
                  <p>
                    Allow location access or browse nearby restaurants so we can
                    find places for you.
                  </p>
                  <button className="primary-button" onClick={() => navigate("/restaurants")}>
                    Browse nearby restaurants
                    <ArrowRight size={17} />
                  </button>
                </div>
              )}
            </div>
          )}

          {favorites.error && <div className="inline-error">{favorites.error}</div>}
        </section>

        {/* WHY DINESMART */}
        <section className="why-section" id="how-it-works">
          <div className="why-copy">
            <span className="eyebrow">WHY DINESMART AI?</span>

            <h2>
              More than a rating.
              <br />
              <span>More than a recommendation.</span>
            </h2>

            <p>
              We turn customer reviews into useful dish-level insights and combine
              them with your preferences to make food discovery more personal and
              trustworthy.
            </p>

            <button className="primary-button" onClick={openPersonalizedRestaurants}>
              Explore DineSmart AI
              <ArrowRight size={18} />
            </button>
          </div>

          <div className="insight-stack">
            {[
              [Sparkles, "Personalized recommendations", "Every match comes with the reasons behind it."],
              [Leaf, "Dietary-aware discovery", "Verified vs. likely dietary info, clearly labelled."],
              [ShieldCheck, "Review trust insights", "Spot low-information or suspicious review patterns."],
              [Star, "Dish-level sentiment", "See what customers think about individual dishes."],
            ].map(([Icon, title, text], index) => (
              <div className="insight-card" key={title}>
                <Icon />
                <div>
                  <strong>{title}</strong>
                  <p>{text}</p>
                </div>
                <span>{`0${index + 1}`}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="disclaimer">
          <ShieldCheck size={18} />
          <p>
            <strong>Responsible AI:</strong> DineSmart provides food-discovery
            insights, not medical advice or a guarantee of allergen safety. Always
            confirm ingredients with the restaurant.
          </p>
        </section>
      </main>

      <Footer />
    </div>
  );
}
