import React from "react";
import HRCandidateSelectionView from "./views/HRCandidateSelectionView.jsx";
import "./styles.css";
import "./styles/hrCandidates.css";

export default function App() {
  return (
    <div className="root-app-layout">
      <HRCandidateSelectionView />
    </div>
  );
}
