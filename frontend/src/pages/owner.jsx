
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  Bell,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Clock,
  Edit3,
  LayoutDashboard,
  LogOut,
  MapPin,
  MessageSquare,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Star,
  Store,
  Trash2,
  TrendingUp,
  Utensils,
  X,
} from "lucide-react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const ORANGE = "#F4512A";
const PALE_ORANGE = "#FFF0E8";
const PAGE_BG = "#FFF9F5";
const BORDER = "#F0E1D8";
const MUTED = "#796960";
const DARK = "#29211E";

const styles = {
  page: {
    minHeight: "100vh",
    background: PAGE_BG,
    color: DARK,
    fontFamily: "Inter, system-ui, sans-serif",
  },
  header: {
    position: "sticky",
    top: 0,
    zIndex: 20,
    background: "#fff",
    borderBottom: `1px solid ${BORDER}`,
    padding: "13px 4.5%",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 15,
    flexWrap: "wrap",
  },
  brand: { display: "flex", alignItems: "center", gap: 12 },
  logo: {
    width: 42,
    height: 42,
    borderRadius: 13,
    background: ORANGE,
    color: "#fff",
    display: "grid",
    placeItems: "center",
    fontWeight: 900,
    fontSize: 19,
  },
  brandName: { display: "block", fontWeight: 850, fontSize: 16 },
  brandSub: { display: "block", color: MUTED, fontSize: 11, marginTop: 3 },
  headerActions: {
    display: "flex",
    alignItems: "center",
    gap: 9,
    flexWrap: "wrap",
  },
  main: {
    width: "min(1200px, 91%)",
    margin: "0 auto",
    padding: "32px 0 60px",
  },
  eyebrow: {
    color: ORANGE,
    fontSize: 11,
    letterSpacing: ".15em",
    fontWeight: 850,
    textTransform: "uppercase",
  },
  heading: {
    fontSize: "clamp(30px, 4vw, 43px)",
    letterSpacing: "-.045em",
    margin: "9px 0",
    lineHeight: 1.13,
  },
  subtitle: { color: MUTED, lineHeight: 1.7, margin: 0 },
  button: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: "10px 14px",
    border: `1px solid ${BORDER}`,
    borderRadius: 11,
    background: "#fff",
    color: DARK,
    cursor: "pointer",
    fontWeight: 750,
    fontSize: 13,
  },
  primary: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: "11px 16px",
    border: `1px solid ${ORANGE}`,
    borderRadius: 11,
    background: ORANGE,
    color: "#fff",
    cursor: "pointer",
    fontWeight: 800,
    fontSize: 13,
  },
  danger: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    padding: "9px 11px",
    border: "1px solid #F5D2C8",
    borderRadius: 9,
    background: "#FFF5F2",
    color: "#B93822",
    cursor: "pointer",
    fontWeight: 700,
    fontSize: 12,
  },
  card: {
    background: "#fff",
    border: `1px solid ${BORDER}`,
    borderRadius: 17,
    padding: 20,
    minWidth: 0,
    boxShadow: "0 5px 18px rgba(74,33,11,.025)",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 850,
    margin: 0,
    letterSpacing: "-.02em",
  },
  smallLabel: { color: MUTED, fontSize: 12 },
  field: {
    width: "100%",
    boxSizing: "border-box",
    padding: "11px 12px",
    borderRadius: 10,
    border: `1px solid ${BORDER}`,
    background: "#FFFCFA",
    color: DARK,
    font: "inherit",
    fontSize: 13,
    outlineColor: ORANGE,
  },
  label: {
    display: "grid",
    gap: 7,
    color: "#68564D",
    fontSize: 12,
    fontWeight: 750,
  },
};

const asArray = (value) => (Array.isArray(value) ? value : []);

const firstValue = (...values) =>
  values.find((value) => value !== undefined && value !== null);

const getList = (data, ...keys) => {
  if (Array.isArray(data)) return data;

  for (const key of keys) {
    if (Array.isArray(data?.[key])) return data[key];
  }

  return [];
};

const getId = (item) => firstValue(item?.id, item?.restaurant_id, item?.menu_item_id);

const getName = (item) =>
  firstValue(item?.name, item?.restaurant_name, item?.title, "Restaurant");

const getRating = (review) =>
  Number(firstValue(review?.rating, review?.stars, review?.score, 0)) || 0;

const getReviewText = (review) =>
  firstValue(review?.comment, review?.review_text, review?.text, review?.content, "");

const getReviewer = (review) =>
  firstValue(review?.user_name, review?.customer_name, review?.username, "Customer");

const getSentiment = (review) => {
  const supplied = String(
    firstValue(review?.sentiment, review?.sentiment_label, "")
  ).toLowerCase();

  if (supplied.includes("positive")) return "Positive";
  if (supplied.includes("negative")) return "Negative";
  if (supplied.includes("neutral")) return "Neutral";

  const rating = getRating(review);
  if (rating >= 4) return "Positive";
  if (rating > 0 && rating <= 2) return "Negative";
  return "Neutral";
};

function StatCard({ icon: Icon, label, value, detail, accent = ORANGE }) {
  return (
    <div style={styles.card}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
        <span style={{ ...styles.smallLabel, fontWeight: 650 }}>{label}</span>
        <span
          style={{
            display: "grid",
            placeItems: "center",
            width: 38,
            height: 38,
            borderRadius: 12,
            background: PALE_ORANGE,
            color: accent,
            flexShrink: 0,
          }}
        >
          <Icon size={19} />
        </span>
      </div>

      <div
        style={{
          fontSize: 30,
          fontWeight: 900,
          letterSpacing: "-.045em",
          marginTop: 13,
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </div>

      <div style={{ ...styles.smallLabel, marginTop: 5, lineHeight: 1.5 }}>
        {detail}
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, title, message, action }) {
  return (
    <div
      style={{
        padding: "30px 15px",
        textAlign: "center",
        borderRadius: 13,
        background: "#FFFCFA",
        border: `1px dashed ${BORDER}`,
      }}
    >
      <Icon size={27} color={ORANGE} style={{ marginBottom: 9 }} />
      <div style={{ fontWeight: 800, marginBottom: 6 }}>{title}</div>
      <p style={{ color: MUTED, fontSize: 13, lineHeight: 1.7, margin: "0 auto 14px", maxWidth: 340 }}>
        {message}
      </p>
      {action}
    </div>
  );
}

function ReviewItem({ review }) {
  const rating = getRating(review);
  const sentiment = getSentiment(review);
  const comment = getReviewText(review);

  const sentimentColors = {
    Positive: { bg: "#EAF7EE", color: "#277344" },
    Neutral: { bg: "#FFF4E0", color: "#98651B" },
    Negative: { bg: "#FFF0EB", color: "#B93822" },
  };

  const sentimentStyle = sentimentColors[sentiment] || sentimentColors.Neutral;

  return (
    <div style={{ padding: "15px 0", borderBottom: `1px solid #F4EAE4` }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", gap: 10, minWidth: 0 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 11,
              background: PALE_ORANGE,
              color: ORANGE,
              display: "grid",
              placeItems: "center",
              fontWeight: 850,
              flexShrink: 0,
            }}
          >
            {String(getReviewer(review)).slice(0, 1).toUpperCase()}
          </div>

          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 13, overflowWrap: "anywhere" }}>
              {getReviewer(review)}
            </div>
            <div style={{ color: MUTED, fontSize: 11, marginTop: 4 }}>
              {firstValue(review?.created_at, review?.date, review?.createdAt, "Recent review")}
            </div>
          </div>
        </div>

        <div
          aria-label={`${rating} out of 5 stars`}
          style={{ display: "flex", gap: 2, alignItems: "center", flexShrink: 0 }}
        >
          {[1, 2, 3, 4, 5].map((star) => (
            <Star
              key={star}
              size={13}
              fill={star <= rating ? "#F59E0B" : "none"}
              color={star <= rating ? "#F59E0B" : "#D9CEC6"}
            />
          ))}
          <span style={{ color: MUTED, fontSize: 11, marginLeft: 4 }}>
            {rating ? `${rating}/5` : "Not rated"}
          </span>
        </div>
      </div>

      <p style={{ fontSize: 13, lineHeight: 1.7, margin: "12px 0", color: "#51433D", overflowWrap: "anywhere" }}>
        {comment || "No written comment was provided."}
      </p>

      <span
        style={{
          display: "inline-block",
          borderRadius: 30,
          padding: "5px 9px",
          fontSize: 10,
          fontWeight: 800,
          background: sentimentStyle.bg,
          color: sentimentStyle.color,
        }}
      >
        {sentiment} feedback
      </span>
    </div>
  );
}

function RatingDistribution({ reviews }) {
  const counts = [5, 4, 3, 2, 1].map((rating) => ({
    rating,
    count: reviews.filter((review) => getRating(review) === rating).length,
  }));

  const maxCount = Math.max(1, ...counts.map((item) => item.count));

  return (
    <div style={{ display: "grid", gap: 13, marginTop: 22 }}>
      {counts.map(({ rating, count }) => (
        <div
          key={rating}
          style={{
            display: "grid",
            gridTemplateColumns: "38px minmax(30px,1fr) 28px",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span style={{ color: MUTED, fontSize: 12, fontWeight: 750 }}>
            {rating} <Star size={11} fill="#F59E0B" color="#F59E0B" style={{ verticalAlign: "middle" }} />
          </span>

          <div
            style={{
              height: 9,
              borderRadius: 20,
              background: "#F4EAE4",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${(count / maxCount) * 100}%`,
                height: "100%",
                background: ORANGE,
                borderRadius: 20,
                transition: "width .25s ease",
              }}
            />
          </div>

          <span style={{ fontSize: 12, textAlign: "right", fontWeight: 750 }}>
            {count}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function Owner() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [restaurants, setRestaurants] = useState([]);
  const [restaurantId, setRestaurantId] = useState("");
  const [restaurant, setRestaurant] = useState(null);
  const [stats, setStats] = useState({});
  const [reviews, setReviews] = useState([]);
  const [menu, setMenu] = useState([]);

  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [reviewFilter, setReviewFilter] = useState("All");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [saving, setSaving] = useState(false);

  const [menuForm, setMenuForm] = useState({
    name: "",
    description: "",
    price: "",
    category: "",
    is_available: true,
  });

  const token =
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    "";

  const apiFetch = useCallback(
    async (path, options = {}) => {
      const headers = {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      };

      const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        navigate("/login");
        throw new Error("Your session has expired. Please sign in again.");
      }

      if (!response.ok) {
        const body = await response.text().catch(() => "");
        let message = `Request failed (${response.status})`;

        if (body) {
          try {
            const parsed = JSON.parse(body);
            message = parsed.detail || parsed.message || message;
          } catch {
            message = body.slice(0, 200);
          }
        }

        throw new Error(message);
      }

      if (response.status === 204) return null;

      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        return response.json();
      }

      return null;
    },
    [navigate, token]
  );

  const loadDashboard = useCallback(
    async (showSpinner = true) => {
      if (showSpinner) setLoading(true);
      setRefreshing(!showSpinner);
      setError("");
      setNotice("");

      try {
        const restaurantData = await apiFetch("/owner/restaurants");
        const restaurantList = getList(
          restaurantData,
          "restaurants",
          "items",
          "data"
        );

        setRestaurants(restaurantList);

        if (!restaurantList.length) {
          setRestaurant(null);
          setRestaurantId("");
          setStats({});
          setReviews([]);
          setMenu([]);
          setError("");
          return;
        }

        const selected =
          restaurantList.find((item) => String(getId(item)) === String(restaurantId)) ||
          restaurantList[0];

        const selectedId = getId(selected);

        if (selectedId === undefined || selectedId === null) {
          throw new Error("A restaurant ID is missing from the API response.");
        }

        setRestaurantId(String(selectedId));

        const results = await Promise.allSettled([
          apiFetch(`/owner/restaurants/${selectedId}`),
          apiFetch(`/owner/restaurants/${selectedId}/stats`),
          apiFetch(`/owner/restaurants/${selectedId}/reviews`),
          apiFetch(`/owner/restaurants/${selectedId}/menu`),
        ]);

        const [restaurantResult, statsResult, reviewsResult, menuResult] = results;

        setRestaurant(
          restaurantResult.status === "fulfilled"
            ? restaurantResult.value?.restaurant || restaurantResult.value || selected
            : selected
        );

        setStats(
          statsResult.status === "fulfilled"
            ? statsResult.value?.stats || statsResult.value || {}
            : {}
        );

        setReviews(
          reviewsResult.status === "fulfilled"
            ? getList(reviewsResult.value, "reviews", "items", "data")
            : []
        );

        setMenu(
          menuResult.status === "fulfilled"
            ? getList(menuResult.value, "menu", "menu_items", "items", "data")
            : []
        );

        const failed = results.filter((result) => result.status === "rejected");
        if (failed.length) {
          setNotice(
            "Some dashboard sections could not load. Check your backend logs and API responses."
          );
        }
      } catch (err) {
        setError(
          err.message ||
            "Unable to load the owner dashboard. Check that the backend is running."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [apiFetch, restaurantId]
  );

  useEffect(() => {
    let storedUser = null;

    try {
      storedUser = JSON.parse(localStorage.getItem("user") || "null");
    } catch {
      storedUser = null;
    }

    setUser(storedUser);

    if (!token) {
      navigate("/login");
      return;
    }

    if (storedUser?.role && !["owner", "restaurant_owner"].includes(
      String(storedUser.role).toLowerCase()
    )) {
      navigate("/");
      return;
    }

    loadDashboard(true);
    // Load the initial dashboard once; restaurant changes are handled below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const changeRestaurant = async (nextId) => {
    setRestaurantId(nextId);
    setLoading(true);
    setError("");
    setNotice("");

    try {
      const selected = restaurants.find((item) => String(getId(item)) === String(nextId));

      if (!selected) return;

      const results = await Promise.allSettled([
        apiFetch(`/owner/restaurants/${nextId}`),
        apiFetch(`/owner/restaurants/${nextId}/stats`),
        apiFetch(`/owner/restaurants/${nextId}/reviews`),
        apiFetch(`/owner/restaurants/${nextId}/menu`),
      ]);

      setRestaurant(
        results[0].status === "fulfilled"
          ? results[0].value?.restaurant || results[0].value || selected
          : selected
      );

      setStats(
        results[1].status === "fulfilled"
          ? results[1].value?.stats || results[1].value || {}
          : {}
      );

      setReviews(
        results[2].status === "fulfilled"
          ? getList(results[2].value, "reviews", "items", "data")
          : []
      );

      setMenu(
        results[3].status === "fulfilled"
          ? getList(results[3].value, "menu", "menu_items", "items", "data")
          : []
      );

      if (results.some((result) => result.status === "rejected")) {
        setNotice("Some restaurant details could not be loaded.");
      }
    } catch (err) {
      setError(err.message || "Could not switch restaurants.");
    } finally {
      setLoading(false);
    }
  };

  const averageRating = useMemo(() => {
    const value = firstValue(
      stats?.average_rating,
      stats?.avg_rating,
      stats?.rating_average,
      restaurant?.average_rating
    );

    if (value !== undefined) return Number(value) || 0;

    const rated = reviews.filter((review) => getRating(review) > 0);
    return rated.length
      ? rated.reduce((sum, review) => sum + getRating(review), 0) / rated.length
      : 0;
  }, [stats, reviews, restaurant]);

  const totalReviews = Number(
    firstValue(stats?.total_reviews, stats?.review_count, stats?.reviews_count, reviews.length)
  ) || 0;

  const totalMenuItems = Number(
    firstValue(stats?.total_menu_items, stats?.menu_items_count, stats?.menu_count, menu.length)
  ) || 0;

  const positiveCount = reviews.filter(
    (review) => getSentiment(review) === "Positive"
  ).length;

  const positivePercentage = reviews.length
    ? Math.round((positiveCount / reviews.length) * 100)
    : null;

  const negativeCount = reviews.filter(
    (review) => getSentiment(review) === "Negative"
  ).length;

  const filteredMenu = menu.filter((item) => {
    const query = search.trim().toLowerCase();

    return (
      !query ||
      String(item?.name || "").toLowerCase().includes(query) ||
      String(item?.category || "").toLowerCase().includes(query) ||
      String(item?.description || "").toLowerCase().includes(query)
    );
  });

  const filteredReviews = reviews.filter((review) => {
    if (reviewFilter === "All") return true;
    return getSentiment(review) === reviewFilter;
  });

  const openAddModal = () => {
    setEditingItem(null);
    setMenuForm({
      name: "",
      description: "",
      price: "",
      category: "",
      is_available: true,
    });
    setModalOpen(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setMenuForm({
      name: item?.name || "",
      description: item?.description || "",
      price: item?.price ?? "",
      category: item?.category || "",
      is_available: item?.is_available ?? item?.available ?? true,
    });
    setModalOpen(true);
  };

  const saveMenuItem = async (event) => {
    event.preventDefault();
    if (!restaurantId) return;

    if (!menuForm.name.trim()) {
      setError("Please enter a dish name.");
      return;
    }

    const price = Number(menuForm.price);
    if (menuForm.price === "" || !Number.isFinite(price) || price < 0) {
      setError("Enter a valid non-negative price.");
      return;
    }

    setSaving(true);
    setError("");
    setNotice("");

    const payload = {
      name: menuForm.name.trim(),
      description: menuForm.description.trim(),
      price,
      category: menuForm.category.trim(),
      is_available: Boolean(menuForm.is_available),
    };

    try {
      if (editingItem) {
        const id = getId(editingItem);
        if (id === undefined || id === null) {
          throw new Error("This menu item does not have an ID.");
        }

        await apiFetch(`/owner/menu/${id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });

        setNotice("Menu item updated successfully.");
      } else {
        await apiFetch(`/owner/restaurants/${restaurantId}/menu`, {
          method: "POST",
          body: JSON.stringify(payload),
        });

        setNotice("Menu item added successfully.");
      }

      setModalOpen(false);
      await loadDashboard(false);
    } catch (err) {
      setError(err.message || "Could not save the menu item.");
    } finally {
      setSaving(false);
    }
  };

  const deleteMenuItem = async (item) => {
    const id = getId(item);
    if (id === undefined || id === null) {
      setError("This menu item does not have an ID.");
      return;
    }

    if (!window.confirm(`Delete "${getName(item)}" from your menu?`)) return;

    setError("");
    setNotice("");

    try {
      await apiFetch(`/owner/menu/${id}`, { method: "DELETE" });
      setNotice("Menu item deleted.");
      await loadDashboard(false);
    } catch (err) {
      setError(err.message || "Could not delete the menu item.");
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const tabs = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "reviews", label: "Customer Reviews", icon: MessageSquare },
    { id: "menu", label: "Menu Management", icon: Utensils },
  ];

  const restaurantName = getName(restaurant || restaurants[0] || {});
  const restaurantAddress = firstValue(
    restaurant?.address,
    restaurant?.location,
    restaurant?.city,
    ""
  );

  if (loading && !restaurant) {
    return (
      <div
        style={{
          ...styles.page,
          display: "grid",
          placeItems: "center",
          padding: 20,
          textAlign: "center",
        }}
      >
        <div>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 15,
              display: "grid",
              placeItems: "center",
              background: PALE_ORANGE,
              color: ORANGE,
              margin: "0 auto 15px",
            }}
          >
            <RefreshCw size={23} />
          </div>
          <p style={{ color: ORANGE, fontWeight: 800 }}>
            Loading owner dashboard...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.brand}>
          <div style={styles.logo}>D</div>
          <div>
            <span style={styles.brandName}>DineSmart AI</span>
            <span style={styles.brandSub}>Restaurant Owner</span>
          </div>
        </div>

        <div style={styles.headerActions}>
          <span style={{ fontSize: 13, fontWeight: 800 }}>
            {firstValue(user?.name, user?.full_name, user?.username, "Restaurant Owner")}
          </span>

          <button
            style={styles.button}
            onClick={() => loadDashboard(false)}
            disabled={refreshing}
          >
            <RefreshCw size={15} className={refreshing ? "owner-spin" : ""} />
            Refresh
          </button>

          <button style={styles.danger} onClick={logout}>
            <LogOut size={15} />
            Logout
          </button>
        </div>
      </header>

      <main style={styles.main}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            gap: 20,
            flexWrap: "wrap",
            marginBottom: 24,
          }}
        >
          <div>
            <p style={styles.eyebrow}>✦ &nbsp; Owner dashboard</p>
            <h1 style={styles.heading}>
              Manage your restaurant<span style={{ color: ORANGE }}>.</span>
            </h1>
            <p style={styles.subtitle}>
              Monitor performance, manage your menu, and understand your customers.
            </p>
          </div>

          <button
            style={styles.primary}
            onClick={openAddModal}
            disabled={!restaurantId}
          >
            <Plus size={17} />
            Add menu item
          </button>
        </div>

        {error && (
          <div
            role="alert"
            style={{
              background: "#FFF0EB",
              border: "1px solid #F3C7BA",
              color: "#9E321F",
              padding: 14,
              borderRadius: 12,
              marginBottom: 17,
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
            }}
          >
            <CircleAlert size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <div style={{ flex: 1, fontSize: 13, lineHeight: 1.6 }}>{error}</div>
            <button
              aria-label="Dismiss error"
              style={{ ...styles.button, padding: 5, border: 0 }}
              onClick={() => setError("")}
            >
              <X size={15} />
            </button>
          </div>
        )}

        {notice && (
          <div
            role="status"
            style={{
              background: "#EDF8F0",
              border: "1px solid #CDE9D4",
              color: "#277344",
              padding: 13,
              borderRadius: 12,
              marginBottom: 17,
              fontSize: 13,
            }}
          >
            <CheckCircle2 size={16} style={{ verticalAlign: "middle", marginRight: 7 }} />
            {notice}
          </div>
        )}

        {restaurants.length > 0 && (
          <section
            style={{
              ...styles.card,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 20,
              flexWrap: "wrap",
              marginBottom: 20,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14, minWidth: 0 }}>
              <div
                style={{
                  width: 52,
                  height: 52,
                  display: "grid",
                  placeItems: "center",
                  borderRadius: 15,
                  background: PALE_ORANGE,
                  color: ORANGE,
                  flexShrink: 0,
                }}
              >
                <Store size={25} />
              </div>

              <div style={{ minWidth: 0 }}>
                <p style={{ ...styles.eyebrow, margin: "0 0 5px", fontSize: 10 }}>
                  My restaurant
                </p>
                <h2 style={{ fontSize: 21, margin: 0, overflowWrap: "anywhere" }}>
                  {restaurantName}
                </h2>
                {restaurantAddress && (
                  <p style={{ color: MUTED, fontSize: 12, margin: "7px 0 0" }}>
                    <MapPin size={13} style={{ verticalAlign: "middle", marginRight: 4 }} />
                    {restaurantAddress}
                  </p>
                )}
              </div>
            </div>

            {restaurants.length > 1 && (
              <label style={{ ...styles.label, minWidth: 200 }}>
                Switch restaurant
                <span style={{ position: "relative" }}>
                  <select
                    value={restaurantId}
                    onChange={(event) => changeRestaurant(event.target.value)}
                    style={{ ...styles.field, appearance: "auto" }}
                  >
                    {restaurants.map((item, index) => (
                      <option key={getId(item) ?? index} value={String(getId(item))}>
                        {getName(item)}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    size={14}
                    style={{
                      position: "absolute",
                      right: 11,
                      top: "50%",
                      transform: "translateY(-50%)",
                      pointerEvents: "none",
                      display: "none",
                    }}
                  />
                </span>
              </label>
            )}
          </section>
        )}

        {restaurants.length === 0 && !error ? (
          <section style={styles.card}>
            <EmptyState
              icon={Store}
              title="No restaurant found"
              message="Your account does not currently have a restaurant linked to it. Check the owner-to-restaurant assignment in your database."
              action={
                <button style={styles.button} onClick={() => loadDashboard(false)}>
                  <RefreshCw size={15} />
                  Try again
                </button>
              }
            />
          </section>
        ) : (
          <>
            <nav
              aria-label="Owner dashboard sections"
              style={{
                display: "flex",
                gap: 9,
                flexWrap: "wrap",
                marginBottom: 20,
              }}
            >
              {tabs.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  style={{
                    ...styles.button,
                    padding: "11px 15px",
                    background: tab === id ? ORANGE : "#fff",
                    borderColor: tab === id ? ORANGE : BORDER,
                    color: tab === id ? "#fff" : "#68564D",
                    boxShadow: tab === id ? "0 5px 14px #F4512A24" : "none",
                  }}
                >
                  <Icon size={16} />
                  {label}
                </button>
              ))}
            </nav>

            {tab === "overview" && (
              <>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(min(100%,205px), 1fr))",
                    gap: 14,
                    marginBottom: 20,
                  }}
                >
                  <StatCard
                    icon={Star}
                    label="Average rating"
                    value={averageRating ? averageRating.toFixed(1) : "—"}
                    detail={totalReviews ? `Across ${totalReviews} reviews` : "Waiting for ratings"}
                  />
                  <StatCard
                    icon={MessageSquare}
                    label="Total reviews"
                    value={totalReviews}
                    detail="Customer feedback received"
                  />
                  <StatCard
                    icon={Utensils}
                    label="Menu items"
                    value={totalMenuItems}
                    detail="Items listed in your menu"
                  />
                  <StatCard
                    icon={TrendingUp}
                    label="Positive reviews"
                    value={positivePercentage === null ? "—" : `${positivePercentage}%`}
                    detail={
                      positivePercentage === null
                        ? "No reviews to analyze yet"
                        : `${positiveCount} positive in the loaded reviews`
                    }
                  />
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(min(100%,340px), 1fr))",
                    gap: 18,
                    marginBottom: 20,
                    alignItems: "stretch",
                  }}
                >
                  <section style={styles.card}>
                    <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
                      <span
                        style={{
                          display: "grid",
                          placeItems: "center",
                          width: 39,
                          height: 39,
                          borderRadius: 12,
                          background: PALE_ORANGE,
                          color: ORANGE,
                        }}
                      >
                        <BarChart3 size={19} />
                      </span>
                      <div>
                        <h2 style={styles.sectionTitle}>Customer rating</h2>
                        <p style={{ ...styles.smallLabel, margin: "5px 0 0" }}>
                          Distribution of loaded reviews
                        </p>
                      </div>
                    </div>

                    {reviews.length ? (
                      <RatingDistribution reviews={reviews} />
                    ) : (
                      <div style={{ paddingTop: 24 }}>
                        <EmptyState
                          icon={Star}
                          title="No ratings yet"
                          message="Rating distribution will appear when customer reviews are available."
                        />
                      </div>
                    )}

                    <div
                      style={{
                        display: "flex",
                        gap: 12,
                        flexWrap: "wrap",
                        marginTop: 22,
                        paddingTop: 15,
                        borderTop: `1px solid ${BORDER}`,
                      }}
                    >
                      <span style={{ fontSize: 12, color: "#277344" }}>
                        ● Positive: {positiveCount}
                      </span>
                      <span style={{ fontSize: 12, color: "#98651B" }}>
                        ● Neutral: {reviews.filter((review) => getSentiment(review) === "Neutral").length}
                      </span>
                      <span style={{ fontSize: 12, color: "#B93822" }}>
                        ● Negative: {negativeCount}
                      </span>
                    </div>
                  </section>

                  <section style={styles.card}>
                    <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
                      <span
                        style={{
                          display: "grid",
                          placeItems: "center",
                          width: 39,
                          height: 39,
                          borderRadius: 12,
                          background: PALE_ORANGE,
                          color: ORANGE,
                        }}
                      >
                        <MessageSquare size={19} />
                      </span>
                      <div>
                        <h2 style={styles.sectionTitle}>Recent reviews</h2>
                        <p style={{ ...styles.smallLabel, margin: "5px 0 0" }}>
                          The latest available customer feedback
                        </p>
                      </div>
                    </div>

                    {reviews.length ? (
                      <>
                        {reviews.slice(0, 3).map((review, index) => (
                          <ReviewItem
                            key={getId(review) ?? review?.created_at ?? index}
                            review={review}
                          />
                        ))}

                        <button
                          style={{ ...styles.button, width: "100%", marginTop: 15 }}
                          onClick={() => setTab("reviews")}
                        >
                          View all reviews
                          <MessageSquare size={15} />
                        </button>
                      </>
                    ) : (
                      <div style={{ paddingTop: 24 }}>
                        <EmptyState
                          icon={MessageSquare}
                          title="No reviews yet"
                          message="Customer comments will appear here when reviews are available."
                        />
                      </div>
                    )}
                  </section>
                </div>

                <section style={styles.card}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 12,
                      flexWrap: "wrap",
                      marginBottom: 18,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
                      <span
                        style={{
                          display: "grid",
                          placeItems: "center",
                          width: 39,
                          height: 39,
                          borderRadius: 12,
                          background: PALE_ORANGE,
                          color: ORANGE,
                        }}
                      >
                        <Utensils size={19} />
                      </span>
                      <div>
                        <h2 style={styles.sectionTitle}>Menu at a glance</h2>
                        <p style={{ ...styles.smallLabel, margin: "5px 0 0" }}>
                          A quick view of your listed dishes
                        </p>
                      </div>
                    </div>

                    <button style={styles.primary} onClick={openAddModal}>
                      <Plus size={15} />
                      Add dish
                    </button>
                  </div>

                  {menu.length ? (
                    <>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%,230px), 1fr))",
                          gap: 12,
                        }}
                      >
                        {menu.slice(0, 4).map((item, index) => {
                          const available = firstValue(
                            item?.is_available,
                            item?.available,
                            true
                          );

                          return (
                            <div
                              key={getId(item) ?? index}
                              style={{
                                border: `1px solid ${BORDER}`,
                                borderRadius: 13,
                                padding: 15,
                                display: "flex",
                                justifyContent: "space-between",
                                gap: 12,
                              }}
                            >
                              <div style={{ minWidth: 0 }}>
                                <div style={{ fontWeight: 800, fontSize: 13, overflowWrap: "anywhere" }}>
                                  {getName(item)}
                                </div>
                                <div style={{ color: MUTED, fontSize: 11, marginTop: 5 }}>
                                  {item?.category || "Uncategorized"}
                                </div>
                                <div style={{ color: ORANGE, fontWeight: 850, marginTop: 10 }}>
                                  {item?.price !== undefined ? `₹${item.price}` : "Price not set"}
                                </div>
                              </div>

                              <span
                                style={{
                                  alignSelf: "flex-start",
                                  borderRadius: 20,
                                  padding: "5px 8px",
                                  fontSize: 10,
                                  fontWeight: 800,
                                  background: available ? "#EAF7EE" : "#FFF0EB",
                                  color: available ? "#277344" : "#B93822",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {available ? "Available" : "Unavailable"}
                              </span>
                            </div>
                          );
                        })}
                      </div>

                      {menu.length > 4 && (
                        <button
                          style={{ ...styles.button, width: "100%", marginTop: 14 }}
                          onClick={() => setTab("menu")}
                        >
                          Manage all {menu.length} menu items
                        </button>
                      )}
                    </>
                  ) : (
                    <EmptyState
                      icon={Utensils}
                      title="Your menu is waiting"
                      message="Add your first dish with its price and category to get started."
                      action={
                        <button style={styles.primary} onClick={openAddModal}>
                          <Plus size={15} />
                          Add first dish
                        </button>
                      }
                    />
                  )}
                </section>
              </>
            )}

            {tab === "reviews" && (
              <section style={styles.card}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 15,
                    flexWrap: "wrap",
                    marginBottom: 17,
                  }}
                >
                  <div>
                    <h2 style={styles.sectionTitle}>Customer reviews</h2>
                    <p style={{ ...styles.smallLabel, marginTop: 6 }}>
                      Read customer feedback and monitor sentiment.
                    </p>
                  </div>

                  <select
                    value={reviewFilter}
                    onChange={(event) => setReviewFilter(event.target.value)}
                    style={{ ...styles.field, width: "auto", minWidth: 150 }}
                  >
                    <option value="All">All feedback</option>
                    <option value="Positive">Positive</option>
                    <option value="Neutral">Neutral</option>
                    <option value="Negative">Negative</option>
                  </select>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(130px,1fr))",
                    gap: 10,
                    marginBottom: 18,
                  }}
                >
                  {[
                    { label: "All reviews", value: reviews.length, color: DARK },
                    { label: "Positive", value: positiveCount, color: "#277344" },
                    { label: "Neutral", value: reviews.filter((review) => getSentiment(review) === "Neutral").length, color: "#98651B" },
                    { label: "Negative", value: negativeCount, color: "#B93822" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      style={{
                        background: "#FFFCFA",
                        border: `1px solid ${BORDER}`,
                        borderRadius: 12,
                        padding: 14,
                      }}
                    >
                      <div style={{ color: MUTED, fontSize: 11 }}>{item.label}</div>
                      <div style={{ fontSize: 23, fontWeight: 900, marginTop: 5, color: item.color }}>
                        {item.value}
                      </div>
                    </div>
                  ))}
                </div>

                {filteredReviews.length ? (
                  filteredReviews.map((review, index) => (
                    <ReviewItem
                      key={getId(review) ?? review?.created_at ?? index}
                      review={review}
                    />
                  ))
                ) : (
                  <EmptyState
                    icon={MessageSquare}
                    title="No matching reviews"
                    message="There are no reviews in this category yet."
                  />
                )}
              </section>
            )}

            {tab === "menu" && (
              <section style={styles.card}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 15,
                    flexWrap: "wrap",
                    marginBottom: 20,
                  }}
                >
                  <div>
                    <h2 style={styles.sectionTitle}>Menu management</h2>
                    <p style={{ ...styles.smallLabel, marginTop: 6 }}>
                      Manage your dishes, prices, and availability.
                    </p>
                  </div>

                  <button style={styles.primary} onClick={openAddModal}>
                    <Plus size={16} />
                    Add menu item
                  </button>
                </div>

                <div style={{ position: "relative", marginBottom: 19 }}>
                  <Search
                    size={17}
                    color={MUTED}
                    style={{
                      position: "absolute",
                      top: "50%",
                      left: 13,
                      transform: "translateY(-50%)",
                    }}
                  />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search dishes or categories..."
                    style={{ ...styles.field, paddingLeft: 39 }}
                  />
                </div>

                {filteredMenu.length ? (
                  <div style={{ display: "grid", gap: 12 }}>
                    {filteredMenu.map((item, index) => {
                      const available = firstValue(
                        item?.is_available,
                        item?.available,
                        true
                      );

                      return (
                        <div
                          key={getId(item) ?? index}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            gap: 16,
                            flexWrap: "wrap",
                            border: `1px solid ${BORDER}`,
                            borderRadius: 13,
                            padding: 16,
                          }}
                        >
                          <div style={{ minWidth: 0, flex: "1 1 220px" }}>
                            <div style={{ fontWeight: 850, overflowWrap: "anywhere" }}>
                              {getName(item)}
                            </div>
                            <div style={{ color: MUTED, fontSize: 12, marginTop: 5 }}>
                              {item?.category || "Uncategorized"}
                            </div>
                            {item?.description && (
                              <p style={{ color: MUTED, fontSize: 12, lineHeight: 1.6, margin: "7px 0 0" }}>
                                {item.description}
                              </p>
                            )}
                            <div style={{ fontWeight: 850, color: ORANGE, marginTop: 9 }}>
                              {item?.price !== undefined ? `₹${item.price}` : "Price not set"}
                            </div>
                          </div>

                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 9,
                              flexWrap: "wrap",
                            }}
                          >
                            <span
                              style={{
                                borderRadius: 30,
                                padding: "6px 9px",
                                background: available ? "#EAF7EE" : "#FFF0EB",
                                color: available ? "#277344" : "#B93822",
                                fontSize: 11,
                                fontWeight: 800,
                              }}
                            >
                              {available ? "Available" : "Unavailable"}
                            </span>

                            <button
                              style={styles.button}
                              onClick={() => openEditModal(item)}
                            >
                              <Edit3 size={14} />
                              Edit
                            </button>

                            <button
                              style={styles.danger}
                              onClick={() => deleteMenuItem(item)}
                            >
                              <Trash2 size={14} />
                              Delete
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <EmptyState
                    icon={Utensils}
                    title={search ? "No matching dishes" : "No menu items yet"}
                    message={
                      search
                        ? "Try another dish name or category."
                        : "Add your first dish to start managing your restaurant menu."
                    }
                    action={
                      !search && (
                        <button style={styles.primary} onClick={openAddModal}>
                          <Plus size={15} />
                          Add menu item
                        </button>
                      )
                    }
                  />
                )}
              </section>
            )}

            <footer
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 12,
                flexWrap: "wrap",
                color: MUTED,
                fontSize: 11,
                marginTop: 24,
              }}
            >
              <span>DineSmart AI · Restaurant management</span>
              <span>
                <Clock size={12} style={{ verticalAlign: "middle", marginRight: 5 }} />
                Data shown is based on the latest successful API response.
              </span>
            </footer>
          </>
        )}
      </main>

      {modalOpen && (
        <div
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !saving) {
              setModalOpen(false);
            }
          }}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(35,24,19,.48)",
            display: "grid",
            placeItems: "center",
            padding: 16,
            overflowY: "auto",
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="menu-modal-title"
            style={{
              background: "#fff",
              width: "min(100%, 520px)",
              borderRadius: 19,
              padding: 23,
              boxShadow: "0 25px 80px rgba(0,0,0,.2)",
              margin: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 12,
                marginBottom: 20,
              }}
            >
              <div>
                <p style={{ ...styles.eyebrow, margin: "0 0 5px" }}>
                  Menu management
                </p>
                <h2 id="menu-modal-title" style={{ ...styles.sectionTitle, fontSize: 22 }}>
                  {editingItem ? "Edit menu item" : "Add a new dish"}
                </h2>
              </div>

              <button
                aria-label="Close form"
                style={{ ...styles.button, padding: 8 }}
                onClick={() => setModalOpen(false)}
                disabled={saving}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={saveMenuItem} style={{ display: "grid", gap: 15 }}>
              <label style={styles.label}>
                Dish name *
                <input
                  style={styles.field}
                  value={menuForm.name}
                  onChange={(event) =>
                    setMenuForm({ ...menuForm, name: event.target.value })
                  }
                  placeholder="e.g. Masala dosa"
                  required
                />
              </label>

              <label style={styles.label}>
                Description
                <textarea
                  style={{ ...styles.field, minHeight: 85, resize: "vertical" }}
                  value={menuForm.description}
                  onChange={(event) =>
                    setMenuForm({ ...menuForm, description: event.target.value })
                  }
                  placeholder="Describe the dish..."
                  rows={3}
                />
              </label>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))",
                  gap: 13,
                }}
              >
                <label style={styles.label}>
                  Price (₹) *
                  <input
                    style={styles.field}
                    type="number"
                    min="0"
                    step="0.01"
                    value={menuForm.price}
                    onChange={(event) =>
                      setMenuForm({ ...menuForm, price: event.target.value })
                    }
                    placeholder="120"
                    required
                  />
                </label>

                <label style={styles.label}>
                  Category
                  <input
                    style={styles.field}
                    value={menuForm.category}
                    onChange={(event) =>
                      setMenuForm({ ...menuForm, category: event.target.value })
                    }
                    placeholder="Breakfast"
                  />
                </label>
              </div>

              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: 13,
                  border: `1px solid ${BORDER}`,
                  borderRadius: 11,
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={Boolean(menuForm.is_available)}
                  onChange={(event) =>
                    setMenuForm({
                      ...menuForm,
                      is_available: event.target.checked,
                    })
                  }
                  style={{ accentColor: ORANGE, width: 16, height: 16 }}
                />
                <span style={{ fontSize: 13, fontWeight: 750 }}>
                  This item is available for customers
                </span>
              </label>

              <div style={{ display: "flex", gap: 10, marginTop: 5 }}>
                <button
                  type="button"
                  style={{ ...styles.button, flex: 1 }}
                  onClick={() => setModalOpen(false)}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  style={{ ...styles.primary, flex: 1 }}
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <RefreshCw size={15} />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={16} />
                      {editingItem ? "Save changes" : "Add dish"}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style>{`
        .owner-spin {
          animation: ownerSpin .8s linear infinite;
        }
        @keyframes ownerSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @media (max-width: 600px) {
          button {
            max-width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
