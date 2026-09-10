import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import API_BASE_URL from "../../config";


function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage("");

    const cleanEmail = email.trim().toLowerCase();
    const cleanPassword = password.trim();

    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        email: cleanEmail,
        password: cleanPassword,
      });

      const token = response.data.access_token || response.data.token;
      const role  = response.data.role;

      if (token) {
        localStorage.setItem("token", token);
      }
      if (role) {
        localStorage.setItem("role", role);
      }

      // Only proceed to dashboard if the backend confirms this is a "user" account
      if (role && role !== "user") {
        setMessage(`Access denied. This portal is for users only. Your role: ${role}`);
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        return;
      }

      navigate("/user/dashboard");
    } catch (error) {
      if (error?.code === "ERR_NETWORK" || !error?.response) {
        setMessage("Backend server is not running. Please start the API server first.");
        return;
      }

      const data = error?.response?.data;
      const errorMessage =
        (typeof data === "string" && data) ||
        data?.detail ||
        data?.message ||
        data?.msg ||
        "Login failed. Please check your credentials.";

      setMessage(errorMessage);
    }
  };

  const fillDemoCredentials = () => {
    setEmail("user@mitra.com");
    setPassword("User@123");
    setMessage("");
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-6">

      <div className="w-full max-w-md">

        <div className="text-center mb-8">

          <button
            onClick={() => navigate("/roles")}
            className="text-slate-500 hover:text-slate-300 text-sm mb-6 inline-block transition"
          >
            ← Back to Role Selection
          </button>

          <div className="text-5xl mb-4">
            ⚖️
          </div>

          <h1 className="text-4xl font-bold text-white">
            MITRA METROLOGY
          </h1>

          <p className="text-slate-400 mt-3">
            User Sign In
          </p>

        </div>

        <form
          onSubmit={handleLogin}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
        >

          <div className="flex items-center justify-between p-3 bg-blue-950/40 border border-blue-800/40 rounded-xl text-xs text-blue-300 mb-5">
            <div>
              <span className="font-semibold">Demo Citizen:</span>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">user@mitra.com / User@123</div>
            </div>
            <button
              type="button"
              onClick={fillDemoCredentials}
              className="px-2.5 py-1 bg-blue-800/60 hover:bg-blue-700/60 text-white rounded-lg text-[11px] font-medium transition"
            >
              Fill Demo
            </button>
          </div>

          <label className="block text-slate-300 mb-2">
            Email
          </label>

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@mitra.com"
            required
            className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 mb-5 outline-none focus:border-blue-500"
          />

          <label className="block text-slate-300 mb-2">
            Password
          </label>

          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="User@123"
            required
            className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 mb-6 outline-none focus:border-blue-500"
          />

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-semibold transition"
          >
            Login
          </button>

          {message && (
            <p className="text-red-400 text-center mt-4">
              {message}
            </p>
          )}

        </form>

        <p className="text-slate-400 text-center mt-6">
          Don't have an account?{" "}
          <button
            onClick={() => navigate("/user/register")}
            className="text-blue-400 hover:text-blue-300 font-semibold underline underline-offset-2 transition"
          >
            Sign Up
          </button>
        </p>

      </div>

    </div>
  );
}

export default Login;