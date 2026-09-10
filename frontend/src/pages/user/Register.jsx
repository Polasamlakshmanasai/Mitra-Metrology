import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

import API_BASE_URL from "../../config";


function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  const getRegistrationError = (error) => {
    if (error?.code === "ERR_NETWORK" || !error?.response) {
      return "Backend server is not running. Please start the API server first.";
    }

    const data = error?.response?.data;

    if (!data) return "Registration failed";

    if (typeof data === "string") return data;

    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;

      if (Array.isArray(data.detail)) {
        const firstItem = data.detail[0];
        return firstItem?.msg || firstItem?.message || "Registration failed";
      }

      return data.detail.msg || data.detail.message || "Registration failed";
    }

    return data.msg || data.message || data.error || "Registration failed";
  };

  const handleRegister = async (e) => {
    e.preventDefault();

    try {
      await axios.post(`${API_BASE_URL}/auth/register`, {
        name,
        username: name,
        email,
        password,
      });

      setIsError(false);
      setMessage("Registration successful!");

      setTimeout(() => {
        navigate("/user/login");
      }, 1000);
    } catch (error) {
      setIsError(true);
      setMessage(getRegistrationError(error));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-6">

      <div className="w-full max-w-md">

        <div className="text-center mb-8">

          <button
            onClick={() => navigate("/user/login")}
            className="text-slate-500 hover:text-slate-300 text-sm mb-6 inline-block transition"
          >
            ← Back to Sign In
          </button>

          <div className="text-5xl mb-4">
            ⚖️
          </div>

          <h1 className="text-4xl font-bold text-white">
            MITRA METROLOGY
          </h1>

          <p className="text-slate-400 mt-3">
            Create your account
          </p>

        </div>

        <form
          onSubmit={handleRegister}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
        >

          <label className="block text-slate-300 mb-2">
            Name
          </label>

          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            required
            className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 mb-5 outline-none focus:border-blue-500"
          />

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
            placeholder="Enter your password"
            required
            className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 mb-6 outline-none focus:border-blue-500"
          />

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-semibold transition"
          >
            Register
          </button>

          {message && (
            <p className={`text-center mt-4 ${isError ? "text-red-400" : "text-green-400"}`}>
              {message}
            </p>
          )}

        </form>

        <p className="text-slate-400 text-center mt-6">
          Already have an account?{" "}
          <button
            onClick={() => navigate("/user/login")}
            className="text-blue-400 hover:text-blue-300 font-semibold underline underline-offset-2 transition"
          >
            Sign In
          </button>
        </p>

      </div>

    </div>
  );
}

export default Register;