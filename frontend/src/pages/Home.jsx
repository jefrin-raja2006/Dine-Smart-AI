import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Heart,
  Leaf,
  LogOut,
  MapPin,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Wheat,
  User,
} from "lucide-react";

const preferences = [
  { name: "Vegetarian", icon: Leaf },
  { name: "Vegan", icon: Leaf },
  { name: "Jain", icon: Sparkles },
  { name: "Gluten-Free", icon: Wheat },
];

const restaurants = [
  {
    id: 1,
    name: "Spice Garden",
    cuisine: "South Indian • Vegetarian",
    location: "Chennai",
    rating: 4.8,
    match: 94,
    dish: "Biryani",
    sentiment: 91,
    image:
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 2,
    name: "Green Leaf Kitchen",
    cuisine: "Healthy • Vegan",
    location: "Chennai",
    rating: 4.7,
    match: 91,
    dish: "Buddha Bowl",
    sentiment: 89,
    image:
      "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 3,
    name: "The Curry House",
    cuisine: "Indian • Jain Options",
    location: "Chennai",
    rating: 4.6,
    match: 88,
    dish: "Dosa",
    sentiment: 88,
    image:
      "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=900&q=80",
  },
];

export default function Home() {
  const navigate = useNavigate();

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState([]);
  const [favorites, setFavorites] = useState([]);

  const user = JSON.parse(localStorage.getItem("user") || "null");

  const togglePreference = (name) => {
    setSelected((current) =>
      current.includes(name)
        ? current.filter((item) => item !== name)
        : [...current, name]
    );
  };

  const toggleFavorite = (id) => {
    setFavorites((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };

  const filteredRestaurants = restaurants.filter((restaurant) =>
    `${restaurant.name} ${restaurant.cuisine}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="app">
      <header className="navbar">
        <Link className="brand" to="/home">
          <span className="brand-mark">D</span>
          DineSmart <b>AI</b>
        </Link>

        <nav className="nav-links">
          <Link to="/restaurants">Discover</Link>
          <a href="#recommendations">AI Picks</a>
          <a href="#how-it-works">How it works</a>
        </nav>

        <div className="user-actions">
          <Link to="/profile" className="user-profile">
            <span className="user-icon">
              <User size={17} />
            </span>
            <span>{user?.name || "User"}</span>
          </Link>

          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      <main>
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
              Discover restaurants and dishes that match your dietary
              preferences, powered by intelligent review insights.
            </p>

            <div className="search-panel">
              <div className="search-field">
                <Search size={20} />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Restaurant, dish or cuisine..."
                />
              </div>

              <div className="location-field">
                <MapPin size={19} />
                Chennai
                <ChevronDown size={16} />
              </div>

              <Link className="search-button" to="/restaurants">
                Search
                <ArrowRight size={17} />
              </Link>
            </div>

            <div className="quick-text">
              Popular:
              <button onClick={() => setSearch("South Indian")}>
                South Indian
              </button>
              <button onClick={() => setSearch("Vegan")}>Vegan</button>
              <button onClick={() => setSearch("Indian")}>Indian</button>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-photo">
              <img
                src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1100&q=85"
                alt="Food"
              />

              <div className="match-card">
                <div className="match-icon">
                  <Sparkles size={19} />
                </div>

                <div>
                  <span>AI MATCH</span>
                  <strong>94%</strong>
                  <small>Great fit for your preferences</small>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="preferences-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">PERSONALIZE</span>
              <h2>What matters to you?</h2>
            </div>

            <p>
              Select your dietary preferences to improve your recommendations.
            </p>
          </div>

          <div className="preference-grid">
            {preferences.map(({ name, icon: Icon }) => {
              const active = selected.includes(name);

              return (
                <button
                  className={`preference-card ${active ? "active" : ""}`}
                  key={name}
                  onClick={() => togglePreference(name)}
                >
                  <span className="preference-icon">
                    <Icon size={22} />
                  </span>

                  <span className="preference-name">{name}</span>

                  <span className="check-circle">
                    {active && <Check size={14} />}
                  </span>
                </button>
              );
            })}
          </div>

          {selected.length > 0 && (
            <p className="selected-text">
              Selected: {selected.join(", ")}
            </p>
          )}
        </section>

        <section className="restaurant-section" id="recommendations">
          <div className="section-heading">
            <div>
              <span className="eyebrow">PERSONALIZED FOR YOU</span>
              <h2>AI picks you might love</h2>
            </div>

            <Link className="text-button" to="/restaurants">
              View all
              <ArrowRight size={17} />
            </Link>
          </div>

          <div className="restaurant-grid">
            {filteredRestaurants.map((restaurant) => (
              <article className="restaurant-card" key={restaurant.id}>
                <div className="restaurant-image">
                  <img src={restaurant.image} alt={restaurant.name} />

                  <button
                    className={`favorite-button ${
                      favorites.includes(restaurant.id) ? "liked" : ""
                    }`}
                    onClick={() => toggleFavorite(restaurant.id)}
                  >
                    <Heart
                      size={18}
                      fill={
                        favorites.includes(restaurant.id)
                          ? "currentColor"
                          : "none"
                      }
                    />
                  </button>

                  <span className="ai-match">
                    <Sparkles size={12} />
                    {restaurant.match}% MATCH
                  </span>
                </div>

                <div className="restaurant-body">
                  <div className="restaurant-title-row">
                    <h3>{restaurant.name}</h3>

                    <span className="rating">
                      <Star size={14} fill="currentColor" />
                      {restaurant.rating}
                    </span>
                  </div>

                  <p className="cuisine">{restaurant.cuisine}</p>

                  <div className="location-row">
                    <MapPin size={14} />
                    {restaurant.location}
                  </div>

                  <div className="dish-insight">
                    <div>
                      <span>AI DISH INSIGHT</span>
                      <strong>{restaurant.dish}</strong>
                    </div>

                    <div className="sentiment">
                      <span>Positive</span>
                      <strong>{restaurant.sentiment}%</strong>
                    </div>
                  </div>

                  <div className="trust-row">
                    <ShieldCheck size={16} />
                    Review trust: High
                  </div>

                  <Link
                    className="details-link"
                    to={`/restaurant/${restaurant.id}`}
                  >
                    View restaurant
                    <ArrowRight size={15} />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="why-section" id="how-it-works">
          <div className="why-copy">
            <span className="eyebrow">WHY DINESMART AI?</span>

            <h2>
              More than a rating.
              <br />
              <span>More than a recommendation.</span>
            </h2>

            <p>
              We turn customer reviews into useful dish-level insights and
              combine them with your preferences to make food discovery more
              personal and trustworthy.
            </p>

            <Link className="primary-button" to="/restaurants">
              Explore DineSmart AI
              <ArrowRight size={18} />
            </Link>
          </div>

          <div className="insight-stack">
            <div className="insight-card">
              <Sparkles />
              <div>
                <strong>Personalized recommendations</strong>
                <p>Recommendations based on your preferences.</p>
              </div>
              <span>01</span>
            </div>

            <div className="insight-card">
              <Leaf />
              <div>
                <strong>Dietary-aware discovery</strong>
                <p>Find food matching your selected preferences.</p>
              </div>
              <span>02</span>
            </div>

            <div className="insight-card">
              <ShieldCheck />
              <div>
                <strong>Review trust insights</strong>
                <p>Identify potentially suspicious review patterns.</p>
              </div>
              <span>03</span>
            </div>

            <div className="insight-card">
              <Star />
              <div>
                <strong>Dish-level sentiment</strong>
                <p>See what customers think about individual dishes.</p>
              </div>
              <span>04</span>
            </div>
          </div>
        </section>

        <section className="disclaimer">
          <ShieldCheck size={18} />
          <p>
            <strong>Responsible AI:</strong> DineSmart provides food-discovery
            insights, not medical advice or a guarantee of allergen safety.
          </p>
        </section>
      </main>

      <footer className="footer">
        <div className="footer-brand">
          <span className="brand-mark">D</span>
          <div>
            <strong>DineSmart AI</strong>
            <span>Find food that fits you.</span>
          </div>
        </div>

        <div className="footer-links">
          <Link to="/restaurants">Discover</Link>
          <Link to="/profile">Profile</Link>
          <button onClick={handleLogout}>Logout</button>
        </div>

        <span>© 2026 DineSmart AI</span>
      </footer>
    </div>
  );
}
