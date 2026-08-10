import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Heart,
  MapPin,
  ShieldCheck,
  Sparkles,
  Star,
  ThumbsUp,
  AlertTriangle,
  Leaf,
} from "lucide-react";

const data = {
  1: {
    name: "Spice Garden",
    cuisine: "South Indian • Vegetarian",
    location: "Chennai",
    rating: 4.8,
    reviews: 328,
    image:
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1400&q=85",
    tags: ["Vegetarian", "Jain Options"],
    dishes: [
      { name: "Biryani", score: 91, reviews: 124 },
      { name: "Dosa", score: 88, reviews: 97 },
      { name: "Paneer Curry", score: 84, reviews: 76 },
    ],
  },
  2: {
    name: "Green Leaf Kitchen",
    cuisine: "Healthy • Vegan",
    location: "Chennai",
    rating: 4.7,
    reviews: 241,
    image:
      "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1400&q=85",
    tags: ["Vegan", "Gluten-Free"],
    dishes: [
      { name: "Buddha Bowl", score: 89, reviews: 91 },
      { name: "Avocado Salad", score: 87, reviews: 73 },
      { name: "Vegan Wrap", score: 82, reviews: 51 },
    ],
  },
  3: {
    name: "The Curry House",
    cuisine: "Indian • Jain Options",
    location: "Chennai",
    rating: 4.6,
    reviews: 186,
    image:
      "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1400&q=85",
    tags: ["Jain", "Vegetarian"],
    dishes: [
      { name: "Dosa", score: 88, reviews: 82 },
      { name: "Paneer Tikka", score: 85, reviews: 64 },
      { name: "Veg Thali", score: 81, reviews: 42 },
    ],
  },
};

const reviews = [
  {
    name: "Arun",
    rating: 5,
    text: "The biryani was excellent and the service was really good.",
    dish: "Biryani",
    sentiment: "Positive",
    trust: "High",
  },
  {
    name: "Priya",
    rating: 4,
    text: "Loved the dosa. Crispy and fresh. Would definitely order again.",
    dish: "Dosa",
    sentiment: "Positive",
    trust: "High",
  },
  {
    name: "Rahul",
    rating: 2,
    text: "The food was okay but the service was very slow.",
    dish: "Service",
    sentiment: "Mixed",
    trust: "Medium",
  },
];

export default function RestaurantDetails() {
  const { id } = useParams();
  const restaurant = data[id] || data[1];
  const [favorite, setFavorite] = useState(false);

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

        <div className="nav-actions">
          <Link className="login-btn" to="/login">
            Log in
          </Link>
          <Link className="signup-btn" to="/register">
            Get Started
          </Link>
        </div>
      </header>

      <main className="details-page">
        <Link to="/restaurants" className="back-to-list">
          <ArrowLeft size={17} />
          Back to restaurants
        </Link>

        <section className="details-hero">
          <img src={restaurant.image} alt={restaurant.name} />

          <button
            className={`details-favorite ${favorite ? "liked" : ""}`}
            onClick={() => setFavorite(!favorite)}
          >
            <Heart
              size={20}
              fill={favorite ? "currentColor" : "none"}
            />
          </button>
        </section>

        <section className="details-header">
          <div>
            <span className="eyebrow">AI-ANALYZED RESTAURANT</span>

            <h1>{restaurant.name}</h1>

            <p className="details-cuisine">{restaurant.cuisine}</p>

            <div className="details-meta">
              <span>
                <MapPin size={15} />
                {restaurant.location}
              </span>

              <span className="details-rating">
                <Star size={15} fill="currentColor" />
                {restaurant.rating}
              </span>

              <span>{restaurant.reviews} reviews</span>
            </div>

            <div className="details-tags">
              {restaurant.tags.map((tag) => (
                <span key={tag}>
                  <Leaf size={13} />
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="ai-match-large">
            <Sparkles size={19} />
            <span>AI MATCH</span>
            <strong>94%</strong>
            <small>Based on your preferences</small>
          </div>
        </section>

        <section className="ai-insights-section">
          <div className="details-section-title">
            <span className="eyebrow">AI INSIGHTS</span>
            <h2>What customers actually think</h2>
            <p>
              Our AI analyzes customer reviews to identify dish-level
              sentiment and review trust patterns.
            </p>
          </div>

          <div className="insight-summary">
            <div className="summary-card">
              <Sparkles />
              <span>Overall sentiment</span>
              <strong>87%</strong>
              <small>Positive</small>
            </div>

            <div className="summary-card">
              <ShieldCheck />
              <span>Review trust</span>
              <strong>92%</strong>
              <small>High confidence</small>
            </div>

            <div className="summary-card">
              <Star />
              <span>Best rated dish</span>
              <strong>{restaurant.dishes[0].name}</strong>
              <small>{restaurant.dishes[0].score}% positive</small>
            </div>
          </div>
        </section>

        <section className="dish-section">
          <div className="details-section-title">
            <span className="eyebrow">DISH-LEVEL SENTIMENT</span>
            <h2>What should you order?</h2>
          </div>

          <div className="dish-list">
            {restaurant.dishes.map((dish, index) => (
              <div className="dish-card" key={dish.name}>
                <div className="dish-rank">0{index + 1}</div>

                <div className="dish-info">
                  <h3>{dish.name}</h3>
                  <span>{dish.reviews} customer reviews analyzed</span>
                </div>

                <div className="sentiment-bar">
                  <div>
                    <span>Positive sentiment</span>
                    <strong>{dish.score}%</strong>
                  </div>

                  <div className="progress">
                    <span style={{ width: `${dish.score}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="trust-section">
          <div className="trust-header">
            <div>
              <span className="eyebrow">REVIEW TRUST ANALYSIS</span>
              <h2>Can you trust the reviews?</h2>
            </div>

            <div className="trust-score">
              <ShieldCheck size={20} />
              <strong>92%</strong>
              <span>High trust</span>
            </div>
          </div>

          <div className="trust-warning">
            <AlertTriangle size={19} />

            <div>
              <strong>AI-assisted review analysis</strong>
              <p>
                The system identifies potentially suspicious patterns. It
                does not claim that a review is definitely fake or fraudulent.
              </p>
            </div>
          </div>
        </section>

        <section className="reviews-section">
          <div className="details-section-title">
            <span className="eyebrow">CUSTOMER REVIEWS</span>
            <h2>Recent reviews</h2>
          </div>

          <div className="review-list">
            {reviews.map((review, index) => (
              <article className="review-card" key={index}>
                <div className="review-top">
                  <div className="review-user">
                    <div className="avatar">
                      {review.name[0]}
                    </div>

                    <div>
                      <strong>{review.name}</strong>

                      <div className="review-stars">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            size={12}
                            fill={star <= review.rating ? "currentColor" : "none"}
                          />
                        ))}
                      </div>
                    </div>
                  </div>

                  <span className="review-trust">
                    <ShieldCheck size={13} />
                    {review.trust} trust
                  </span>
                </div>

                <p>"{review.text}"</p>

                <div className="review-analysis">
                  <span>
                    <Sparkles size={12} />
                    Dish: {review.dish}
                  </span>

                  <span className="positive">
                    Sentiment: {review.sentiment}
                  </span>
                </div>

                <button className="helpful-button">
                  <ThumbsUp size={13} />
                  Helpful
                </button>
              </article>
            ))}
          </div>
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
