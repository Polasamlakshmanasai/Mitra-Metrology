// Central API configuration.
// Priority 1: VITE_API_URL env var set on Render (set this before building!)
// Priority 2: Your deployed Render backend URL (reliable fallback)
// Priority 3: localhost for local development
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV
    ? "http://localhost:8000"
    : "https://mitra-metrology-api.onrender.com");

export default API_BASE_URL;
