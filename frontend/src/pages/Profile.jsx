import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Heart,
  Leaf,
  Settings,
  ShieldCheck,
  Sparkles,
  Star,
  User,
  Wheat,
} from "lucide-react";

export default function Profile() {
  const preferences = [
    "Vegetarian",
    "Jain",
    "Gluten-Free",
  ];

  return (
    <div className="app">
      <header className="navbar">
        <Link className="brand" to="/">
          <span className="brand-mark">D</span>
          DineSmart <b>AI</b>
        </Link>

        <nav className="nav-links">
          <Link to="/restaurants">Discover</Link>
          <Link to="/">AI Picks</Link>
          <Link to="/profile">Profile</Link>
        </nav>

        <Link className="signup-btn" to="/">
          Home
        </Link>
      </header>

      <main className="profile-page">
        <Link to="/" className="back-to-list">
          <ArrowLeft size={17} />
          Back to home
        </Link>

        <section className="profile-header">
          <div className="profile-avatar">
            <User size={35} />
          </div>

          <div>
            <span className="eyebrow">MY PROFILE</span>
            <h1>Welcome back, Food Explorer.</h1>
            <p>
              Your preferences help DineSmart personalize your discovery.
            </p>
          </div>

          <button className="settings-button">
            <Settings size={17} />
            Settings
          </button>
        </section>

        <div className="profile-grid">
          <section className="profile-card">
            <div className="profile-card-title">
              <div>
                <span className="eyebrow">YOUR PREFERENCES</span>
                <h2>Dietary preferences</h2>
              </div>

              <Leaf size={21} />
            </div>

            <div className="profile-preferences">
              {preferences.map((item) => (
                <span key={item}>
                  <Leaf size={13} />
                  {item}
                </span>
              ))}
            </div>

            <button className="edit-button">
              Edit preferences
            </button>
          </section>

          <section className="profile-card">
            <div className="profile-card-title">
              <div>
                <span className="eyebrow">AI PROFILE</span>
                <h2>Your discovery stats</h2>
              </div>

              <Sparkles size={21} />
            </div>

            <div className="stats-grid">
              <div>
                <strong>94%</strong>
                <span>Avg. recommendation match</span>
              </div>

              <div>
                <strong>17</strong>
                <span>Restaurants explored</span>
              </div>

              <div>
                <strong>8</strong>
                <span>Favorites</span>
              </div>

              <div>
                <strong>32</strong>
                <span>Reviews analyzed</span>
              </div>
            </div>
          </section>
        </div>

        <section className="profile-card favorites-section">
          <div className="profile-card-title">
            <div>
              <span className="eyebrow">SAVED PLACES</span>
              <h2>Your favorites</h2>
            </div>

            <Heart size={21} />
          </div>

          <div className="favorite-list">
            <div className="favorite-item">
              <div className="favorite-icon">
                <Heart size={18} />
              </div>

              <div>
                <strong>Spice Garden</strong>
                <span>South Indian • 4.8 ?</span>
              </div>

              <Link to="/restaurant/1">View</Link>
            </div>

            <div className="favorite-item">
              <div className="favorite-icon">
                <Heart size={18} />
              </div>

              <div>
                <strong>Green Leaf Kitchen</strong>
                <span>Healthy • 4.7 ?</span>
              </div>

              <Link to="/restaurant/2">View</Link>
            </div>
          </div>
        </section>

        <section className="profile-ai-banner">
          <div className="profile-ai-icon">
            <Sparkles />
          </div>

          <div>
            <span>AI PERSONALIZATION</span>
            <h2>Your recommendations are getting smarter.</h2>
            <p>
              As you explore, favorite, and rate restaurants, DineSmart can
              better understand your preferences.
            </p>
          </div>

          <ShieldCheck size={25} />
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

        <span>© 2026 DineSmart AI</span>
      </footer>
    </div>
  );
}
