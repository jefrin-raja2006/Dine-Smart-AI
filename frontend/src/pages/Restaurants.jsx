import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Heart,
  MapPin,
  Search,
  ShieldCheck,
  Star,
  Navigation,
} from "lucide-react";

import { getNearbyRestaurants } from "../services/api";

export default function Restaurants() {
  const [restaurants, setRestaurants] = useState([]);
  const [search, setSearch] = useState("");
  const [diet, setDiet] = useState("All");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [location, setLocation] = useState(null);

  const getUserLocation = () => {
    setLoading(true);
    setError("");

    if (!navigator.geolocation) {
      setError(
        "Your browser does not support location."
      );
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude =
          position.coords.latitude;

        const longitude =
          position.coords.longitude;

        console.log(
          "User location:",
          latitude,
          longitude
        );

        setLocation({
          latitude,
          longitude,
        });

        try {
          const result =
            await getNearbyRestaurants(
              latitude,
              longitude,
              15000
            );

          console.log(
            "Restaurant API result:",
            result
          );

          setRestaurants(
            result.restaurants || []
          );

        } catch (err) {
          console.error(err);

          setError(
            err.message ||
              "Unable to load restaurants."
          );

        } finally {
          setLoading(false);
        }
      },

      (geoError) => {
        console.error(
          "Location error:",
          geoError
        );

        setError(
          "Unable to get your location. Please allow location access."
        );

        setLoading(false);
      },

      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 300000,
      }
    );
  };

  useEffect(() => {
    getUserLocation();
  }, []);

  const filtered =
    restaurants.filter((restaurant) => {
      const text =
        `${restaurant.name || ""} ${
          restaurant.cuisine || ""
        } ${
          restaurant.address || ""
        } ${
          restaurant.city || ""
        }`.toLowerCase();

      const matchesSearch =
        text.includes(
          search.toLowerCase()
        );

      // AI dietary filtering will be added next
      const matchesDiet =
        diet === "All";

      return (
        matchesSearch &&
        matchesDiet
      );
    });

  return (
    <div>

      {/* NAVBAR */}

      <header className="navbar">

        <Link
          className="logo"
          to="/home"
        >
          <strong>D</strong>
          <span>DineSmart AI</span>
        </Link>

        <div className="nav-actions">

          <Link
            className="login-btn"
            to="/profile"
          >
            Profile
          </Link>

        </div>

      </header>

      {/* PAGE */}

      <main className="listing-page">

        <div className="listing-heading">

          <span className="eyebrow">
            DISCOVER NEAR YOU
          </span>

          <h1>
            Find your next favorite place.
          </h1>

          <p>
            Real restaurants discovered
            around your current location.
          </p>

        </div>

        {/* LOCATION BOX */}

        <div className="location-status">

          <MapPin size={18} />

          <div>

            <strong>
              Your current location
            </strong>

            <span>

              {location
                ? `${location.latitude.toFixed(
                    4
                  )}, ${location.longitude.toFixed(
                    4
                  )}`
                : "Detecting..."}

            </span>

          </div>

          <button
            onClick={getUserLocation}
            disabled={loading}
          >

            <Navigation size={15} />

            {loading
              ? "Finding..."
              : "Refresh location"}

          </button>

        </div>

        {/* SEARCH */}

        <div className="listing-controls">

          <div className="listing-search">

            <Search size={19} />

            <input
              placeholder="Search restaurants..."
              value={search}
              onChange={(e) =>
                setSearch(e.target.value)
              }
            />

          </div>

          {[
            "All",
            "Vegetarian",
            "Vegan",
            "Jain",
            "Gluten-Free",
          ].map((item) => (

            <button
              key={item}
              className={
                diet === item
                  ? "filter active"
                  : "filter"
              }
              onClick={() =>
                setDiet(item)
              }
            >
              {item}
            </button>

          ))}

        </div>

        {/* LOADING */}

        {loading && (

          <div className="loading">

            <MapPin size={20} />

            Finding restaurants near you...

          </div>

        )}

        {/* ERROR */}

        {!loading && error && (

          <div className="error">
            {error}
          </div>

        )}

        {/* RESTAURANTS */}

        {!loading &&
          !error && (

            <>

              <div className="nearby-count">

                <strong>
                  {filtered.length}
                </strong>

                {" "}real restaurants found

              </div>

              <div className="restaurant-grid">

                {filtered.map(
                  (restaurant) => (

                    <article
                      className="restaurant-card"
                      key={
                        restaurant.osm_id
                      }
                    >

                      {/* IMAGE */}

                      <div className="restaurant-image">

                        <img
                          src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80"
                          alt={
                            restaurant.name
                          }
                        />

                        <button
                          className="favorite-button"
                          onClick={() =>
                            alert(
                              "Favorites will be connected next."
                            )
                          }
                        >

                          <Heart size={18} />

                        </button>

                      </div>

                      {/* DETAILS */}

                      <div className="restaurant-body">

                        <div className="restaurant-title-row">

                          <h3>
                            {
                              restaurant.name
                            }
                          </h3>

                          <span className="rating">

                            <Star
                              size={14}
                            />

                            N/A

                          </span>

                        </div>

                        <p className="cuisine">

                          {
                            restaurant.cuisine ||
                            "Restaurant"
                          }

                        </p>

                        <div className="tags">

                          <span>
                            {
                              restaurant.amenity ||
                              "Restaurant"
                            }
                          </span>

                          <span>
                            OpenStreetMap
                          </span>

                        </div>

                        <div className="location-row">

                          <MapPin
                            size={14}
                          />

                          {restaurant.address ||
                            restaurant.city ||
                            restaurant.street ||
                            "Nearby"}

                        </div>

                        {restaurant.phone && (

                          <div className="location-row">

                            📞

                            {restaurant.phone}

                          </div>

                        )}

                        <div className="trust-row">

                          <ShieldCheck
                            size={16}
                          />

                          Real location data

                        </div>

                        {restaurant.website && (

                          <a
                            className="details-link"
                            href={
                              restaurant.website
                            }
                            target="_blank"
                            rel="noreferrer"
                          >
                            Visit website →
                          </a>

                        )}

                      </div>

                    </article>

                  )
                )}

              </div>

              {filtered.length === 0 && (

                <div className="no-results">

                  No restaurants found.

                </div>

              )}

            </>

          )}

      </main>

    </div>
  );
}