import { Link, useLocation } from "react-router-dom";
import "../styles/Sidebar.css";
function Sidebar() {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <h2 className="logo">Employability Prediction System</h2>

      <nav>
        <Link className={location.pathname === "/" ? "active" : ""} to="/">
          Dashboard
        </Link>

        <Link className={location.pathname === "/prediction" ? "active" : ""} to="/prediction">
          Prediction
        </Link>

        <Link className={location.pathname === "/results" ? "active" : ""} to="/results">
          Results
        </Link>

        <Link className={location.pathname === "/model" ? "active" : ""} to="/model">
          Model Info
        </Link>
      </nav>
    </aside>
  );
}

export default Sidebar;