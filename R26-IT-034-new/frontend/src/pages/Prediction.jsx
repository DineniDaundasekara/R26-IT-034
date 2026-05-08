import React, { useState } from "react";
import axios from "axios";

const Prediction = () => {
  const [sieValues, setSieValues] = useState(Array(14).fill(4));
  const [compValues, setCompValues] = useState(Array(10).fill(4));
  const [psyValues, setPsyValues] = useState(Array(14).fill(4));

  const [score, setScore] = useState(null);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(false);

  const average = (arr) => {
    const nums = arr.map(Number);
    return nums.reduce((a, b) => a + b, 0) / nums.length;
  };

  const handleChange = (type, index, value) => {
    if (type === "sie") {
      const updated = [...sieValues];
      updated[index] = Number(value);
      setSieValues(updated);
    }

    if (type === "comp") {
      const updated = [...compValues];
      updated[index] = Number(value);
      setCompValues(updated);
    }

    if (type === "psy") {
      const updated = [...psyValues];
      updated[index] = Number(value);
      setPsyValues(updated);
    }
  };

  const handlePredict = async () => {
    try {
      setLoading(true);

      const SIE_avg = average(sieValues);
      const Comp_avg = average(compValues);
      const PsyCap_avg = average(psyValues);

      const response = await axios.post("http://localhost:5000/api/predict", {
        SIE_avg,
        PsyCap_avg,
        Comp_avg,
      });

      setScore(response.data.score);
      setLevel(response.data.level);
    } catch (error) {
      console.error(error);
      alert("Prediction failed. Check backend and ML API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "Arial" }}>
      <aside style={{ width: "260px", background: "#08245c", color: "white", padding: "25px" }}>
        <h2>Employability Prediction System</h2>
        <p>Dashboard</p>
        <p>Prediction</p>
        <p>Results</p>
        <p>Model</p>
      </aside>

      <main style={{ flex: 1, padding: "30px", background: "#f6f8fb" }}>
        <h1>Employability Prediction System</h1>
        <p>Predict employability using item-level questionnaire responses.</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: "25px" }}>
          <div>
            <Section title="Internship Experience (SIE1–SIE14)" values={sieValues} type="sie" handleChange={handleChange} />
            <Section title="Competence (C1–C10)" values={compValues} type="comp" handleChange={handleChange} />
            <Section title="Psychological Capital (PsyCap1–PsyCap14)" values={psyValues} type="psy" handleChange={handleChange} />

            <button
              onClick={handlePredict}
              style={{
                padding: "15px 30px",
                background: "#2563eb",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontSize: "18px",
                cursor: "pointer",
              }}
            >
              {loading ? "Predicting..." : "Predict Employability"}
            </button>
          </div>

          <div style={{ background: "white", padding: "25px", borderRadius: "14px", boxShadow: "0 4px 15px #ddd" }}>
            <h2>Prediction Result</h2>

            {score === null ? (
              <p>No prediction yet.</p>
            ) : (
              <>
                <p>Predicted Employability Score</p>
                <h1 style={{ fontSize: "60px", color: "#2563eb" }}>{score}</h1>

                <h2 style={{ color: level === "High" ? "green" : level === "Medium" ? "orange" : "red" }}>
                  {level}
                </h2>

                <hr />

                <p><b>SIE Avg:</b> {average(sieValues).toFixed(2)}</p>
                <p><b>Competence Avg:</b> {average(compValues).toFixed(2)}</p>
                <p><b>PsyCap Avg:</b> {average(psyValues).toFixed(2)}</p>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

const Section = ({ title, values, type, handleChange }) => {
  return (
    <div style={{ background: "white", padding: "20px", marginBottom: "20px", borderRadius: "14px" }}>
      <h2>{title}</h2>

      {values.map((value, index) => (
        <div
          key={index}
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "10px",
            borderBottom: "1px solid #eee",
            paddingBottom: "8px",
          }}
        >
          <label>
            {type === "sie" && `SIE${index + 1}`}
            {type === "comp" && `C${index + 1}`}
            {type === "psy" && `PsyCap${index + 1}`}
          </label>

          <select
            value={value}
            onChange={(e) => handleChange(type, index, e.target.value)}
            style={{ padding: "6px", width: "90px" }}
          >
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
          </select>
        </div>
      ))}
    </div>
  );
};

export default Prediction;