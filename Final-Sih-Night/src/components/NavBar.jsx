import React from "react";
import "./Navbar.css";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="logo">InternAI</div>
      <ul className="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="/criteria">Criteria</a></li>
        <li><a href="/companies">Companies</a></li>
      </ul>
    </nav>
  );
};

export default Navbar;
