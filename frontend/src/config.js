// Central API configuration.
// In production, set VITE_API_URL as an environment variable on Render:
//   VITE_API_URL = https://mitra-metrology-api.onrender.com
// Locally it falls back to http://localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default API_BASE_URL;
