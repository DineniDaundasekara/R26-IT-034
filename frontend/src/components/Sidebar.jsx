import React, { useState } from 'react';
import { 
  UserCheck, 
  LayoutDashboard, 
  Briefcase, 
  History, 
  Menu, 
  X 
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, hasActiveCandidate }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleNavClick = (tab) => {
    setActiveTab(tab);
    setIsMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Top Bar with Hamburger */}
      <div className="mobile-top-bar">
        <button 
          type="button"
          className="btn-mobile-menu"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          aria-label="Toggle Navigation"
        >
          {isMobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Backdrop for Mobile Drawer */}
      {isMobileOpen && (
        <div 
          className="sidebar-backdrop"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Component */}
      <aside className={`app-sidebar ${isMobileOpen ? 'mobile-open' : ''}`}>
        {/* Mobile Close Button (shown only on mobile viewports) */}
        <div className="sidebar-mobile-header">
          <button 
            type="button" 
            className="sidebar-close-btn"
            onClick={() => setIsMobileOpen(false)}
            aria-label="Close Navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Group */}
        <div className="sidebar-nav-container">
          <nav className="sidebar-nav-links">
            <button
              type="button"
              className={`sidebar-nav-item ${activeTab === 'register' ? 'active' : ''}`}
              onClick={() => handleNavClick('register')}
            >
              <div className="nav-item-icon-wrap">
                <UserCheck size={19} />
              </div>
              <span className="nav-item-text">Check Candidate</span>
            </button>

            {hasActiveCandidate && (
              <button
                type="button"
                className={`sidebar-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
                onClick={() => handleNavClick('dashboard')}
              >
                <div className="nav-item-icon-wrap">
                  <LayoutDashboard size={19} />
                </div>
                <span className="nav-item-text">Candidate Dashboard</span>
                <span className="sidebar-active-dot" />
              </button>
            )}

            <button
              type="button"
              className={`sidebar-nav-item ${activeTab === 'roles' ? 'active' : ''}`}
              onClick={() => handleNavClick('roles')}
            >
              <div className="nav-item-icon-wrap">
                <Briefcase size={19} />
              </div>
              <span className="nav-item-text">Job Roles</span>
            </button>

            <button
              type="button"
              className={`sidebar-nav-item ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => handleNavClick('history')}
            >
              <div className="nav-item-icon-wrap">
                <History size={19} />
              </div>
              <span className="nav-item-text">Past Checks</span>
            </button>
          </nav>
        </div>
      </aside>
    </>
  );
}
