import { UserCheck, LayoutDashboard, Briefcase, History } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, hasActiveCandidate }) {
  return (
    <header className="navbar">
      <div className="nav-container">
        <nav className="nav-links">
          <button
            className={`nav-link ${activeTab === 'register' ? 'active' : ''}`}
            onClick={() => setActiveTab('register')}
          >
            <UserCheck size={16} />
            Check Candidate
          </button>

          {hasActiveCandidate && (
            <button
              className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <LayoutDashboard size={16} />
              Candidate Dashboard
            </button>
          )}

          <button
            className={`nav-link ${activeTab === 'roles' ? 'active' : ''}`}
            onClick={() => setActiveTab('roles')}
          >
            <Briefcase size={16} />
            Job Roles
          </button>

          <button
            className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <History size={16} />
            Past Checks
          </button>
        </nav>
      </div>
    </header>
  );
}
