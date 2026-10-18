import { useNavigate } from "react-router-dom";
import { User, ShieldCheck, Scale, ArrowRight, CheckCircle, FileText, Lock } from "lucide-react";
import Footer from "../../components/Footer";

function RoleSelection() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      
      {/* ── Top Government Header Strip ───────────────────────────── */}
      <div className="bg-[#174A7E] text-white text-xs py-2 px-4 sm:px-8 border-b border-[#133D68]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold tracking-wide">LEGAL METROLOGY COMPLIANCE PORTAL</span>
            <span className="hidden sm:inline text-blue-200">|</span>
            <span className="hidden sm:inline text-blue-100">National Commodity Regulatory Inspectorate</span>
          </div>
          <span className="text-blue-100 text-[11px]">Packaged Commodities Rules, 2011</span>
        </div>
      </div>

      {/* ── Main Portal Selection ─────────────────────────────────── */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-12 flex flex-col justify-center">
        
        {/* Title Header */}
        <div className="text-center mb-12">
          <div className="w-14 h-14 rounded bg-[#174A7E] text-white flex items-center justify-center mx-auto mb-4 shadow-sm">
            <Scale size={30} />
          </div>
          <h1 className="text-3xl font-bold text-[#183153] tracking-tight">
            MITRA METROLOGY
          </h1>
          <p className="mt-1 text-base text-[#174A7E] font-medium">
            Packaged Commodity Legal Metrology & FSSAI Inspection Portal
          </p>
          <p className="mt-2 text-xs sm:text-sm text-[#64748B] max-w-xl mx-auto">
            Select your designated portal to verify statutory declarations, review OCR findings, or manage official regulatory inspections.
          </p>
        </div>

        {/* Portal Cards Grid */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto w-full">
          
          {/* Card 1: Citizen / User Portal */}
          <div 
            onClick={() => navigate("/user/login")}
            className="bg-white border border-[#D5DCE5] rounded p-8 shadow-sm hover:border-[#174A7E] hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded bg-[#F5F7FA] text-[#174A7E] border border-[#D5DCE5] flex items-center justify-center">
                  <User size={24} />
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-[#DCFCE7] text-[#15803D] border border-[#BBF7D0]">
                  Public Access
                </span>
              </div>
              
              <h2 className="text-xl font-bold text-[#183153] group-hover:text-[#174A7E] transition-colors">
                Citizen & Consumer Portal
              </h2>
              
              <p className="text-sm text-[#475569] mt-3 leading-relaxed">
                Scan packaged products to verify mandatory declarations including MRP, Net Quantity, Expiry Date, Manufacturer Address, and FSSAI standards.
              </p>

              <ul className="mt-5 space-y-2 text-xs text-[#64748B]">
                <li className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#15803D]" />
                  Verify product label declarations instantly
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#15803D]" />
                  Review & correct OCR-extracted information
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#15803D]" />
                  File statutory non-compliance grievances
                </li>
              </ul>
            </div>
            
            <button
              className="mt-8 w-full py-2.5 px-4 bg-[#174A7E] hover:bg-[#133D68] text-white text-sm font-semibold rounded transition-colors flex items-center justify-center gap-2"
            >
              Enter Citizen Portal <ArrowRight size={15} />
            </button>
          </div>

          {/* Card 2: Legal Metrology Officer Portal */}
          <div 
            onClick={() => navigate("/officer/login")}
            className="bg-white border border-[#D5DCE5] rounded p-8 shadow-sm hover:border-[#174A7E] hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded bg-[#F5F7FA] text-[#183153] border border-[#D5DCE5] flex items-center justify-center">
                  <ShieldCheck size={24} />
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
                  Authorized Officers
                </span>
              </div>
              
              <h2 className="text-xl font-bold text-[#183153] group-hover:text-[#174A7E] transition-colors">
                Legal Metrology Officer Portal
              </h2>
              
              <p className="text-sm text-[#475569] mt-3 leading-relaxed">
                Access official inspection consoles, validate statutory evidence, issue formal compliance findings, and process consumer complaints.
              </p>

              <ul className="mt-5 space-y-2 text-xs text-[#64748B]">
                <li className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#174A7E]" />
                  Conduct formal regulatory inspections
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#174A7E]" />
                  Download court-admissible PDF audit reports
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#174A7E]" />
                  Process & resolve statutory violations
                </li>
              </ul>
            </div>
            
            <button
              className="mt-8 w-full py-2.5 px-4 bg-white hover:bg-[#F5F7FA] text-[#174A7E] border-2 border-[#174A7E] text-sm font-semibold rounded transition-colors flex items-center justify-center gap-2"
            >
              Officer Secure Login <ArrowRight size={15} />
            </button>
          </div>

        </div>

        {/* Regulatory Note */}
        <div className="mt-12 text-center text-xs text-[#64748B] max-w-xl mx-auto">
          <p className="leading-relaxed">
            Statutory framework governed by the Legal Metrology Act, 2009 read with Legal Metrology (Packaged Commodities) Rules, 2011 and Food Safety & Standards Regulations.
          </p>
        </div>

      </main>

      <Footer />
    </div>
  );
}

export default RoleSelection;