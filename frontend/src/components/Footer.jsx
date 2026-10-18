import { Link } from "react-router-dom";
import { Shield, ExternalLink, HelpCircle, FileCheck, Scale } from "lucide-react";

function Footer() {
  return (
    <footer className="bg-[#F5F7FA] border-t border-[#D5DCE5] text-[#183153] mt-auto">
      {/* Upper Footer: Regulatory Scope & Information */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Column 1: About Portal */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-[#174A7E] flex items-center justify-center text-white">
                <Scale size={16} />
              </div>
              <span className="text-base font-bold text-[#183153] tracking-wide">
                MITRA METROLOGY
              </span>
            </div>
            <p className="text-xs text-[#475569] leading-relaxed max-w-lg">
              Automated packaged commodity compliance inspection system designed for statutory verification under the Legal Metrology (Packaged Commodities) Rules, 2011 and FSSAI (Labelling and Display) Regulations, 2020.
            </p>
            <div className="p-3 bg-white rounded border border-[#D5DCE5] text-xs text-[#64748B] max-w-lg">
              <span className="font-semibold text-[#183153]">Regulatory Notice: </span>
              Mitra Metrology provides assisted verification using optical character recognition and deterministic rule validation. Official enforcement decisions and notices are issued exclusively by authorized Legal Metrology inspectors.
            </div>
          </div>

          {/* Column 2: Legal Metrology Declarations */}
          <div>
            <h4 className="text-xs font-bold text-[#183153] uppercase tracking-wider mb-3">
              Mandatory Declarations
            </h4>
            <ul className="space-y-1.5 text-xs text-[#475569]">
              <li className="flex items-center gap-1.5">
                <FileCheck size={13} className="text-[#174A7E]" />
                Maximum Retail Price (MRP)
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck size={13} className="text-[#174A7E]" />
                Net Quantity & Standard Units
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck size={13} className="text-[#174A7E]" />
                Manufacturing & Expiry Dates
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck size={13} className="text-[#174A7E]" />
                Manufacturer / Packer Address
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck size={13} className="text-[#174A7E]" />
                Consumer Care Information
              </li>
            </ul>
          </div>

          {/* Column 3: Quick Services */}
          <div>
            <h4 className="text-xs font-bold text-[#183153] uppercase tracking-wider mb-3">
              Portal Services
            </h4>
            <ul className="space-y-1.5 text-xs text-[#475569]">
              <li>
                <Link to="/user/scan" className="hover:text-[#174A7E] hover:underline">
                  New Package Scan
                </Link>
              </li>
              <li>
                <Link to="/food-scan" className="hover:text-[#174A7E] hover:underline">
                  FSSAI Food Label Check
                </Link>
              </li>
              <li>
                <Link to="/user/history" className="hover:text-[#174A7E] hover:underline">
                  Inspection Records & PDF Reports
                </Link>
              </li>
              <li>
                <Link to="/user/complaint" className="hover:text-[#174A7E] hover:underline">
                  File Statutory Grievance
                </Link>
              </li>
              <li>
                <Link to="/roles" className="hover:text-[#174A7E] hover:underline">
                  Role & Portal Selection
                </Link>
              </li>
            </ul>
          </div>

        </div>
      </div>

      {/* Bottom Strip */}
      <div className="border-t border-[#D5DCE5] bg-[#FFFFFF] py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[#64748B]">
          <div>
            <span>Mitra Metrology Platform v2.0 • Legal Metrology & Food Label Inspector</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Deterministic Rule Engine</span>
            <span>•</span>
            <span>OCR Audit Trail</span>
            <span>•</span>
            <span>Officer Verification Workflow</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
