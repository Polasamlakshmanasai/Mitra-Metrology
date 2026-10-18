import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Scale, AlertCircle, ArrowLeft, Mail, Lock, User, CheckCircle } from "lucide-react";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getRegistrationError = (error) => {
    if (error?.code === "ERR_NETWORK" || !error?.response) {
      return "Connection error. Please check your network or server status.";
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
    setIsSubmitting(true);
    setMessage("");

    try {
      await axios.post(`${API_BASE_URL}/auth/register`, {
        name,
        username: name,
        email,
        password,
      });

      setIsError(false);
      setMessage("Account registered successfully. Redirecting to login...");

      setTimeout(() => {
        navigate("/user/login");
      }, 1500);
    } catch (error) {
      setIsError(true);
      setMessage(getRegistrationError(error));
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      
      {/* ── Top Government Header Strip ───────────────────────────── */}
      <div className="bg-[#174A7E] text-white text-xs py-2 px-4 sm:px-8 border-b border-[#133D68]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold tracking-wide">LEGAL METROLOGY COMPLIANCE PORTAL</span>
            <span className="hidden sm:inline text-blue-200">|</span>
            <span className="hidden sm:inline text-blue-100">Citizen Registration</span>
          </div>
          <Link to="/user/login" className="text-blue-100 hover:text-white flex items-center gap-1 text-[11px]">
            <ArrowLeft size={12} /> Back to Sign In
          </Link>
        </div>
      </div>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-10 flex flex-col justify-center">
        <div className="border border-[#D5DCE5] rounded shadow-sm overflow-hidden bg-white grid md:grid-cols-12">
          
          {/* Left Side: Information */}
          <div className="md:col-span-5 bg-[#F5F7FA] p-8 sm:p-10 border-b md:border-b-0 md:border-r border-[#D5DCE5] flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded bg-[#174A7E] text-white flex items-center justify-center mb-6 shadow-sm">
                <Scale size={26} />
              </div>
              <h2 className="text-2xl font-bold text-[#183153] tracking-tight">
                Create Account
              </h2>
              <p className="text-xs font-semibold text-[#174A7E] uppercase tracking-wider mt-1">
                Citizen Portal Registration
              </p>
              <p className="text-sm text-[#475569] mt-4 leading-relaxed">
                Register a citizen account to track package verifications, download formal inspection reports, and file consumer grievances under Legal Metrology rules.
              </p>

              <div className="mt-8 space-y-3 pt-6 border-t border-[#D5DCE5]">
                <div className="flex items-start gap-2.5 text-xs text-[#64748B]">
                  <CheckCircle size={15} className="text-[#15803D] mt-0.5 shrink-0" />
                  <span>Personal inspection audit log access</span>
                </div>
                <div className="flex items-start gap-2.5 text-xs text-[#64748B]">
                  <CheckCircle size={15} className="text-[#15803D] mt-0.5 shrink-0" />
                  <span>Automated FSSAI and Legal Metrology checks</span>
                </div>
                <div className="flex items-start gap-2.5 text-xs text-[#64748B]">
                  <CheckCircle size={15} className="text-[#15803D] mt-0.5 shrink-0" />
                  <span>Direct grievance tracking with authorities</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-[#D5DCE5] text-xs text-[#64748B]">
              <span>Already registered? </span>
              <Link to="/user/login" className="text-[#174A7E] font-semibold hover:underline">
                Sign In →
              </Link>
            </div>
          </div>

          {/* Right Side: Registration Form */}
          <div className="md:col-span-7 p-8 sm:p-10 bg-white flex flex-col justify-center">
            
            <div className="mb-6">
              <h3 className="text-xl font-bold text-[#183153]">Citizen Registration</h3>
              <p className="text-xs text-[#64748B] mt-1">Provide your details to establish a verified account</p>
            </div>

            {message && (
              <div
                className={`mb-6 p-3.5 rounded text-xs border flex items-start gap-2 ${
                  isError
                    ? "bg-[#FEE2E2] border-[#FECACA] text-[#B91C1C]"
                    : "bg-[#DCFCE7] border-[#BBF7D0] text-[#15803D]"
                }`}
              >
                {isError ? (
                  <AlertCircle size={16} className="mt-0.5 shrink-0" />
                ) : (
                  <CheckCircle size={16} className="mt-0.5 shrink-0" />
                )}
                <span>{message}</span>
              </div>
            )}

            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                    <User size={16} />
                  </div>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    placeholder="Enter your full name"
                    className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                  />
                </div>
              </div>

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
                    placeholder="name@example.com"
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
                    placeholder="Minimum 8 characters"
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
                  {isSubmitting ? "Creating Account..." : "Create Citizen Account"}
                </button>
              </div>
            </form>

            <div className="mt-6 pt-5 border-t border-[#D5DCE5] text-center">
              <span className="text-xs text-[#64748B]">Already have an account? </span>
              <Link to="/user/login" className="text-xs text-[#174A7E] font-semibold hover:underline">
                Sign In Here
              </Link>
            </div>

          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}

export default Register;