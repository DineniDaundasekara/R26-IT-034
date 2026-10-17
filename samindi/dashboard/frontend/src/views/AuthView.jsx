import { useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  FileText,
  GraduationCap,
  Loader2,
  Lock,
  Mail,
  Mic,
  Sparkles,
  UserRound,
} from "lucide-react";
import { loginAccount, registerAccount } from "../authApi.js";

const DEMO = {
  email: "demo@pathready.ai",
  password: "PathReady2026",
};

function getInitialMode() {
  return window.location.pathname.toLowerCase().includes("register") ? "register" : "login";
}

export default function AuthView({ onAuthenticated }) {
  const [mode, setMode] = useState(getInitialMode);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const isRegister = mode === "register";

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    window.history.pushState({}, "", nextMode === "register" ? "/register" : "/login");
  }

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    if (error) setError("");
  }

  function fillDemo() {
    setMode("login");
    setForm((current) => ({
      ...current,
      email: DEMO.email,
      password: DEMO.password,
    }));
    setError("");
    window.history.pushState({}, "", "/login");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const email = form.email.trim();
    const password = form.password;
    const fullName = form.fullName.trim();

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    if (isRegister) {
      if (fullName.length < 2) {
        setError("Please enter your full name.");
        return;
      }
      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return;
      }
      if (password !== form.confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    setLoading(true);
    try {
      const user = isRegister
        ? await registerAccount({ fullName, email, password })
        : await loginAccount({ email, password });
      onAuthenticated(user);
    } catch (submitError) {
      setError(submitError.message || "Authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <aside className="auth-brand-panel">
        <div className="auth-brand-top">
          <div className="brand-logo-mark auth-logo">
            <GraduationCap size={26} />
          </div>
          <div>
            <p className="auth-kicker">Final-year research platform</p>
            <h1>Career Intelligence Platform</h1>
            <p className="auth-brand-copy">
              Comprehensive Career Development and Recruitment Framework — interview
              readiness, career path guidance, behaviour-aware career simulation, and
              career safety analysis in one professional workspace.
            </p>
          </div>
        </div>

        <ul className="auth-highlights">
          <li>
            <span className="auth-highlight-icon">
              <Mic size={18} />
            </span>
            <div>
              <strong>Interview readiness & career path guidance</strong>
              <p>Spoken communication diagnostics, STAR coaching, and CV-based career path evaluation.</p>
            </div>
          </li>
          <li>
            <span className="auth-highlight-icon teal">
              <FileText size={18} />
            </span>
            <div>
              <strong>Career safety & industry stability</strong>
              <p>Explainable career risk estimation with a personalized resilience action plan.</p>
            </div>
          </li>
          <li>
            <span className="auth-highlight-icon teal">
              <Sparkles size={18} />
            </span>
            <div>
              <strong>Behaviour-aware career simulation</strong>
              <p>Explainable employability prediction from internship experience, competence, and psychological capital.</p>
            </div>
          </li>
        </ul>
      </aside>

      <main className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-mode-tabs" role="tablist">
            <button
              type="button"
              className={!isRegister ? "active" : ""}
              onClick={() => switchMode("login")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={isRegister ? "active" : ""}
              onClick={() => switchMode("register")}
            >
              Create account
            </button>
          </div>

          <h2>{isRegister ? "Register for Career Intelligence" : "Welcome back"}</h2>
          <p className="auth-lede">
            {isRegister
              ? "Create your research workspace, then continue to the home page to open any of the four career intelligence modules."
              : "Sign in with your details to continue to the home page and access all research modules."}
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {isRegister && (
              <label className="auth-field">
                <span>Full name</span>
                <div className="auth-input-wrap">
                  <UserRound size={16} />
                  <input
                    autoComplete="name"
                    placeholder="e.g. Samindi Perera"
                    value={form.fullName}
                    onChange={(event) => updateField("fullName", event.target.value)}
                  />
                </div>
              </label>
            )}

            <label className="auth-field">
              <span>Email</span>
              <div className="auth-input-wrap">
                <Mail size={16} />
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="you@university.edu"
                  value={form.email}
                  onChange={(event) => updateField("email", event.target.value)}
                />
              </div>
            </label>

            <label className="auth-field">
              <span>Password</span>
              <div className="auth-input-wrap">
                <Lock size={16} />
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  placeholder={isRegister ? "At least 8 characters, letters and numbers" : "Enter your password"}
                  value={form.password}
                  onChange={(event) => updateField("password", event.target.value)}
                />
                <button
                  type="button"
                  className="auth-eye"
                  onClick={() => setShowPassword((value) => !value)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>

            {isRegister && (
              <label className="auth-field">
                <span>Confirm password</span>
                <div className="auth-input-wrap">
                  <Lock size={16} />
                  <input
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    placeholder="Re-enter your password"
                    value={form.confirmPassword}
                    onChange={(event) => updateField("confirmPassword", event.target.value)}
                  />
                </div>
              </label>
            )}

            {error && <p className="auth-error">{error}</p>}

            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? <Loader2 size={18} className="spin" /> : <ArrowRight size={18} />}
              <span>{isRegister ? "Create account and continue" : "Sign in and go to home"}</span>
            </button>
          </form>

          <div className="auth-demo-box">
            <CheckCircle2 size={16} />
            <div>
              <strong>Viva demonstration account</strong>
              <p>
                {DEMO.email} · {DEMO.password}
              </p>
              <button type="button" onClick={fillDemo}>
                Use demo details
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
