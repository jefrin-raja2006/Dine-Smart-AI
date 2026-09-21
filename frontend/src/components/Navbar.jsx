import { Link, NavLink, useNavigate } from "react-router-dom";
import { LogOut, User } from "lucide-react";
import { clearSession, getUser } from "../services/session";

export default function Navbar() {
  const navigate = useNavigate();
  const user = getUser();

  const handleLogout = () => {
    clearSession();
    navigate("/");
  };

  return (
    <header className="navbar">
      <Link className="brand" to="/home">
        <span className="brand-mark">D</span>
        DineSmart <b>AI</b>
      </Link>

      <nav className="nav-links">
        <NavLink to="/home">Home</NavLink>
        <NavLink to="/restaurants" end>
          Discover
        </NavLink>
        <NavLink to="/restaurants?mode=ai">AI Picks</NavLink>
      </nav>

      <div className="user-actions">
        <Link to="/profile" className="user-profile">
          <span className="user-icon">
            <User size={17} />
          </span>
          <span>{user?.name || "Profile"}</span>
        </Link>

        <button className="logout-button" onClick={handleLogout}>
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </header>
  );
}
