import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./Thirdpage.css";

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
              key={rec.id ?? index}
              className="recommendation-card"
              style={{ animationDelay: `${index * 0.2}s` }} // ✅ staggered delay
            >
              <h2>{rec.JobTitle}</h2>
              <p>
                <strong>Company:</strong> {rec.CompanyName}
              </p>
              <p>
                <strong>Location:</strong>{" "}
                {rec.Cities && rec.Cities !== rec.States
                  ? `${rec.Cities}, ${rec.States}`
                  : rec.States}
              </p>
              <p>
                <strong>Type:</strong> {rec.JobType}
              </p>
              {rec.Stipend && (
                <p>
                  <strong>Stipend:</strong> {rec.Stipend}
                  {rec.Duration ? ` · ${rec.Duration}` : ""}
                </p>
              )}
              <p>
                <strong>Match Score:</strong>{" "}
                <span className="match-score">
                  {(rec.match_score * 100).toFixed(2)}%
                </span>
              </p>
              {rec.reasons?.length > 0 && (
                <div className="why">
                  <strong>Why this match</strong>
                  <ul>
                    {rec.reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}
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
