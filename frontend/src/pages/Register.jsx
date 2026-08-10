import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Check,
  Eye,
  EyeOff,
  Leaf,
  Sparkles,
  Wheat,
} from "lucide-react";
import { registerUser } from "../services/api";

const preferences = [
  "Vegetarian",
  "Vegan",
  "Jain",
  "Gluten-Free",
  "Dairy-Free",
];

export default function Register() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [selected, setSelected] = useState([]);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const togglePreference = (item) => {
    setSelected((current) =>
      current.includes(item)
        ? current.filter((x) => x !== item)
        : [...current, item]
    );
  };

  const handleRegister = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      await registerUser({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
      });

      navigate("/login");
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
          Back to home
        </Link>

        <div className="register-form-container">

          <span className="auth-label">
            <Sparkles size={15} />
            PERSONALIZED FOOD DISCOVERY
          </span>

          <h1>
            Create your
            <br />
            <span>account.</span>
          </h1>

          <p>
            Tell us a little about yourself so DineSmart can personalize
            your food discovery experience.
          </p>

          <form onSubmit={handleRegister} className="auth-form">

            <div className="form-row">

              <div>
                <label>First name</label>

                <input
                  type="text"
                  placeholder="Jefrin"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label>Last name</label>

                <input
                  type="text"
                  placeholder="Raja"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>

            </div>

            <label>Email address</label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <label>Password</label>

            <div className="password-input">

              <input
                type={showPassword ? "text" : "password"}
                placeholder="Create a strong password"
                minLength="8"
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

            <div className="dietary-title">

              <div>
                <label>Dietary preferences</label>
                <small>Optional — you can change these later.</small>
              </div>

              <Leaf size={18} />

            </div>

            <div className="preference-select-grid">

              {preferences.map((item) => {

                const active = selected.includes(item);

                return (
                  <button
                    type="button"
                    key={item}
                    className={`preference-select ${
                      active ? "selected" : ""
                    }`}
                    onClick={() => togglePreference(item)}
                  >
                    <span>{item}</span>

                    <span className="preference-check">
                      {active && <Check size={12} />}
                    </span>

                  </button>
                );
              })}

            </div>

            <div className="register-note">

              <Wheat size={16} />

              <span>
                Your preferences help us provide more relevant restaurant
                and dish recommendations.
              </span>

            </div>

            {error && (
              <div className="auth-error">
                {error}
              </div>
            )}

            <button
              className="auth-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? "Creating account..." : "Create account"}
            </button>

          </form>

          <p className="auth-switch">
            Already have an account?{" "}
            <Link to="/login">Sign in</Link>
          </p>

        </div>
      </div>

      <div className="register-visual">

        <div className="register-image">

          <img
            src="https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=85"
            alt="Healthy food"
          />

          <div className="register-overlay">

            <span>PERSONALIZED FOR YOU</span>

            <h2>
              Food discovery that understands your preferences.
            </h2>

          </div>

        </div>

      </div>

    </div>
  );
}
