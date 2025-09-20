import React, { useRef, useEffect } from "react";

const Threads2 = ({ amplitude = 1, distance = 0, enableMouseInteraction = true }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const numLines = 20;
    const lineSpacing = height / numLines;
    let mouseX = width / 2;

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "#0a0f1e"; // ✅ dark blue background
      ctx.fillRect(0, 0, width, height);

      ctx.strokeStyle = "rgba(255, 105, 180, 0.8)"; // ✅ pink threads
      ctx.lineWidth = 1.5;

      for (let i = 0; i < numLines; i++) {
        ctx.beginPath();
        for (let x = 0; x < width; x += 10) {
          let y =
            i * lineSpacing +
            Math.sin((x + Date.now() / 200) / 50 + i) * 20 +
            Math.sin(x / 100) * amplitude * 20 +
            (mouseX / width - 0.5) * distance * 20;
          ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      requestAnimationFrame(draw);
    };

    draw();

    if (enableMouseInteraction) {
      window.addEventListener("mousemove", (e) => {
        mouseX = e.clientX;
      });
    }

    window.addEventListener("resize", () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    return () => {
      window.removeEventListener("mousemove", () => {});
      window.removeEventListener("resize", () => {});
    };
  }, [amplitude, distance, enableMouseInteraction]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1, // ✅ stays behind everything
      }}
    />
  );
};

export default Threads2;
