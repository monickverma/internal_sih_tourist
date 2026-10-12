// Base URL of the recommender API.
// Production (Vercel): defaults to the relative "/api" path served by api/index.py
// in the same deployment. Override with VITE_API_BASE (e.g. http://127.0.0.1:8000/api).
export const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");
