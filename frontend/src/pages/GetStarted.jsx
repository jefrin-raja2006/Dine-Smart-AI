import { Link } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";

export default function GetStarted() {
  return (
    <div className="get-started-page">

      <header className="get-started-nav">
        <div className="brand">
          <span className="brand-mark">D</span>
          DineSmart <b>AI</b>
        </div>

        
      </header>

      <main className="get-started-content">

        <div className="get-started-text">

          <span className="auth-label">
            <Sparkles size={15} />
            AI-POWERED FOOD DISCOVERY
          </span>

          <h1>
            Food that
            <br />
            <span>fits you.</span>
          </h1>

          <p>
            Discover restaurants and dishes based on your dietary
            preferences, allergies, reviews and personal taste.
          </p>

          <Link to="/login" className="get-started-btn">
            Get Started
            <ArrowRight size={19} />
          </Link>

          <p className="existing-account">
            Already have an account?{" "}
            <Link to="/login">Sign in</Link>
          </p>

        </div>

        <div className="get-started-image">
          <img
            src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85"
            alt="Delicious food"
          />

          <div className="get-started-card">
            <span>AI MATCH</span>
            <strong>94%</strong>
            <small>Great fit for your preferences</small>
          </div>
        </div>

      </main>

    </div>
  );
}
