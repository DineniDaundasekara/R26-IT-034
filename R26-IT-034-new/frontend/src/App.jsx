import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Prediction from "./pages/Prediction";
import ResultsHistory from "./pages/ResultsHistory";
import ModelInfo from "./pages/ModelInfo";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/prediction" element={<Prediction />} />
        <Route path="/results" element={<ResultsHistory />} />
        <Route path="/model" element={<ModelInfo />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;