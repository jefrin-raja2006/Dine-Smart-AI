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
import { saveSession } from "../services/session";

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

  // =====================================================
  // TOGGLE DIETARY PREFERENCE
  // =====================================================

  const togglePreference = (item) => {
    setSelected((current) => {
      if (current.includes(item)) {
        return current.filter((x) => x !== item);
      }

      return [...current, item];
    });
  };

  // =====================================================
  // REGISTER
  // =====================================================

  const handleRegister = async (e) => {
    e.preventDefault();

    setError("");

    // Basic validation
    if (!firstName.trim()) {
      setError("Please enter your first name.");
      return;
    }

    if (!lastName.trim()) {
      setError("Please enter your last name.");
      return;
    }

    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      const result = await registerUser({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
        dietary_preferences: selected,
      });

      // The API returns a session token, so the new user is signed in right away
      saveSession(result);
      navigate("/home");
    } catch (err) {
      setError(
        err.message || "Unable to create account. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      {/* =================================================
          LEFT SIDE
      ================================================= */}

      <div className="auth-left">

        {/* BACK TO HOME */}

        <Link to="/" className="back-link">
          <ArrowLeft size={17} />
          Back to home
        </Link>


        {/* =================================================
            REGISTER FORM
        ================================================= */}

        <div className="register-form-container">

          {/* LABEL */}

          <span className="auth-label">
            <Sparkles size={15} />
            PERSONALIZED FOOD DISCOVERY
          </span>


          {/* TITLE */}

          <h1>
            Create your
            <br />
            <span>account.</span>
          </h1>


          {/* DESCRIPTION */}

          <p>
            Tell us a little about yourself so DineSmart can
            personalize your food discovery experience.
          </p>


          {/* =================================================
              FORM
          ================================================= */}

          <form
            onSubmit={handleRegister}
            className="auth-form"
          >

            {/* FIRST + LAST NAME */}

            <div className="form-row">

              <div>
                <label htmlFor="firstName">
                  First name
                </label>

                <input
                  id="firstName"
                  type="text"
                  placeholder="Jefrin"
                  value={firstName}
                  onChange={(e) =>
                    setFirstName(e.target.value)
                  }
                  required
                />
              </div>


              <div>
                <label htmlFor="lastName">
                  Last name
                </label>

                <input
                  id="lastName"
                  type="text"
                  placeholder="Raja"
                  value={lastName}
                  onChange={(e) =>
                    setLastName(e.target.value)
                  }
                  required
                />
              </div>

            </div>


            {/* EMAIL */}

            <label htmlFor="email">
              Email address
            </label>

            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              required
            />


            {/* PASSWORD */}

            <label htmlFor="password">
              Password
            </label>

            <div className="password-input">

              <input
                id="password"
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                placeholder="Create a strong password"
                minLength={8}
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                required
              />

              <button
                type="button"
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
                onClick={() =>
                  setShowPassword(!showPassword)
                }
              >
                {showPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>

            </div>


            {/* =================================================
                DIETARY PREFERENCES
            ================================================= */}

            <div className="dietary-title">

              <div>

                <label>
                  Dietary preferences
                </label>

                <small>
                  Optional — you can change these later.
                </small>

              </div>

              <Leaf size={18} />

            </div>


            {/* PREFERENCE BUTTONS */}

            <div className="preference-select-grid">

              {preferences.map((item) => {

                const active =
                  selected.includes(item);

                return (
                  <button
                    type="button"
                    key={item}
                    className={`preference-select ${
                      active ? "selected" : ""
                    }`}
                    onClick={() =>
                      togglePreference(item)
                    }
                    aria-pressed={active}
                  >

                    <span>
                      {item}
                    </span>

                    <span className="preference-check">

                      {active && (
                        <Check size={12} />
                      )}

                    </span>

                  </button>
                );
              })}

            </div>


            {/* =================================================
                INFORMATION NOTE
            ================================================= */}

            <div className="register-note">

              <Wheat size={16} />

              <span>
                Your preferences help us provide more
                relevant restaurant and dish recommendations.
              </span>

            </div>


            {/* =================================================
                ERROR MESSAGE
            ================================================= */}

            {error && (
              <div className="auth-error">
                {error}
              </div>
            )}


            {/* =================================================
                SUBMIT BUTTON
            ================================================= */}

            <button
              className="auth-submit"
              type="submit"
              disabled={loading}
            >

              {loading
                ? "Creating account..."
                : "Create account"}

            </button>

          </form>


          {/* =================================================
              LOGIN LINK
          ================================================= */}

          <p className="auth-switch">

            Already have an account?{" "}

            <Link to="/login">
              Sign in
            </Link>

          </p>

        </div>

      </div>


      {/* =================================================
          RIGHT SIDE IMAGE
      ================================================= */}

      <div className="register-visual">

        <div className="register-image">

          <img
            src="https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=85"
            alt="Healthy food"
          />


          {/* IMAGE OVERLAY */}

          <div className="register-overlay">

            <span>
              PERSONALIZED FOR YOU
            </span>

            <h2>
              Food discovery that understands
              your preferences.
            </h2>

          </div>

        </div>

      </div>

    </div>
  );
}