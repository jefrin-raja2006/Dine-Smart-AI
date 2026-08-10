import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Heart, MapPin, Search, ShieldCheck, Star } from "lucide-react";
import { getRestaurants } from "../services/api";

export default function Restaurants() {
  const [restaurants, setRestaurants] = useState([]);
  const [search, setSearch] = useState("");
  const [diet, setDiet] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getRestaurants()
      .then((data) => {
        setRestaurants(data);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load restaurants.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const filtered = restaurants.filter((restaurant) => {
    const matchesSearch =
      `${restaurant.name} ${restaurant.cuisine}`
        .toLowerCase()
        .includes(search.toLowerCase());

    // Dietary tags will be added from the database later.
    // For now, "All" shows every restaurant.
    const matchesDiet = diet === "All";

    return matchesSearch && matchesDiet;
  });

  return (
    <div>
      <header className="navbar">
        <Link className="logo" to="/">
          <strong>D</strong>
          <span>DineSmart AI</span>
        </Link>

        <div className="nav-actions">
          <Link className="login-btn" to="/login">
            Log in
          </Link>

          <Link className="signup-btn" to="/register">
            Get Started
          </Link>
        </div>
      </header>

      <main className="listing-page">
        <div className="listing-heading">
          <span className="eyebrow">DISCOVER</span>

          <h1>Find your next favorite place.</h1>

          <p>
            Search restaurants and filter them according to your dietary
            preferences.
          </p>
        </div>

        <div className="listing-controls">
          <div className="listing-search">
            <Search size={19} />

            <input
              placeholder="Search restaurants or cuisine..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {["All", "Vegetarian", "Vegan", "Jain", "Gluten-Free"].map(
            (item) => (
              <button
                key={item}
                className={diet === item ? "filter active" : "filter"}
                onClick={() => setDiet(item)}
              >
                {item}
              </button>
            )
          )}
        </div>

        {loading && (
          <div className="loading">
            Loading restaurants...
          </div>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="restaurant-grid">
            {filtered.map((restaurant) => (
              <article
                className="restaurant-card"
                key={restaurant.id}
              >
                <div className="restaurant-image">
                  <img
                    src={
                      restaurant.image_url ||
                      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80"
                    }
                    alt={restaurant.name}
                  />

                  <button className="favorite-button">
                    <Heart size={18} />
                  </button>
                </div>

                <div className="restaurant-body">
                  <div className="restaurant-title-row">
                    <h3>{restaurant.name}</h3>

                    <span className="rating">
                      <Star size={14} fill="currentColor" />
                      {restaurant.rating}
                    </span>
                  </div>

                  <p className="cuisine">
                    {restaurant.cuisine}
                  </p>

                  <div className="tags">
                    <span>AI Verified</span>
                  </div>

                  <div className="location-row">
                    <MapPin size={14} />
                    {restaurant.location}
                  </div>

                  <div className="trust-row">
                    <ShieldCheck size={16} />
                    Review trust: High
                  </div>

                  <Link
                    className="details-link"
                    to={`/restaurant/${restaurant.id}`}
                  >
                    View details ?
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="no-results">
            No restaurants found.
          </div>
        )}
      </main>
    </div>
  );
}
