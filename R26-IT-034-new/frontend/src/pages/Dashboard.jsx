import Sidebar from "../components/Sidebar";
import "../styles/Dashboard.css";

function Dashboard() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <button className="menu-btn">☰</button>

          <div className="topbar-right">
            <span className="notification">🔔<small>3</small></span>
            <span className="date">📅 May 26, 2025</span>
            <span className="avatar">AD</span>
          </div>
        </header>

        <section className="hero-section">
          <div className="welcome-block">
            <h1>Welcome back, Admin User! 👋</h1>
            <p>Employability Factors Based Career Impact Prediction</p>

            <button className="start-btn">🚀 Start Prediction</button>
          </div>

          <div className="summary-cards">
            <article className="summary-card">
              <div className="card-icon blue">🗄️</div>
              <span className="info-dot">ⓘ</span>
              <p>Dataset</p>
              <h3>1000 Records</h3>
              <small>Latest version uploaded</small>
            </article>

            <article className="summary-card">
              <div className="card-icon purple">🔗</div>
              <span className="info-dot">ⓘ</span>
              <p>Model</p>
              <h3>XGBoost</h3>
              <small>Active final model</small>
            </article>

            {/* <article className="summary-card">
              <div className="card-icon green">📈</div>
              <span className="info-dot">ⓘ</span>
              <p>R² Score</p>
              <h3>0.7017</h3>
              <small>Model performance</small>
            </article> */}

            <article className="summary-card">
              <div className="card-icon orange">🏅</div>
              <span className="info-dot">ⓘ</span>
              <p>Latest Prediction</p>
              <h3>Medium</h3>
              <small>Latest predicted level</small>
            </article>
          </div>
        </section>

        <section className="dashboard-content-grid">
          <div className="workflow-card">
            <div className="workflow-header">
              <div>
                <h2>Prediction Workflow</h2>
                <p>Three key validated constructs drive employability prediction</p>
              </div>

              <button className="about-btn">ⓘ About the Model</button>
            </div>

            <div className="workflow-steps">
              <div className="step-circle blue-step">1</div>
              <div className="step-line"></div>
              <span className="arrow">›</span>
              <div className="step-line"></div>
              <div className="step-circle purple-step">2</div>
              <div className="step-line"></div>
              <span className="arrow">›</span>
              <div className="step-line"></div>
              <div className="step-circle green-step">3</div>
            </div>

            <div className="workflow-detail-cards">
              <article className="workflow-detail blue-border">
                <div className="workflow-icon blue-bg">💼</div>
                <h3>Internship Experience</h3>
                <p>
                  Practical exposure and learning through internship involvement.
                </p>

                <ul>
                  <li>Domain Relevance</li>
                  <li>Duration</li>
                  <li>Quality of Exposure</li>
                  <li>Learning & Reflection</li>
                  <li>Supervisor Feedback</li>
                </ul>
              </article>

              <article className="workflow-detail purple-border">
                <div className="workflow-icon purple-bg">🧠</div>
                <h3>Competence</h3>
                <p>
                  Skills, knowledge and abilities demonstrated by the individual.
                </p>

                <ul>
                  <li>Technical Skills</li>
                  <li>Problem Solving</li>
                  <li>Communication</li>
                  <li>Adaptability</li>
                  <li>Domain Knowledge</li>
                </ul>
              </article>

              <article className="workflow-detail green-border">
                <div className="workflow-icon green-bg">📊</div>
                <h3>Psychological Capital</h3>
                <p>
                  Positive psychological resources that influence performance.
                </p>

                <ul>
                  <li>Self-Efficacy</li>
                  <li>Optimism</li>
                  <li>Hope</li>
                  <li>Resilience</li>
                  <li>Confidence</li>
                </ul>
              </article>
            </div>

            <div className="workflow-note">
              ✨ These constructs are processed using the improved XGBoost model to
              predict employability outcomes.
            </div>
          </div>

          <aside className="latest-result-card">
            <div className="result-title-row">
              <h2>Latest Prediction Result</h2>
              <span>+ Live</span>
            </div>

            <div className="score-box">
              <p>Predicted Employability Score</p>
              <h1>3.92</h1>
              <small>out of 5.00</small>
              <div className="score-badge medium">Medium</div>
            </div>

            <div className="interpretation">
              <div className="interpret-icon">↗</div>
              <div>
                <h4>Score Interpretation</h4>
                <p>
                  The candidate shows moderate employability potential based on
                  the questionnaire-based factor analysis.
                </p>
              </div>
            </div>

            <div className="result-meta">
              <div>
                <span>Prediction ID</span>
                <strong>#PRD-2026-0001</strong>
              </div>

              <div>
                <span>Prediction Time</span>
                <strong>May 26, 2026 10:24 AM</strong>
              </div>

              <div>
                <span>Model Used</span>
                <strong>XGBoost Regression</strong>
              </div>

              <div>
                <span>R² Score</span>
                <strong>0.7017</strong>
              </div>
            </div>

            <button className="view-btn">📄 View Full Result</button>
          </aside>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;