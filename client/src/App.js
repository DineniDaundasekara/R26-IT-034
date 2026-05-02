import React from "react";
import "./App.css";
import PredictorForm from "./components/PredictorForm";

function App() {
  return (
    <div style={{ padding: "20px" }}>
      <h1>Employability Prediction System</h1>
      <PredictorForm />
    </div>
  );
}

export default App;