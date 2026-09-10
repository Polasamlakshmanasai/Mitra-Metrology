import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

function OfficerLogin() {
  const navigate = useNavigate();

  const [officerId, setOfficerId] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage("");

    try {
      const email = officerId.includes("@") ? officerId : `${officerId}@mitra.gov.in`;
      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password,
      });

      const token = res.data.access_token || res.data.token;
      const role = res.data.role;

      if (role !== "officer") {
        setMessage("403 Officer access required: This account does not possess inspector privileges.");
        return;
      }

      if (token) {
        localStorage.setItem("token", token);
      }
      localStorage.setItem("role", "officer");
      navigate("/officer/dashboard");
    } catch (err) {
      const detail = err?.response?.data?.detail || "Invalid officer badge or password.";
      setMessage(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-emerald-950 border border-emerald-800/60 flex items-center justify-center text-3xl mx-auto mb-4">
            🧑‍💼
          </div>

          <h1 className="text-3xl font-extrabold text-white">
            LEGAL METROLOGY
          </h1>
          <p className="text-emerald-400 font-semibold text-sm mt-1">
            Officer & Inspector Portal
          </p>
          <p className="text-slate-400 text-xs mt-2">
            Government of India • Ministry of Consumer Affairs
          </p>
        </div>

        <form
          onSubmit={handleLogin}
          className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-5"
        >
          {message && (
            <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 rounded-xl text-xs">
              ⚠️ {message}
            </div>
          )}

          <div>
            <label className="block text-slate-300 text-xs font-semibold mb-2">
              Badge / Officer Email
            </label>
            <input
              type="text"
              required
              value={officerId}
              onChange={(e) => setOfficerId(e.target.value)}
              placeholder="officer@mitra.gov.in"
              className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-semibold mb-2">
              Security PIN / Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-bold transition shadow-lg shadow-emerald-600/20 text-sm"
          >
            {isSubmitting ? "Authenticating..." : "Access Inspector Portal →"}
          </button>

          <div className="pt-2 text-center">
            <Link to="/roles" className="text-xs text-slate-400 hover:text-white transition">
              ← Switch Role
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

export default OfficerLogin;
