import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Clock,
  ExternalLink,
  Globe,
  Heart,
  Leaf,
  MapPin,
  Navigation,
  Phone,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
} from "lucide-react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import useFavorites from "../hooks/useFavorites";
import {
  deleteMyReview,
  getInsights,
  getRestaurant,
  getReviews,
  submitReview,
} from "../services/api";
import { capitalize, formatDate, formatDistance, placeholderImage } from "../utils/format";

const LEVEL_LABEL = {
  verified: "Verified",
  likely: "Likely (inferred)",
  unknown: "No information",
  unlikely: "Unlikely",
};

function StarInput({ value, onChange }) {
  return (
    <div className="star-input" role="radiogroup" aria-label="Your rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          type="button"
          key={star}
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star > 1 ? "s" : ""}`}
          className={star <= value ? "on" : ""}
          onClick={() => onChange(star)}
        >
          <Star size={26} fill={star <= value ? "currentColor" : "none"} />
        </button>
      ))}
    </div>
  );
}

function ReviewForm({ restaurantId, existing, onSaved }) {
  const [rating, setRating] = useState(existing?.rating || 0);
  const [text, setText] = useState(existing?.text || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!rating) return setError("Please choose a star rating.");
    if (text.trim().length < 5) return setError("Please write at least a few words.");

    setSaving(true);
    try {
      await submitReview(restaurantId, rating, text.trim());
      await onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <h3>{existing ? "Update your review" : "Share your experience"}</h3>
      <p>
        Mention specific dishes and what you liked or didn't - our AI turns it into
        dish-level insights for other diners.
      </p>

      <StarInput value={rating} onChange={setRating} />

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. The dosa was crisp and fresh, but the service was slow…"
        maxLength={2000}
        rows={4}
        aria-label="Your review"
      />

      <div className="review-form-footer">
        <span>{text.length}/2000</span>
        <button className="primary-button" type="submit" disabled={saving}>
          {saving ? "Analysing…" : existing ? "Update review" : "Post review"}
        </button>
      </div>

      {error && <div className="inline-error">{error}</div>}
    </form>
  );
}

export default function RestaurantDetails() {
  const { id } = useParams();
  const favorites = useFavorites();

  const [restaurant, setRestaurant] = useState(null);
  const [insights, setInsights] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showTrustFor, setShowTrustFor] = useState(null);

  const loadAll = useCallback(async () => {
    let location;
    try {
      location = JSON.parse(sessionStorage.getItem("lastLocation") || "null");
    } catch {
      location = null;
    }

    const [details, insightData, reviewData] = await Promise.all([
      getRestaurant(id, location),
      getInsights(id),
      getReviews(id, { limit: 50 }),
    ]);

    setRestaurant(details);
    setInsights(insightData);
    setReviews(reviewData.reviews || []);
  }, [id]);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError("");

    loadAll()
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [loadAll]);

  const myReview = reviews.find((review) => review.is_mine);

  const handleDelete = async () => {
    if (!window.confirm("Delete your review?")) return;
    try {
      await deleteMyReview(id);
      await loadAll();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <Navbar />
        <main className="details-page">
          <div className="loading">
            <MapPin size={20} />
            Loading restaurant…
          </div>
        </main>
      </div>
    );
  }

  if (error || !restaurant) {
    return (
      <div className="app">
        <Navbar />
        <main className="details-page">
          <Link to="/restaurants" className="back-to-list">
            <ArrowLeft size={17} />
            Back to restaurants
          </Link>
          <div className="error">{error || "Restaurant not found."}</div>
        </main>
      </div>
    );
  }

  const isFavorite = favorites.isFavorite(restaurant.id);
  const hasReviews = insights?.review_count > 0;
  const distance = formatDistance(restaurant.distance_km);
  const mapUrl =
    restaurant.latitude != null
      ? `https://www.openstreetmap.org/?mlat=${restaurant.latitude}&mlon=${restaurant.longitude}#map=18/${restaurant.latitude}/${restaurant.longitude}`
      : null;
  const directionsUrl =
    restaurant.latitude != null
      ? `https://www.openstreetmap.org/directions?to=${restaurant.latitude}%2C${restaurant.longitude}`
      : null;

  return (
    <div className="app">
      <Navbar />

      <main className="details-page">
        <Link to="/restaurants" className="back-to-list">
          <ArrowLeft size={17} />
          Back to restaurants
        </Link>

        <section className="details-hero">
          <img src={placeholderImage(restaurant)} alt={restaurant.name} />

          <button
            className={`details-favorite ${isFavorite ? "liked" : ""}`}
            onClick={() => favorites.toggle(restaurant)}
            disabled={favorites.isBusy(restaurant.id)}
            aria-pressed={isFavorite}
            aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
          >
            <Heart size={20} fill={isFavorite ? "currentColor" : "none"} />
          </button>
        </section>

        {favorites.error && <div className="inline-error">{favorites.error}</div>}

        <section className="details-header">
          <div>
            <span className="eyebrow">AI-ANALYZED RESTAURANT</span>

            <h1>{restaurant.name}</h1>
            <p className="details-cuisine">{restaurant.cuisine}</p>

            <div className="details-meta">
              <span>
                <MapPin size={15} />
                {restaurant.address || "Address not listed"}
              </span>

              <span className="details-rating">
                <Star size={15} fill={hasReviews ? "currentColor" : "none"} />
                {hasReviews ? restaurant.rating.toFixed(1) : "No rating yet"}
              </span>

              <span>
                {restaurant.review_count} review{restaurant.review_count === 1 ? "" : "s"}
              </span>

              {distance && <span>{distance} away</span>}
            </div>

            <div className="details-tags">
              {restaurant.diet_tags?.map((tag) => (
                <span key={tag.name} className={`diet-tag ${tag.level}`} title={tag.note}>
                  <Leaf size={13} />
                  {tag.name}
                  {tag.level === "likely" ? " · likely" : ""}
                </span>
              ))}
            </div>

            <div className="details-actions">
              {directionsUrl && (
                <a className="action-link" href={directionsUrl} target="_blank" rel="noreferrer">
                  <Navigation size={15} />
                  Directions
                </a>
              )}
              {mapUrl && (
                <a className="action-link" href={mapUrl} target="_blank" rel="noreferrer">
                  <MapPin size={15} />
                  View on map
                </a>
              )}
              {restaurant.website && (
                <a className="action-link" href={restaurant.website} target="_blank" rel="noreferrer">
                  <Globe size={15} />
                  Website
                  <ExternalLink size={12} />
                </a>
              )}
              {restaurant.phone && (
                <a className="action-link" href={`tel:${restaurant.phone}`}>
                  <Phone size={15} />
                  {restaurant.phone}
                </a>
              )}
            </div>

            {restaurant.opening_hours && (
              <p className="opening-hours">
                <Clock size={14} />
                {restaurant.opening_hours}
              </p>
            )}
          </div>

          {restaurant.ai_match !== undefined && (
            <div className="ai-match-large">
              <Sparkles size={19} />
              <span>AI MATCH</span>
              <strong>{restaurant.ai_match}%</strong>
              <small>Based on your preferences</small>

              {restaurant.match_reasons?.length > 0 && (
                <ul className="match-reasons">
                  {restaurant.match_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </section>

        {restaurant.note && (
          <div className="trust-warning">
            <AlertTriangle size={19} />
            <div>
              <strong>Please double-check</strong>
              <p>{restaurant.note}</p>
            </div>
          </div>
        )}

        {/* DIETARY EVIDENCE */}
        <section className="diet-evidence">
          <div className="details-section-title">
            <span className="eyebrow">DIETARY INFORMATION</span>
            <h2>Does it suit your diet?</h2>
          </div>

          <div className="diet-evidence-grid">
            {restaurant.diet_evidence?.map((item) => (
              <div key={item.name} className={`evidence-card ${item.level}`}>
                <strong>{item.name}</strong>
                <span>{LEVEL_LABEL[item.level]}</span>
                <small>{item.note}</small>
              </div>
            ))}
          </div>

          <p className="evidence-footnote">
            "Verified" comes from OpenStreetMap tags or menu data; "likely" is inferred
            from the cuisine or name. This is not a guarantee of allergen safety -
            always confirm with the restaurant.
          </p>
        </section>

        {/* MENU (only when the restaurant has menu data) */}
        {restaurant.menu_items?.length > 0 && (
          <section className="menu-section">
            <div className="details-section-title">
              <span className="eyebrow">MENU</span>
              <h2>What they serve</h2>
            </div>

            <div className="menu-list">
              {restaurant.menu_items.map((item) => (
                <div className="menu-item" key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    {item.description && <p>{item.description}</p>}
                    <div className="menu-flags">
                      {item.is_vegetarian && <span>Vegetarian</span>}
                      {item.is_vegan && <span>Vegan</span>}
                      {item.is_jain && <span>Jain</span>}
                      {item.is_gluten_free && <span>Gluten-Free</span>}
                    </div>
                  </div>
                  {item.price != null && <b>₹{item.price}</b>}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* AI INSIGHTS */}
        <section className="ai-insights-section">
          <div className="details-section-title">
            <span className="eyebrow">AI INSIGHTS</span>
            <h2>What customers actually think</h2>
            <p>
              Our AI analyses customer reviews to identify dish-level sentiment and
              review trust patterns.
            </p>
          </div>

          {!hasReviews ? (
            <div className="empty-insights">
              <Sparkles size={22} />
              <p>{insights?.message}</p>
            </div>
          ) : (
            <>
              {insights.message && <div className="info-banner">{insights.message}</div>}

              <div className="insight-summary">
                <div className="summary-card">
                  <Sparkles />
                  <span>Overall sentiment</span>
                  <strong>{insights.sentiment.positive_pct}%</strong>
                  <small>Positive · {capitalize(insights.sentiment.label)}</small>
                </div>

                <div className="summary-card">
                  <ShieldCheck />
                  <span>Review trust</span>
                  <strong>{insights.trust.score}%</strong>
                  <small>{capitalize(insights.trust.label)} confidence</small>
                </div>

                <div className="summary-card">
                  <Star />
                  <span>Best rated dish</span>
                  <strong>{insights.best_dish ? capitalize(insights.best_dish.name) : "—"}</strong>
                  <small>
                    {insights.best_dish
                      ? `${insights.best_dish.positive_pct}% positive`
                      : "Not enough dish mentions yet"}
                  </small>
                </div>
              </div>
            </>
          )}
        </section>

        {insights?.dishes?.length > 0 && (
          <section className="dish-section">
            <div className="details-section-title">
              <span className="eyebrow">DISH-LEVEL SENTIMENT</span>
              <h2>What should you order?</h2>
            </div>

            <div className="dish-list">
              {insights.dishes.slice(0, 8).map((dish, index) => (
                <div className="dish-card" key={dish.name}>
                  <div className="dish-rank">{String(index + 1).padStart(2, "0")}</div>

                  <div className="dish-info">
                    <h3>{capitalize(dish.name)}</h3>
                    <span>
                      Mentioned in {dish.mentions} review{dish.mentions === 1 ? "" : "s"}
                      {dish.mentions < 2 ? " (early signal)" : ""}
                    </span>
                  </div>

                  <div className="sentiment-bar">
                    <div>
                      <span>Positive sentiment</span>
                      <strong>{dish.positive_pct === null ? "—" : `${dish.positive_pct}%`}</strong>
                    </div>

                    <div className="progress">
                      <span style={{ width: `${dish.positive_pct ?? 0}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {insights.aspects.length > 0 && (
              <div className="aspect-chips">
                {insights.aspects.map((aspect) => (
                  <span key={aspect.name} className={`aspect-chip ${aspect.label}`}>
                    {capitalize(aspect.name)}: {aspect.label}
                  </span>
                ))}
              </div>
            )}
          </section>
        )}

        {/* TRUST */}
        <section className="trust-section">
          <div className="trust-header">
            <div>
              <span className="eyebrow">REVIEW TRUST ANALYSIS</span>
              <h2>Can you trust the reviews?</h2>
            </div>

            {hasReviews && (
              <div className="trust-score">
                <ShieldCheck size={20} />
                <strong>{insights.trust.score}%</strong>
                <span>{capitalize(insights.trust.label)} trust</span>
              </div>
            )}
          </div>

          <div className="trust-warning">
            <AlertTriangle size={19} />
            <div>
              <strong>AI-assisted review analysis</strong>
              <p>
                The system flags patterns common in low-information or promotional
                reviews. It does not claim that a review is definitely fake, and
                lower-trust reviews simply count for less in the insights above.
              </p>
            </div>
          </div>
        </section>

        {/* REVIEWS */}
        <section className="reviews-section">
          <div className="details-section-title">
            <span className="eyebrow">CUSTOMER REVIEWS</span>
            <h2>Recent reviews</h2>
          </div>

          <ReviewForm
            key={myReview ? `edit-${myReview.id}-${myReview.created_at}` : "new"}
            restaurantId={restaurant.id}
            existing={myReview}
            onSaved={loadAll}
          />

          <div className="review-list">
            {reviews.length === 0 && (
              <div className="no-results">
                <p>No reviews yet - be the first to review {restaurant.name}.</p>
              </div>
            )}

            {reviews.map((review) => (
              <article className="review-card" key={review.id}>
                <div className="review-top">
                  <div className="review-user">
                    <div className="avatar">{review.user_name?.[0]?.toUpperCase()}</div>

                    <div>
                      <strong>
                        {review.user_name}
                        {review.is_mine && <em className="mine-badge">You</em>}
                      </strong>

                      <div className="review-stars" aria-label={`${review.rating} out of 5 stars`}>
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            size={12}
                            fill={star <= review.rating ? "currentColor" : "none"}
                          />
                        ))}
                        <small>{formatDate(review.created_at)}</small>
                      </div>
                    </div>
                  </div>

                  <button
                    className={`review-trust trust-${review.trust_label}`}
                    onClick={() => setShowTrustFor(showTrustFor === review.id ? null : review.id)}
                    aria-expanded={showTrustFor === review.id}
                  >
                    <ShieldCheck size={13} />
                    {capitalize(review.trust_label)} trust
                  </button>
                </div>

                <p>"{review.text}"</p>

                <div className="review-analysis">
                  {review.mentions
                    ?.filter((m) => m.kind === "dish")
                    .slice(0, 3)
                    .map((m) => (
                      <span key={m.name} className={m.label}>
                        <Sparkles size={12} />
                        {capitalize(m.name)}: {m.label}
                      </span>
                    ))}

                  <span className={review.sentiment}>
                    Sentiment: {capitalize(review.sentiment)}
                  </span>
                </div>

                {showTrustFor === review.id && (
                  <div className="trust-explain">
                    <strong>Why this trust level?</strong>
                    <ul>
                      {review.trust_strengths?.map((s) => (
                        <li key={s} className="plus">{s}</li>
                      ))}
                      {review.trust_reasons?.map((r) => (
                        <li key={r} className="minus">{r}</li>
                      ))}
                      {!review.trust_strengths?.length && !review.trust_reasons?.length && (
                        <li>No notable signals.</li>
                      )}
                    </ul>
                  </div>
                )}

                {review.is_mine && (
                  <button className="helpful-button danger" onClick={handleDelete}>
                    <Trash2 size={13} />
                    Delete my review
                  </button>
                )}
              </article>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
