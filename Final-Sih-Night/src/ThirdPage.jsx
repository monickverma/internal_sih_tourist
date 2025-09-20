import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./ThirdPage.css";

const ThirdPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const recommendations = location.state?.recommendations || [];

  const [fadeClass, setFadeClass] = useState("fade-in");

  useEffect(() => {
    setFadeClass("fade-in");
    return () => setFadeClass("fade-out");
  }, []);

  const handleBack = () => {
    setFadeClass("fade-out");
    setTimeout(() => navigate("/"), 500);
  };

  return (
    <div className={`third-page ${fadeClass}`}>
      {/* ✅ Top-left logo */}
      <div className="third-page-logo">InternAI</div>

      <h1>Here are some internships tailored to you</h1>

      {recommendations.length === 0 ? (
        <p style={{ textAlign: "center" }}>No recommendations available.</p>
      ) : (
        <div className="recommendation-grid">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className="recommendation-card"
              style={{ animationDelay: `${index * 0.2}s` }} // ✅ staggered delay
            >
              <h2>{rec.JobTitle}</h2>
              <p>
                <strong>Company:</strong> {rec.CompanyName}
              </p>
              <p>
                <strong>Location:</strong> {rec.States}
              </p>
              <p>
                <strong>Type:</strong> {rec.JobType}
              </p>
              <p>
                <strong>Match Score:</strong>{" "}
                <span className="match-score">
                  {(rec.match_score * 100).toFixed(2)}%
                </span>
              </p>
            </div>
          ))}
        </div>
      )}

      <button onClick={handleBack} className="back-btn">
        ⬅ Back to Home
      </button>
    </div>
  );
};

export default ThirdPage;
