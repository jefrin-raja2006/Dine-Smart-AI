import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Eye, EyeOff, Sparkles } from "lucide-react";
import { loginUser } from "../services/api";
import { saveSession } from "../services/session";

export default function Login() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await loginUser({
        email,
        password,
      });

      saveSession(result);

      // Role-based navigation
      const role = result?.user?.role || "customer";

      if (role === "admin") {
        navigate("/admin");
      } else if (role === "owner") {
        navigate("/owner");
      } else {
        navigate("/home");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-left">
        <Link to="/" className="back-link">
          <ArrowLeft size={17} />
          Back
        </Link>

        <div className="auth-content">
          <span className="auth-label">
            <Sparkles size={15} />
            SMART FOOD DISCOVERY
          </span>

          <h1>
            Welcome
            <br />
            <span>back.</span>
          </h1>

          <p>
            Sign in to discover restaurants and dishes that fit your
            preferences.
          </p>

          <form onSubmit={handleLogin} className="auth-form">
            <label>Email address</label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <div className="password-label">
              <label>Password</label>
            </div>

            <div className="password-input">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>
            </div>

            {error && <div className="auth-error">{error}</div>}

            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="auth-switch">
            Don't have an account?{" "}
            <Link to="/register">Create one</Link>
          </p>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-image">
          <img
            src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85"
            alt="Food"
          />

          <div className="auth-overlay">
            <span>YOUR FOOD. YOUR PREFERENCES.</span>
            <h2>Find food that fits you.</h2>
          </div>
        </div>
      </div>
    </div>
  );
}