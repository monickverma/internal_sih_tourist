import React, { useEffect, useState } from "react";

const TextOverlay = () => {
  const [showNamaste, setShowNamaste] = useState(false);
  const [showSubtitle, setShowSubtitle] = useState(false);

  useEffect(() => {
    // Fade-in sequence
    setTimeout(() => setShowNamaste(true), 200);   // Namaste first
    setTimeout(() => setShowSubtitle(true), 1200); // Subtitle after delay
  }, []);

  return (
    <div
      style={{
        position: "absolute",
        top: "30%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        color: "white",
        zIndex: 10,
        textAlign: "center",
        fontFamily: "'Unbounded', sans-serif", // ✅ Unbounded everywhere
      }}
    >
      {/* Hindi Namaste with Unbounded font */}
      <p
        style={{
          fontWeight: "700", // ✅ Bold
          fontStyle: "italic", // ✅ Italics
          fontSize: "4.5rem",
          margin: 0,
          letterSpacing: "4px",
          transform: "scaleX(1.1)",
          opacity: showNamaste ? 1 : 0,
          transition: "opacity 2s ease, text-shadow 0.4s ease",
          color: "rgb(195, 142, 150)", // ✅ pink accent
        }}
        onMouseOver={(e) => {
          e.target.style.textShadow =
            "0 0 25px rgba(192,192,192,1), 0 0 50px rgba(192,192,192,0.9)";
        }}
        onMouseOut={(e) => {
          e.target.style.textShadow = "none";
        }}
      >
        नमस्ते.
      </p>

      {/* Subtitle with Unbounded font */}
      <p
        style={{
          margin: "20px 0 0 0",
          fontSize: "1.8rem",
          fontWeight: "400",
          opacity: showSubtitle ? 1 : 0,
          transition: "opacity 2s ease, text-shadow 0.4s ease",
        }}
        onMouseOver={(e) => {
          e.target.style.textShadow =
            "0 0 15px rgba(192,192,192,1), 0 0 30px rgba(192,192,192,0.7)";
        }}
        onMouseOut={(e) => {
          e.target.style.textShadow = "none";
        }}
      >
        Your pathway to perfect internships
      </p>
    </div>
  );
};

export default TextOverlay;
