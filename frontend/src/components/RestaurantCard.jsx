import { Link } from "react-router-dom";
import {
  ArrowRight,
  Heart,
  Leaf,
  MapPin,
  Phone,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import { formatDistance, placeholderImage } from "../utils/format";

export default function RestaurantCard({
  restaurant,
  isFavorite = false,
  favoriteBusy = false,
  onToggleFavorite,
}) {
  const distance = formatDistance(restaurant.distance_km);
  const hasReviews = restaurant.review_count > 0;
  const hasAi = restaurant.ai_match !== undefined && restaurant.ai_match !== null;

  return (
    <article className="restaurant-card" data-testid="restaurant-card">
      <div className="restaurant-image">
        <Link to={`/restaurant/${restaurant.id}`} aria-label={`Open ${restaurant.name}`}>
          <img src={placeholderImage(restaurant)} alt={restaurant.name} loading="lazy" />
        </Link>

        {onToggleFavorite && (
          <button
            className={`favorite-button ${isFavorite ? "active liked" : ""}`}
            onClick={() => onToggleFavorite(restaurant)}
            disabled={favoriteBusy}
            aria-pressed={isFavorite}
            aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
          >
            <Heart size={18} fill={isFavorite ? "currentColor" : "none"} />
          </button>
        )}

        {hasAi && (
          <span className="ai-match">
            <Sparkles size={12} />
            {restaurant.ai_match}% MATCH
          </span>
        )}
      </div>

      <div className="restaurant-body">
        <div className="restaurant-title-row">
          <h3>{restaurant.name}</h3>

          <span className="rating">
            <Star size={14} fill={hasReviews ? "currentColor" : "none"} />
            {hasReviews ? restaurant.rating.toFixed(1) : "New"}
          </span>
        </div>

        <p className="cuisine">{restaurant.cuisine || "Restaurant"}</p>

        <div className="tags">
          {restaurant.diet_tags?.slice(0, 3).map((tag) => (
            <span
              key={tag.name}
              className={`diet-tag ${tag.level}`}
              title={tag.note}
            >
              <Leaf size={10} />
              {tag.name}
              {tag.level === "likely" ? " · likely" : ""}
            </span>
          ))}
          {!restaurant.diet_tags?.length && (
            <span className="amenity-tag">
              {(restaurant.amenity || "restaurant").replace("_", " ")}
            </span>
          )}
        </div>

        <div className="location-row">
          <MapPin size={14} />
          <span>{restaurant.address || "Address not listed"}</span>
          {distance && <b className="distance-chip">{distance}</b>}
        </div>

        {restaurant.phone && (
          <div className="location-row">
            <Phone size={14} />
            {restaurant.phone}
          </div>
        )}

        {hasAi && restaurant.match_reasons?.length > 0 && (
          <ul className="match-reasons">
            {restaurant.match_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}

        {hasAi && restaurant.recommended_dish && (
          <div className="dish-insight">
            <div>
              <span>AI DISH INSIGHT</span>
              <strong>{restaurant.recommended_dish}</strong>
            </div>
          </div>
        )}

        {restaurant.note && <p className="card-note">{restaurant.note}</p>}

        <div className="trust-row">
          <ShieldCheck size={16} />
          {hasReviews
            ? `${restaurant.review_count} review${restaurant.review_count === 1 ? "" : "s"}`
            : "No reviews yet"}
        </div>

        <Link className="details-link" to={`/restaurant/${restaurant.id}`}>
          View restaurant
          <ArrowRight size={15} />
        </Link>
      </div>
    </article>
  );
}
