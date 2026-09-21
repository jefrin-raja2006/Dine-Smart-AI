import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import GetStarted from "./pages/GetStarted";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RestaurantDetails from "./pages/RestaurantDetails";
import Profile from "./pages/Profile";
import Restaurants from "./pages/Restaurants";
import { isLoggedIn, SESSION_EXPIRED_EVENT } from "./services/session";
import "./App.css";

function ProtectedRoute({ children }) {
  // needs BOTH the user and a token (old sessions without a token must re-login)
  return isLoggedIn() ? children : <Navigate to="/login" replace />;
}

// When the API says the token expired, send the user to the login page.
function SessionWatcher() {
  const navigate = useNavigate();

  useEffect(() => {
    const onExpired = () => navigate("/login", { replace: true });
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, [navigate]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <SessionWatcher />
      <Routes>
        <Route path="/" element={<GetStarted />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/restaurants" element={<ProtectedRoute><Restaurants /></ProtectedRoute>} />
        <Route path="/restaurant/:id" element={<ProtectedRoute><RestaurantDetails /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
