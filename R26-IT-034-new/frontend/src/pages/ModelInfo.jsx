import Sidebar from "../components/Sidebar";

function ModelInfo() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main">
        <h1>Model Information</h1>

        <div className="card">
          <h3>Algorithm</h3>
          <p>XGBoost Regressor</p>

          <h3>Evaluation Metrics</h3>
          <p>R²: 0.70</p>
          <p>MAE: 0.22</p>
          <p>RMSE: 0.32</p>

          <h3>Features</h3>
          <ul>
            <li>Internship Experience</li>
            <li>Competence</li>
            <li>Psychological Capital</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default ModelInfo;