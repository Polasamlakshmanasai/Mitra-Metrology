import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { ShieldCheck, AlertCircle, ArrowLeft, UserCircle, Key, Lock, CheckCircle } from "lucide-react";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

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

    const cleanId = officerId.trim();
    const cleanPassword = password.trim();

    try {
      const email = cleanId.includes("@") ? cleanId.toLowerCase() : `${cleanId.toLowerCase()}@mitra.gov.in`;
      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password: cleanPassword,
      });

      const token = res.data.access_token || res.data.token;
      const role = res.data.role;

      if (role !== "officer") {
        setMessage("403 Officer Access Required: This account does not possess inspector privileges.");
        setIsSubmitting(false);
        return;
      }

      if (token) {
        localStorage.setItem("token", token);
      }
      localStorage.setItem("role", "officer");
      navigate("/officer/dashboard");
    } catch (err) {
      if (err?.code === "ERR_NETWORK" || !err?.response) {
        setMessage(`Cannot reach API server at ${API_BASE_URL}. Ensure backend service is running.`);
      } else {
        const detail = err?.response?.data?.detail || "Invalid officer badge ID or password.";
        setMessage(detail);
      }
      setIsSubmitting(false);
    }
  };

  const fillDemoCredentials = () => {
    setOfficerId("officer_22472@mitra.gov.in");
    setPassword("Officer@123");
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
            <span className="hidden sm:inline text-blue-100">Official Regulatory Inspector Console</span>
          </div>
          <Link to="/roles" className="text-blue-100 hover:text-white flex items-center gap-1 text-[11px]">
            <ArrowLeft size={12} /> Portal Selection
          </Link>
        </div>
      </div>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-10 flex flex-col justify-center">
        <div className="border border-[#D5DCE5] rounded shadow-sm overflow-hidden bg-white grid md:grid-cols-12">
          
          {/* Left Side: Regulatory Notice (Light Grey Background) */}
          <div className="md:col-span-5 bg-[#F5F7FA] p-8 sm:p-10 border-b md:border-b-0 md:border-r border-[#D5DCE5] flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded bg-[#174A7E] text-white flex items-center justify-center mb-6 shadow-sm">
                <ShieldCheck size={26} />
              </div>
              <h2 className="text-2xl font-bold text-[#183153] tracking-tight">
                Inspector Console
              </h2>
              <p className="text-xs font-semibold text-[#174A7E] uppercase tracking-wider mt-1">
                Legal Metrology Department
              </p>
              <p className="text-sm text-[#475569] mt-4 leading-relaxed">
                Authorized regulatory officer access for conducting statutory inspections, verifying package declarations, reviewing violation evidence, and rendering official compliance determinations.
              </p>

              <div className="mt-8 p-4 bg-white rounded border border-[#D5DCE5] text-xs text-[#64748B] space-y-2">
                <div className="font-semibold text-[#183153] flex items-center gap-1.5">
                  <Lock size={13} className="text-[#174A7E]" />
                  Authorized Access Notice
                </div>
                <p className="leading-relaxed">
                  All inspections, review actions, and field modifications are logged with officer timestamp and credentials for statutory audit trails.
                </p>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-[#D5DCE5] text-xs text-[#64748B]">
              <span>Citizen access? </span>
              <Link to="/user/login" className="text-[#174A7E] font-semibold hover:underline">
                Citizen Portal Login →
              </Link>
            </div>
          </div>

          {/* Right Side: Officer Login Form */}
          <div className="md:col-span-7 p-8 sm:p-10 bg-white flex flex-col justify-center">
            
            <div className="mb-6">
              <h3 className="text-xl font-bold text-[#183153]">Officer Authentication</h3>
              <p className="text-xs text-[#64748B] mt-1">Enter your officer badge ID / government email to proceed</p>
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
                  Officer ID / Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                    <UserCircle size={16} />
                  </div>
                  <input
                    type="text"
                    value={officerId}
                    onChange={(e) => setOfficerId(e.target.value)}
                    required
                    placeholder="officer_22472@mitra.gov.in"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Official Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                    <Key size={16} />
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
                  className="w-full py-2.5 px-4 bg-[#174A7E] hover:bg-[#133D68] text-white text-sm font-semibold rounded shadow-sm transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                >
                  <ShieldCheck size={16} />
                  {isSubmitting ? "Authenticating..." : "Sign In to Inspector Console"}
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
                <span>Fill Demo Officer Credentials</span>
              </button>

              <Link
                to="/roles"
                className="text-xs text-[#64748B] hover:text-[#183153] font-medium hover:underline"
              >
                ← Back to Roles
              </Link>
            </div>

          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}

export default OfficerLogin;
