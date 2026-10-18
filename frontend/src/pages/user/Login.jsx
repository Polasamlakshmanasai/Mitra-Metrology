import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Scale, AlertCircle, ArrowLeft, Mail, Lock, ShieldCheck, CheckCircle } from "lucide-react";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage("");
    setIsSubmitting(true);

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

      if (role && role !== "user") {
        setMessage(`Access denied. This portal is for citizens and consumers. Your role: ${role}`);
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        setIsSubmitting(false);
        return;
      }

      navigate("/user/dashboard");
    } catch (error) {
      if (error?.code === "ERR_NETWORK" || !error?.response) {
        setMessage("Connection error. Please check your network or server status.");
      } else {
        const data = error?.response?.data;
        setMessage(
          (typeof data === "string" && data) ||
          data?.detail ||
          data?.message ||
          data?.msg ||
          "Invalid email or password."
        );
      }
      setIsSubmitting(false);
    }
  };

  const fillDemoCredentials = () => {
    setEmail("user@mitra.com");
    setPassword("User@123");
    setMessage("");
  };

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      
      {/* ── Top Government Header Strip ───────────────────────────── */}
      <div className="bg-[#174A7E] text-white text-xs py-2 px-4 sm:px-8 border-b border-[#133D68]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold tracking-wide">LEGAL METROLOGY COMPLIANCE PORTAL</span>
            <span className="hidden sm:inline text-blue-200">|</span>
            <span className="hidden sm:inline text-blue-100">Citizen & Consumer Access Console</span>
          </div>
          <Link to="/roles" className="text-blue-100 hover:text-white flex items-center gap-1 text-[11px]">
            <ArrowLeft size={12} /> Portal Selection
          </Link>
        </div>
      </div>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-10 flex flex-col justify-center">
        <div className="border border-[#D5DCE5] rounded shadow-sm overflow-hidden bg-white grid md:grid-cols-12">
          
          {/* Left Side: Regulatory Information (Light Grey Background) */}
          <div className="md:col-span-5 bg-[#F5F7FA] p-8 sm:p-10 border-b md:border-b-0 md:border-r border-[#D5DCE5] flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded bg-[#174A7E] text-white flex items-center justify-center mb-6 shadow-sm">
                <Scale size={26} />
              </div>
              <h2 className="text-2xl font-bold text-[#183153] tracking-tight">
                Citizen Portal
              </h2>
              <p className="text-xs font-semibold text-[#174A7E] uppercase tracking-wider mt-1">
                Packaged Commodity Verification
              </p>
              <p className="text-sm text-[#475569] mt-4 leading-relaxed">
                Log in to inspect pre-packaged product labels, review OCR-extracted declarations, verify statutory compliance, and submit grievances.
              </p>

              <div className="mt-8 space-y-3 pt-6 border-t border-[#D5DCE5]">
                <div className="flex items-start gap-2.5 text-xs text-[#64748B]">
                  <CheckCircle size={15} className="text-[#15803D] mt-0.5 shrink-0" />
                  <span>Rule 6 Mandatory Declarations verification</span>
                </div>
                <div className="flex items-start gap-2.5 text-xs text-[#64748B]">
                  <CheckCircle size={15} className="text-[#15803D] mt-0.5 shrink-0" />
                  <span>Interactive field review & manual corrections</span>
                </div>
                <div className="flex items-start gap-2.5 text-xs text-[#64748B]">
                  <CheckCircle size={15} className="text-[#15803D] mt-0.5 shrink-0" />
                  <span>Official PDF Inspection Report generation</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-[#D5DCE5] text-xs text-[#64748B]">
              <span>Need officer access? </span>
              <Link to="/officer/login" className="text-[#174A7E] font-semibold hover:underline">
                Officer Login →
              </Link>
            </div>
          </div>

          {/* Right Side: Login Form (Pure White) */}
          <div className="md:col-span-7 p-8 sm:p-10 bg-white flex flex-col justify-center">
            
            <div className="mb-6">
              <h3 className="text-xl font-bold text-[#183153]">Sign In to Your Account</h3>
              <p className="text-xs text-[#64748B] mt-1">Enter your registered email and password to access services</p>
            </div>

            {message && (
              <div className="mb-6 p-3.5 bg-[#FEE2E2] border border-[#FECACA] rounded text-xs text-[#B91C1C] flex items-start gap-2">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <span>{message}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                    <Mail size={16} />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="user@mitra.com"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                    <Lock size={16} />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 px-4 bg-[#174A7E] hover:bg-[#133D68] text-white text-sm font-semibold rounded shadow-sm transition-colors disabled:opacity-60"
                >
                  {isSubmitting ? "Signing in..." : "Sign In to Portal"}
                </button>
              </div>
            </form>

            {/* Demo Credentials Helper */}
            <div className="mt-6 pt-5 border-t border-[#D5DCE5] flex items-center justify-between">
              <button
                type="button"
                onClick={fillDemoCredentials}
                className="text-xs text-[#174A7E] hover:text-[#133D68] font-medium hover:underline flex items-center gap-1"
              >
                <span>Fill Demo Citizen Credentials</span>
              </button>

              <Link
                to="/user/register"
                className="text-xs text-[#183153] hover:text-[#174A7E] font-medium hover:underline"
              >
                Register Account →
              </Link>
            </div>

          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}

export default Login;