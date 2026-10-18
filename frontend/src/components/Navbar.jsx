import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Scale, FileText, History, AlertTriangle, LogOut, Camera, FileSearch, User, Menu, X, ShieldCheck } from "lucide-react";

function Navbar({ role = "user" }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user");
    navigate("/roles");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 bg-[#FFFFFF] shadow-sm">
      {/* ── Top Slim Government Strip ───────────────────────────── */}
      <div className="bg-[#174A7E] text-white text-[11px] sm:text-xs py-1 px-4 sm:px-8 border-b border-[#133D68]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold tracking-wide">LEGAL METROLOGY COMPLIANCE PORTAL</span>
            <span className="hidden md:inline text-blue-200">|</span>
            <span className="hidden md:inline text-blue-100">Statutory Package Declarations & Inspection System</span>
          </div>
          <div className="flex items-center gap-4 text-blue-100 text-[11px]">
            <span className="hidden sm:inline">Packaged Commodities Rules, 2011</span>
            <span>•</span>
            <span className="font-medium text-white uppercase tracking-wider">{role === "officer" ? "Inspector Console" : "Citizen Portal"}</span>
          </div>
        </div>
      </div>

      {/* ── Main Navigation Bar ─────────────────────────────────── */}
      <div className="border-b border-[#D5DCE5] bg-[#FFFFFF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            {/* Brand Logo & Name */}
            <Link
              to={role === "officer" ? "/officer/dashboard" : "/user/dashboard"}
              className="flex items-center gap-3 group focus:outline-none"
            >
              <div className="w-10 h-10 rounded bg-[#174A7E] text-white flex items-center justify-center shadow-sm">
                <Scale size={22} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base sm:text-lg font-bold text-[#183153] tracking-tight group-hover:text-[#174A7E] transition-colors">
                    MITRA METROLOGY
                  </span>
                </div>
                <p className="text-[11px] text-[#64748B] font-medium tracking-normal hidden sm:block">
                  Packaged Commodity Compliance & FSSAI Verification
                </p>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden lg:flex items-center gap-1">
              {role === "officer" ? (
                <>
                  <Link
                    to="/officer/dashboard"
                    className={`px-3 py-2 rounded text-sm font-medium transition-colors flex items-center gap-2 ${
                      isActive("/officer/dashboard")
                        ? "bg-[#174A7E] text-white"
                        : "text-[#183153] hover:bg-[#F5F7FA] hover:text-[#174A7E]"
                    }`}
                  >
                    <FileText size={16} />
                    Inspection Dashboard
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/user/dashboard"
                    className={`px-3 py-2 rounded text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      isActive("/user/dashboard")
                        ? "bg-[#174A7E] text-white"
                        : "text-[#183153] hover:bg-[#F5F7FA] hover:text-[#174A7E]"
                    }`}
                  >
                    <FileText size={16} />
                    Overview
                  </Link>

                  <Link
                    to="/user/scan"
                    className={`px-3 py-2 rounded text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      isActive("/user/scan")
                        ? "bg-[#174A7E] text-white"
                        : "text-[#183153] hover:bg-[#F5F7FA] hover:text-[#174A7E]"
                    }`}
                  >
                    <Camera size={16} />
                    New Scan
                  </Link>

                  <Link
                    to="/food-scan"
                    className={`px-3 py-2 rounded text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      isActive("/food-scan")
                        ? "bg-[#174A7E] text-white"
                        : "text-[#183153] hover:bg-[#F5F7FA] hover:text-[#174A7E]"
                    }`}
                  >
                    <FileSearch size={16} />
                    FSSAI Validation
                  </Link>

                  <Link
                    to="/user/history"
                    className={`px-3 py-2 rounded text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      isActive("/user/history")
                        ? "bg-[#174A7E] text-white"
                        : "text-[#183153] hover:bg-[#F5F7FA] hover:text-[#174A7E]"
                    }`}
                  >
                    <History size={16} />
                    Scan History
                  </Link>

                  <Link
                    to="/user/complaint"
                    className={`px-3 py-2 rounded text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      isActive("/user/complaint")
                        ? "bg-[#174A7E] text-white"
                        : "text-[#183153] hover:bg-[#F5F7FA] hover:text-[#174A7E]"
                    }`}
                  >
                    <AlertTriangle size={16} />
                    Grievances
                  </Link>
                </>
              )}
            </nav>

            {/* User Details & Sign Out Button */}
            <div className="hidden lg:flex items-center gap-3 pl-4 border-l border-[#D5DCE5]">
              <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 bg-[#F5F7FA] text-[#183153] rounded border border-[#D5DCE5] font-semibold">
                {role === "officer" ? <ShieldCheck size={13} className="text-[#174A7E]" /> : <User size={13} className="text-[#174A7E]" />}
                {role === "officer" ? "Inspector" : "Citizen"}
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-xs text-[#B91C1C] hover:text-white px-2.5 py-1.5 rounded border border-[#FECACA] hover:bg-[#B91C1C] transition-colors font-medium"
                title="Sign out of portal"
              >
                <LogOut size={13} />
                Sign Out
              </button>
            </div>

            {/* Mobile Menu Button */}
            <div className="flex lg:hidden items-center gap-2">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded text-[#183153] hover:bg-[#F5F7FA] border border-[#D5DCE5]"
                aria-label="Toggle navigation"
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>

          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-[#D5DCE5] bg-[#FFFFFF] px-4 pt-3 pb-4 space-y-1">
            {role === "officer" ? (
              <Link
                to="/officer/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded text-sm font-medium text-[#183153] hover:bg-[#F5F7FA]"
              >
                Inspection Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/user/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded text-sm font-medium text-[#183153] hover:bg-[#F5F7FA]"
                >
                  Overview
                </Link>
                <Link
                  to="/user/scan"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded text-sm font-medium text-[#183153] hover:bg-[#F5F7FA]"
                >
                  New Scan
                </Link>
                <Link
                  to="/food-scan"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded text-sm font-medium text-[#183153] hover:bg-[#F5F7FA]"
                >
                  FSSAI Validation
                </Link>
                <Link
                  to="/user/history"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded text-sm font-medium text-[#183153] hover:bg-[#F5F7FA]"
                >
                  Scan History
                </Link>
                <Link
                  to="/user/complaint"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded text-sm font-medium text-[#183153] hover:bg-[#F5F7FA]"
                >
                  Grievances
                </Link>
              </>
            )}
            <div className="pt-3 border-t border-[#D5DCE5] flex items-center justify-between">
              <span className="text-xs text-[#64748B] font-medium">
                {role === "officer" ? "Inspector Session" : "Citizen Session"}
              </span>
              <button
                onClick={handleLogout}
                className="text-xs text-[#B91C1C] font-semibold hover:underline flex items-center gap-1"
              >
                <LogOut size={13} />
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

export default Navbar;
