import { useEffect, useRef, useState } from "react";
import {
  FileText,
  Home,
  LayoutDashboard,
  LogOut,
  Mic,
  GraduationCap,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Layers,
} from "lucide-react";
import { healthCheck } from "./api.js";
import { logoutAccount, restoreSession } from "./authApi.js";
import AuthView from "./views/AuthView.jsx";
import DashboardView from "./views/DashboardView.jsx";
import InterviewCareerHubView from "./views/InterviewCareerHubView.jsx";
import InterviewReadyView from "./views/InterviewReadyView.jsx";
import CareerLensView from "./views/CareerLensView.jsx";
import CareerRiskView from "./views/CareerRiskView.jsx";
import EmployabilityView from "./views/EmployabilityView.jsx";
import HRCandidateSelectionView from "./views/HRCandidateSelectionView.jsx";

function getInitialView() {
  const path = window.location.pathname.toLowerCase();
  if (path.includes("interview-career") || path.includes("readiness-path")) return "interview-career";
  if (path.includes("communication") || path.includes("interview")) return "communication";
  if (path.includes("career-risk") || path.includes("risk") || path.includes("safety")) return "career-risk";
  if (path.includes("employability") || path.includes("simulation")) return "employability";
  if (path.includes("hr-candidate") || path.includes("hr-selection")) return "hr-candidates";
  if (path.includes("career") || path.includes("cv")) return "career";
  return "home";
}

function initialsFromName(name = "") {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "PR";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export default function App() {
  const [authReady, setAuthReady] = useState(false);
  const [user, setUser] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [currentView, setCurrentView] = useState(getInitialView);
  const [healthData, setHealthData] = useState({
    communicationModelReady: true,
    careerModelReady: true,
    careerRiskModelReady: true,
    serpapiConfigured: false,
    openaiGuidanceReady: false,
  });
  const menuRef = useRef(null);

  useEffect(() => {
    restoreSession()
      .then((sessionUser) => {
        setUser(sessionUser);
        if (sessionUser) {
          const path = window.location.pathname.toLowerCase();
          if (path.includes("login") || path.includes("register")) {
            window.history.replaceState({ view: "home" }, "", "/");
            setCurrentView("home");
          }
        }
      })
      .finally(() => setAuthReady(true));
  }, []);

  useEffect(() => {
    if (!user) return;
    healthCheck()
      .then((data) => {
        setHealthData(data);
      })
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentView(getInitialView());
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (currentView === "hr-candidates" && user && user.role !== "admin") {
      setCurrentView("home");
      window.history.replaceState({ view: "home" }, "", "/");
    }
  }, [currentView, user]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function navigateTo(view) {
    setCurrentView(view);
    setMenuOpen(false);
    const path =
      view === "interview-career"
        ? "/interview-career-guidance"
        : view === "communication"
        ? "/communication-guidance"
        : view === "career"
        ? "/cv-guidance"
        : view === "career-risk"
        ? "/career-risk-guidance"
        : view === "employability"
        ? "/employability-simulation"
        : view === "hr-candidates"
        ? "/hr-candidate-selection"
        : "/";
    window.history.pushState({ view }, "", path);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleAuthenticated(sessionUser) {
    setUser(sessionUser);
    setCurrentView("home");
    window.history.replaceState({ view: "home" }, "", "/");
  }

  async function handleLogout() {
    await logoutAccount();
    setUser(null);
    setMenuOpen(false);
    setCurrentView("home");
    window.history.replaceState({}, "", "/login");
  }

  if (!authReady) {
    return (
      <div className="boot-screen">
        <div className="brand-logo-mark">
          <GraduationCap size={26} />
        </div>
        <p>Loading PathReady AI Suite…</p>
      </div>
    );
  }

  if (!user) {
    return <AuthView onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div className="root-app-layout">
      <header className="global-topbar">
        <div className="brand-group" onClick={() => navigateTo("home")} role="button" tabIndex={0}>
          <div className="brand-logo-mark">
            <GraduationCap size={24} />
          </div>
          <div className="brand-titles">
            <span className="brand-main-title">Career Intelligence Platform</span>
            <span className="brand-sub-title">Comprehensive Career Development and Recruitment Framework</span>
          </div>
        </div>

        <nav className="global-nav-tabs">
          <button
            className={`nav-tab-link ${currentView === "home" ? "active" : ""}`}
            onClick={() => navigateTo("home")}
          >
            <Home size={16} />
            <span>Home</span>
          </button>
          <button
            className={`nav-tab-link ${
              currentView === "interview-career" || currentView === "communication" || currentView === "career"
                ? "active"
                : ""
            }`}
            onClick={() => navigateTo("interview-career")}
          >
            <Layers size={16} />
            <span>Interview Readiness & Career Path Guidance</span>
          </button>
          <button
            className={`nav-tab-link ${currentView === "career-risk" ? "active" : ""}`}
            onClick={() => navigateTo("career-risk")}
          >
            <ShieldAlert size={16} />
            <span>Career Safety</span>
          </button>
          <button
            className={`nav-tab-link ${currentView === "employability" ? "active" : ""}`}
            onClick={() => navigateTo("employability")}
          >
            <Sparkles size={16} />
            <span>Career Simulation</span>
          </button>
          {user.role === "admin" && (
            <button
              className={`nav-tab-link ${currentView === "hr-candidates" ? "active" : ""}`}
              onClick={() => navigateTo("hr-candidates")}
            >
              <ShieldCheck size={16} />
              <span>HR Candidates</span>
            </button>
          )}
        </nav>

        <div className="topbar-status-group">
          <div className="user-menu" ref={menuRef}>
            <button
              type="button"
              className="user-chip"
              onClick={() => setMenuOpen((open) => !open)}
              aria-expanded={menuOpen}
            >
              <span className="user-avatar">{initialsFromName(user.fullName)}</span>
              <span className="user-chip-copy">
                <strong>{user.fullName}</strong>
                <small>{user.email}</small>
              </span>
            </button>
            {menuOpen && (
              <div className="user-dropdown">
                <div className="user-dropdown-meta">
                  <LayoutDashboard size={14} />
                  Signed in to research workspace
                </div>
                <button type="button" className="logout-btn" onClick={handleLogout}>
                  <LogOut size={15} />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="main-viewport">
        {currentView === "home" && (
          <DashboardView
            onSelectModule={navigateTo}
            healthData={healthData}
            user={user}
          />
        )}
        {currentView === "interview-career" && (
          <InterviewCareerHubView
            onSelectModule={navigateTo}
            onBackToDashboard={() => navigateTo("home")}
            healthData={healthData}
          />
        )}
        {currentView === "communication" && (
          <InterviewReadyView onBackToDashboard={() => navigateTo("interview-career")} healthData={healthData} />
        )}
        {currentView === "career" && (
          <CareerLensView onBackToDashboard={() => navigateTo("interview-career")} healthData={healthData} />
        )}
        {currentView === "career-risk" && (
          <CareerRiskView onBackToDashboard={() => navigateTo("home")} healthData={healthData} />
        )}
        {currentView === "employability" && (
          <EmployabilityView onBackToDashboard={() => navigateTo("home")} healthData={healthData} />
        )}
        {currentView === "hr-candidates" && user.role === "admin" && (
          <HRCandidateSelectionView onBackToDashboard={() => navigateTo("home")} healthData={healthData} />
        )}
      </div>

      <footer className="global-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="footer-mark"><GraduationCap size={18} /></span>
            <strong>Career Intelligence Platform</strong>
          </div>
          <div className="footer-text">
            <p>
              Comprehensive Career Development and Recruitment Framework · Final Year Research Project – 2026
            </p>
            <p className="footer-tagline">
              Responsible AI &bull; Explainability &bull; Career Development
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
