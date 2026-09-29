import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import RegisterAssessPage from './pages/RegisterAssessPage';
import CandidateDashboardPage from './pages/CandidateDashboardPage';
import JobRolesPage from './pages/JobRolesPage';
import HistoryPage from './pages/HistoryPage';
import './index.css';
import './styles.css';

const DEFAULT_ROLES = [
  {
    roleId: "full_stack_mern",
    roleName: "Full Stack MERN Developer",
    category: "Software Engineering",
    requiredSkills: [{ name: "React" }, { name: "Node.js" }, { name: "MongoDB" }, { name: "Express.js" }, { name: "JavaScript" }],
    preferredSkills: [{ name: "Docker" }, { name: "TypeScript" }, { name: "Redux" }]
  },
  {
    roleId: "backend_python",
    roleName: "Backend Python Engineer",
    category: "Software Engineering",
    requiredSkills: [{ name: "Python" }, { name: "FastAPI" }, { name: "PostgreSQL" }, { name: "REST APIs" }],
    preferredSkills: [{ name: "Docker" }, { name: "Redis" }, { name: "Celery" }]
  },
  {
    roleId: "frontend_react",
    roleName: "Frontend React Engineer",
    category: "Web Development",
    requiredSkills: [{ name: "React" }, { name: "JavaScript" }, { name: "TypeScript" }, { name: "HTML5/CSS3" }],
    preferredSkills: [{ name: "Next.js" }, { name: "Redux" }, { name: "Tailwind CSS" }]
  },
  {
    roleId: "devops_cloud",
    roleName: "DevOps & Cloud Engineer",
    category: "Infrastructure",
    requiredSkills: [{ name: "Docker" }, { name: "Kubernetes" }, { name: "CI/CD Pipelines" }, { name: "Linux" }],
    preferredSkills: [{ name: "Terraform" }, { name: "AWS" }, { name: "Prometheus" }]
  },
  {
    roleId: "data_engineer",
    roleName: "Data Engineer",
    category: "Data Engineering",
    requiredSkills: [{ name: "Python" }, { name: "SQL" }, { name: "Apache Spark" }, { name: "Data Pipelines" }],
    preferredSkills: [{ name: "Airflow" }, { name: "Kafka" }, { name: "Snowflake" }]
  }
];

export default function App() {
  const [currentCandidate, setCurrentCandidate] = useState(() => {
    try {
      const saved = localStorage.getItem('currentCandidate');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState(() => {
    const savedTab = localStorage.getItem('activeTab');
    const savedCand = localStorage.getItem('currentCandidate');
    if (savedTab === 'dashboard' && !savedCand) {
      return 'register';
    }
    return savedTab || 'register';
  });

  const [roles, setRoles] = useState(DEFAULT_ROLES);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    localStorage.setItem('activeTab', tab);
  };

  useEffect(() => {
    // Try Node backend first, fallback to FastAPI directly
    axios.get('/api/roles')
      .then(resp => {
        const standard = resp.data.standardRoles || resp.data.roles || [];
        const custom = resp.data.customRoles || [];
        if (standard.length > 0 || custom.length > 0) {
          setRoles([...standard, ...custom]);
        }
      })
      .catch(() => {
        // Direct FastAPI fallback
        axios.get('http://127.0.0.1:8000/api/roles')
          .then(resp => {
            const standard = resp.data.standardRoles || resp.data.roles || [];
            if (standard.length > 0) setRoles(standard);
          })
          .catch(err => console.warn('Using default ESCO job roles:', err.message));
      });
  }, []);

  const handleVerificationSuccess = (candidateRecord) => {
    setCurrentCandidate(candidateRecord);
    setActiveTab('dashboard');
    try {
      localStorage.setItem('currentCandidate', JSON.stringify(candidateRecord));
      localStorage.setItem('activeTab', 'dashboard');
    } catch (e) {}
  };

  const handleSelectCandidateFromHistory = (candidateRecord) => {
    setCurrentCandidate(candidateRecord);
    setActiveTab('dashboard');
    try {
      localStorage.setItem('currentCandidate', JSON.stringify(candidateRecord));
      localStorage.setItem('activeTab', 'dashboard');
    } catch (e) {}
  };

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        hasActiveCandidate={!!currentCandidate}
      />

      <div className="app-main-content">
        <main className="page-container">
          {activeTab === 'register' && (
            <RegisterAssessPage
              roles={roles}
              onVerificationSuccess={handleVerificationSuccess}
            />
          )}

          {activeTab === 'dashboard' && (
            <CandidateDashboardPage
              candidateRecord={currentCandidate}
              onBackToRegister={() => handleTabChange('register')}
            />
          )}

          {activeTab === 'roles' && (
            <JobRolesPage roles={roles} />
          )}

          {activeTab === 'history' && (
            <HistoryPage onSelectCandidate={handleSelectCandidateFromHistory} />
          )}
        </main>
      </div>
    </div>
  );
}
