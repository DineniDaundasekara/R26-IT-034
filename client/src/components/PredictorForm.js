import React, { useState } from "react";
import axios from "axios";

const sieFields = Array.from({ length: 14 }, (_, i) => `SIE${i + 1}`);
const compFields = Array.from({ length: 10 }, (_, i) => `C${i + 1}`);
const psyFields = Array.from({ length: 14 }, (_, i) => `PsyCap${i + 1}`);

const allFields = [...sieFields, ...compFields, ...psyFields];

const PredictorForm = () => {
  const initialState = {};
  allFields.forEach(field => {
    initialState[field] = 3;
  });

  const [formData, setFormData] = useState(initialState);
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: Number(e.target.value)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://localhost:5000/api/predict", formData);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Prediction failed");
    }
  };

  const renderFields = (fields, title) => (
    <div style={{ marginBottom: "20px" }}>
      <h3>{title}</h3>
      {fields.map(field => (
        <div key={field} style={{ marginBottom: "8px" }}>
          <label>{field}: </label>
          <select name={field} value={formData[field]} onChange={handleChange}>
            {[1,2,3,4,5].map(v => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );

  return (
    <div>
      <form onSubmit={handleSubmit}>
        {renderFields(sieFields, "Internship Experience")}
        {renderFields(compFields, "Competence")}
        {renderFields(psyFields, "Psychological Capital")}

        <button type="submit">Predict Employability</button>
      </form>

      {result && (
        <div style={{ marginTop: "20px", padding: "15px", border: "1px solid #ccc" }}>
          <h2>Prediction Result</h2>
          <p><strong>Predicted Score:</strong> {result.predictedScore}</p>
          <p><strong>Level:</strong> {result.level}</p>
        </div>
      )}
    </div>
  );
};

export default PredictorForm;