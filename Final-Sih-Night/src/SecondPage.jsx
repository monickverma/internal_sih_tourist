import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Stepper from "./components/Stepper";
import "./SecondPage.css";

const SecondPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [fadeClass, setFadeClass] = useState("fade-in");

  useEffect(() => {
    setFadeClass("fade-in");
    return () => setFadeClass("fade-out");
  }, []);

  const handleComplete = async (formData) => {
    try {
      setLoading(true);

      const response = await fetch("http://127.0.0.1:8000/recommend?top_k=5", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (response.ok) {
        console.log("✅ Recommendations:", result);

        // ✅ Fade out before navigating
        setFadeClass("fade-out");
        setTimeout(
          () =>
            navigate("/third", {
              state: { recommendations: result.recommendations },
            }),
          500 // match CSS animation time
        );
      } else {
        alert("❌ Failed: " + (result.detail || "Unknown error"));
      }
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      alert("❌ Error calling backend");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`second-page ${fadeClass}`}>
      <div className="second-page-logo">InternAI</div>
      <div className="stepper-wrapper">
        <Stepper onComplete={handleComplete} />
      </div>
      {loading && <p style={{ color: "white" }}>⏳ Loading recommendations...</p>}
    </div>
  );
};

export default SecondPage;
