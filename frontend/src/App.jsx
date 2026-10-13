import { useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";

import GetStarted from "./pages/GetStarted";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RestaurantDetails from "./pages/RestaurantDetails";
import Profile from "./pages/Profile";
import Restaurants from "./pages/Restaurants";
import Owner from "./pages/owner";

import {
  isLoggedIn,
  SESSION_EXPIRED_EVENT,
} from "./services/session";

import "./App.css";

function ProtectedRoute({ children }) {
  // Needs BOTH the user and a token.
  // Old sessions without a token must log in again.
  return isLoggedIn() ? children : <Navigate to="/login" replace />;
}

// Owner-only frontend route.
// The Owner.jsx page also performs its own role check.
function OwnerRoute({ children }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }

  let user = null;

  try {
    user = JSON.parse(
      localStorage.getItem("user") || "null"
    );
  } catch {
    user = null;
  }

  const role = String(user?.role || "").toLowerCase();

  if (role !== "owner" && role !== "admin") {
    return <Navigate to="/home" replace />;
  }

  return children;
}

// When the API says the token expired,
// send the user to the login page.
function SessionWatcher() {
  const navigate = useNavigate();

  useEffect(() => {
    const onExpired = () => {
      navigate("/login", { replace: true });
    };

    window.addEventListener(
      SESSION_EXPIRED_EVENT,
      onExpired
    );

    return () =>
      window.removeEventListener(
        SESSION_EXPIRED_EVENT,
        onExpired
      );
  }, [navigate]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <SessionWatcher />

      <Routes>
        {/* PUBLIC ROUTES */}
        <Route
          path="/"
          element={<GetStarted />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        {/* CUSTOMER ROUTES */}
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />

        <Route
          path="/restaurants"
          element={
            <ProtectedRoute>
              <Restaurants />
            </ProtectedRoute>
          }
        />

        <Route
          path="/restaurant/:id"
          element={
            <ProtectedRoute>
              <RestaurantDetails />
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        {/* OWNER / ADMIN ROUTE */}
        <Route
          path="/owner"
          element={
            <OwnerRoute>
              <Owner />
            </OwnerRoute>
          }
        />

        {/* UNKNOWN ROUTES */}
        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;