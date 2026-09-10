import { Link, useNavigate, useLocation } from "react-router-dom";

function Navbar({ role = "user" }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    navigate("/roles");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <Link to={role === "officer" ? "/officer/dashboard" : "/user/dashboard"} className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-xl">
            ⚖️
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">
              MITRA <span className="text-blue-400">METROLOGY</span>
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">Legal Metrology Compliance Inspector</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-2 sm:gap-4">
          {role === "officer" ? (
            <>
              <Link
                to="/officer/dashboard"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive("/officer/dashboard")
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                Inspection Dashboard
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/user/dashboard"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive("/user/dashboard")
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                Dashboard
              </Link>

              <Link
                to="/food-scan"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
                  isActive("/food-scan")
                    ? "bg-emerald-600 text-white shadow-lg shadow-emerald-500/20 font-bold"
                    : "text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/40 border border-emerald-800/40"
                }`}
              >
                <span>🥗</span> Food Label (FSSAI)
              </Link>

              <Link
                to="/user/scan"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
                  isActive("/user/scan")
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                <span>📷</span> Metrology Scanner
              </Link>

              <Link
                to="/user/history"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive("/user/history")
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                History
              </Link>

              <Link
                to="/user/complaint"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive("/user/complaint")
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800"
                }`}
              >
                Report Grievance
              </Link>
            </>
          )}

          {/* Role badge and Logout */}
          <div className="flex items-center gap-3 pl-3 border-l border-slate-800 ml-2">
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                role === "officer"
                  ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                  : "bg-blue-950 text-blue-400 border-blue-800"
              }`}
            >
              {role === "officer" ? "Inspector" : "Citizen"}
            </span>

            <button
              onClick={handleLogout}
              className="text-xs text-slate-400 hover:text-red-400 p-1.5 rounded-lg hover:bg-slate-800 transition"
              title="Logout"
            >
              Sign out ⎋
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
}

export default Navbar;
