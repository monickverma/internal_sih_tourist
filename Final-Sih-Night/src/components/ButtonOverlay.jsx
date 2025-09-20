import React, { useEffect, useState } from "react";

const ButtonOverlay = ({ onClick }) => {
  const [showButton, setShowButton] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowButton(true), 2200); // delay after subtitle
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      style={{
        position: "absolute",
        top: "55%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        zIndex: 10,
      }}
    >
      <button
        style={{
          backgroundColor: "rgb(195, 142, 150)", // ✅ button background
          color: "rgb(6, 15, 49)", // ✅ dark navy text
          padding: "12px 24px",
          border: "none",
          borderRadius: "8px",
          fontSize: "1rem",
          fontWeight: "bold",
          cursor: "pointer",
          marginTop: "150px",
          boxShadow:
            "0 0 15px rgba(195,142,150,0.6), 0 0 30px rgba(195,142,150,0.4)",
          transition: "all 0.6s ease",
          opacity: showButton ? 1 : 0, // ✅ fade-in for button
        }}
        onMouseOver={(e) => {
          e.target.style.boxShadow =
            "0 0 25px rgba(195,142,150,1), 0 0 50px rgba(195,142,150,0.9)";
        }}
        onMouseOut={(e) => {
          e.target.style.boxShadow =
            "0 0 15px rgba(195,142,150,0.6), 0 0 30px rgba(195,142,150,0.4)";
        }}
        onClick={onClick} // ✅ trigger fade-out from App
      >
        Get Started
      </button>
    </div>
  );
};

export default ButtonOverlay;
