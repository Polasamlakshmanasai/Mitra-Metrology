import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Scale } from "lucide-react";

function Splash() {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/roles");
    }, 1800);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F7FA] text-[#183153] px-4">
      <div className="bg-white border border-[#D5DCE5] rounded p-8 sm:p-12 shadow-sm text-center max-w-md w-full">
        
        {/* Emblem / Logo */}
        <div className="w-16 h-16 rounded bg-[#174A7E] text-white flex items-center justify-center mx-auto mb-6 shadow-sm">
          <Scale size={34} />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-[#183153]">
          MITRA METROLOGY
        </h1>

        <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-[#174A7E]">
          Packaged Commodity Compliance Portal
        </p>

        <div className="mt-4 pt-4 border-t border-[#D5DCE5]">
          <p className="text-xs text-[#64748B] leading-relaxed">
            Legal Metrology (Packaged Commodities) Rules, 2011 & FSSAI Verification System
          </p>
        </div>

        {/* Loading Spinner */}
        <div className="mt-8 flex items-center justify-center gap-2 text-xs text-[#64748B]">
          <div className="w-3.5 h-3.5 border-2 border-[#174A7E] border-t-transparent rounded-full animate-spin"></div>
          <span>Initializing Portal Environment...</span>
        </div>

      </div>
    </div>
  );
}

export default Splash;