import React from "react";
import Sidebar from "../components/Sidebar";
import "./Prediction.css";

function ResultsHistory() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="prediction-main">
        <header className="page-header">
          <h1>Results & History</h1>
          <p>View latest employability prediction results and model summary.</p>
        </header>

        <section className="top-stats">
          <article className="stat-card highlight">
            <p>Latest Score</p>
            <h3>3.92</h3>
            <span>Medium</span>
          </article>

          <article className="stat-card">
            <p>Model</p>
            <h3>XGBoost</h3>
            <span>Final Model</span>
          </article>

          <article className="stat-card">
            <p>R² Score</p>
            <h3>0.7017</h3>
            <span>Test Evaluation</span>
          </article>

          <article className="stat-card">
            <p>MAE</p>
            <h3>0.2288</h3>
            <span>Average Error</span>
          </article>
        </section>

        <section className="input-panel">
          <h3>Prediction History</h3>

          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "20px" }}>
            <thead>
              <tr>
                <th style={thStyle}>Date</th>
                <th style={thStyle}>Score</th>
                <th style={thStyle}>Level</th>
                <th style={thStyle}>Notes</th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td style={tdStyle}>Latest</td>
                <td style={tdStyle}>3.92</td>
                <td style={tdStyle}>Medium</td>
                <td style={tdStyle}>Prediction generated from questionnaire inputs.</td>
              </tr>

              <tr>
                <td style={tdStyle}>Previous Demo</td>
                <td style={tdStyle}>3.75</td>
                <td style={tdStyle}>Medium</td>
                <td style={tdStyle}>Demo record for presentation.</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}

const thStyle = {
  textAlign: "left",
  padding: "14px",
  background: "#eef2ff",
  color: "#0f172a",
};

const tdStyle = {
  padding: "14px",
  borderBottom: "1px solid #e5e7eb",
};

export default ResultsHistory;