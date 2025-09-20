import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";

const menuItems = [
  { label: "Home", link: "/" },
  { label: "Internship Finder", link: "/second" },
  { label: "About", link: "/about" },
  { label: "Services", link: "/services" },
  { label: "Contact", link: "/contact" },
];

const StaggeredMenu = () => {
  const [isOpen, setIsOpen] = useState(false);

  const containerVariants = {
    open: {
      transition: { staggerChildren: 0.15 },
    },
    closed: {
      transition: { staggerChildren: 0.05, staggerDirection: -1 },
    },
  };

  const itemVariants = {
    open: { opacity: 1, y: 0 },
    closed: { opacity: 0, y: 20 },
  };

  return (
    <div style={{ position: "absolute", top: 20, left: 20, zIndex: 1000 }}>
      {/* Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          padding: "0.8em 1.2em",
          background: "#0de3e3",
          color: "#000",
          fontWeight: "bold",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          boxShadow: "0 0 10px rgba(0,0,0,0.4)",
        }}
      >
        {isOpen ? "Close" : "Menu"}
      </button>

      {/* Menu Items */}
      <AnimatePresence>
        {isOpen && (
          <motion.ul
            initial="closed"
            animate="open"
            exit="closed"
            variants={containerVariants}
            style={{
              listStyle: "none",
              margin: "1em 0 0 0",
              padding: 0,
              background: "#111",
              borderRadius: "8px",
              boxShadow: "0 0 15px rgba(0,0,0,0.5)",
              overflow: "hidden",
            }}
          >
            {menuItems.map((item) => (
              <motion.li
                key={item.label}
                variants={itemVariants}
                style={{
                  borderBottom: "1px solid #333",
                }}
              >
                <Link
                  to={item.link}
                  style={{
                    display: "block",
                    padding: "0.8em 1.2em",
                    color: "#fff",
                    textDecoration: "none",
                    transition: "all 0.3s ease",
                  }}
                  onClick={() => setIsOpen(false)}
                >
                  {item.label}
                </Link>
              </motion.li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
};

export default StaggeredMenu;
