import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { 
  AlertTriangle, CheckCircle, Edit2, Save, X, ChevronRight, 
  EyeOff, RefreshCcw, ShieldCheck, Image as ImageIcon, ArrowLeft, Info, HelpCircle
} from "lucide-react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

const OCRReview = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [scanData, setScanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // local edits state: { field_name: { corrected_value: string|null, mark_unreadable: boolean } }
  const [corrections, setCorrections] = useState({});
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const fetchReviewData = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch(`${API_BASE_URL}/scans/${scanId}/review`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to load scan review data");
        const data = await res.json();
        
        // If already confirmed, redirect to history
        if (data.user_confirmed) {
          navigate(`/user/history`);
          return;
        }
        
        setScanData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchReviewData();
  }, [scanId, navigate]);

  const handleCorrectionChange = (fieldName, value) => {
    setCorrections(prev => ({
      ...prev,
      [fieldName]: { corrected_value: value, mark_unreadable: false }
    }));
  };

  const handleMarkUnreadable = (fieldName) => {
    setCorrections(prev => ({
      ...prev,
      [fieldName]: { corrected_value: null, mark_unreadable: true }
    }));
  };

  const handleReset = (fieldName) => {
    setCorrections(prev => {
      const next = { ...prev };
      delete next[fieldName];
      return next;
    });
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      
      // 1. Save corrections if any
      const correctionList = Object.entries(corrections).map(([field_name, data]) => ({
        field_name,
        corrected_value: data.corrected_value,
        mark_unreadable: data.mark_unreadable
      }));

      if (correctionList.length > 0) {
        const saveRes = await fetch(`${API_BASE_URL}/scans/${scanId}/fields`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ corrections: correctionList })
        });
        if (!saveRes.ok) throw new Error("Failed to save field corrections");
      }

      // 2. Confirm and generate report
      const confirmRes = await fetch(`${API_BASE_URL}/scans/${scanId}/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({})
      });
      if (!confirmRes.ok) throw new Error("Failed to generate compliance report");

      // 3. Navigate back to history where report is viewable
      navigate(`/user/history`);
    } catch (err) {
      setError(err.message);
      setConfirming(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="user" />
      <div className="flex-grow flex items-center justify-center p-8">
        <div className="text-center">
          <RefreshCcw className="w-8 h-8 text-[#174A7E] animate-spin mx-auto mb-3" />
          <p className="text-xs font-semibold text-[#183153]">Loading Extracted Declaration Records...</p>
        </div>
      </div>
      <Footer />
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="user" />
      <div className="flex-grow flex items-center justify-center p-8">
        <div className="bg-[#FEE2E2] text-[#B91C1C] border border-[#FECACA] p-5 rounded max-w-md w-full shadow-sm">
          <div className="flex items-center gap-2 font-bold text-sm mb-1">
            <AlertTriangle size={18} /> Error Loading Review
          </div>
          <p className="text-xs text-[#7F1D1D] mb-4">{error}</p>
          <button
            onClick={() => navigate("/user/scan")}
            className="px-3 py-1.5 bg-[#B91C1C] text-white text-xs font-semibold rounded hover:bg-[#991B1B]"
          >
            Return to New Scan
          </button>
        </div>
      </div>
      <Footer />
    </div>
  );

  if (!scanData) return null;

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="user" />
      
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        
        {/* ── Step Indicator ────────────────────────────────────────── */}
        <div className="mb-8 border-b border-[#D5DCE5] pb-6">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Link to="/user/scan" className="text-xs font-semibold text-[#174A7E] hover:underline flex items-center gap-1">
                  <ArrowLeft size={13} /> Back to Scan
                </Link>
                <span className="text-[#D5DCE5]">|</span>
                <span className="text-xs font-mono text-[#64748B]">Scan Record #{scanData.scan_id}</span>
              </div>
              <h1 className="text-2xl font-bold text-[#183153] tracking-tight">
                Review Extracted Information
              </h1>
              <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
                Verify each declaration before the deterministic Legal Metrology compliance engine evaluates the data.
              </p>
            </div>

            <button
              onClick={handleConfirm}
              disabled={confirming}
              className="flex justify-center items-center gap-2 px-5 py-2.5 rounded shadow-sm text-xs sm:text-sm font-semibold text-white bg-[#174A7E] hover:bg-[#133D68] disabled:opacity-70 transition-colors"
            >
              {confirming ? (
                <RefreshCcw className="w-4 h-4 animate-spin" />
              ) : (
                <ShieldCheck className="w-4 h-4" />
              )}
              Confirm & Generate Compliance Report
            </button>
          </div>

          {/* Workflow Steps */}
          <div className="grid grid-cols-4 gap-2 text-xs font-semibold">
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#F5F7FA] text-[#15803D] border border-[#BBF7D0]">
              <span className="w-5 h-5 rounded-full bg-[#DCFCE7] text-[#15803D] flex items-center justify-center text-[11px] font-bold">✓</span>
              <span className="hidden sm:inline">Image Uploaded</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#174A7E] text-white">
              <span className="w-5 h-5 rounded-full bg-white text-[#174A7E] flex items-center justify-center text-[11px] font-bold">2</span>
              <span className="hidden sm:inline">Review Extracted Data</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#F5F7FA] text-[#64748B] border border-[#D5DCE5]">
              <span className="w-5 h-5 rounded-full bg-[#D5DCE5] text-[#183153] flex items-center justify-center text-[11px] font-bold">3</span>
              <span className="hidden sm:inline">Confirm Review</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#F5F7FA] text-[#64748B] border border-[#D5DCE5]">
              <span className="w-5 h-5 rounded-full bg-[#D5DCE5] text-[#183153] flex items-center justify-center text-[11px] font-bold">4</span>
              <span className="hidden sm:inline">Compliance Report</span>
            </div>
          </div>
        </div>

        {/* Quality Warning Banner if applicable */}
        {scanData.has_quality_warning && (
          <div className="mb-6 p-4 bg-[#FEF3C7] rounded border border-[#FDE68A] text-[#B45309] flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-[#B45309] shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#92400E]">
                Image Quality Notice ({scanData.quality_tier})
              </h4>
              <p className="text-xs text-[#92400E] mt-1 leading-relaxed">
                The uploaded label image quality was assessed as {scanData.quality_tier}. Please double-check all OCR-extracted values below against the physical packaging image.
              </p>
            </div>
          </div>
        )}

        {/* ── Side-by-Side Review Grid ──────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Image Preview (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col">
            <div className="bg-white rounded border border-[#D5DCE5] overflow-hidden sticky top-24 shadow-sm">
              <div className="bg-[#F5F7FA] px-4 py-3 border-b border-[#D5DCE5] flex items-center justify-between">
                <h3 className="text-xs font-bold text-[#183153] uppercase tracking-wider flex items-center gap-2">
                  <ImageIcon size={14} className="text-[#174A7E]" />
                  Original Package Label
                </h3>
                <span className="text-[11px] text-[#64748B]">Audited Image</span>
              </div>
              
              <div className="p-4 bg-[#F5F7FA] flex items-center justify-center min-h-[380px]">
                {scanData.image_url ? (
                  <img 
                    src={`${API_BASE_URL}${scanData.image_url}`} 
                    alt="Physical product package" 
                    className="max-h-[550px] w-auto object-contain rounded border border-[#D5DCE5] bg-white shadow-xs"
                  />
                ) : (
                  <p className="text-xs text-[#64748B]">Image not available in storage</p>
                )}
              </div>
              
              {/* Expandable raw OCR text section */}
              {scanData.raw_ocr_text && (
                <div className="border-t border-[#D5DCE5]">
                  <details className="group">
                    <summary className="px-4 py-2.5 text-xs font-semibold text-[#174A7E] cursor-pointer hover:bg-[#F5F7FA] select-none flex items-center justify-between">
                      <span>View Raw OCR Stream</span>
                      <span className="text-[11px] text-[#64748B] font-normal">Click to expand</span>
                    </summary>
                    <div className="px-4 pb-4 bg-white border-t border-[#D5DCE5]">
                      <pre className="text-[11px] bg-[#F5F7FA] p-3 rounded overflow-auto max-h-40 text-[#475569] border border-[#D5DCE5] whitespace-pre-wrap font-mono mt-2">
                        {scanData.raw_ocr_text}
                      </pre>
                    </div>
                  </details>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Editable Fields Form (7 Cols) */}
          <div className="lg:col-span-7">
            <div className="bg-white rounded border border-[#D5DCE5] shadow-sm overflow-hidden">
              <div className="bg-[#F5F7FA] px-4 py-3 border-b border-[#D5DCE5] flex items-center justify-between">
                <h3 className="text-xs font-bold text-[#183153] uppercase tracking-wider flex items-center gap-2">
                  <Edit2 size={14} className="text-[#174A7E]" />
                  Statutory Declarations (Editable)
                </h3>
                <span className="text-[11px] text-[#64748B]">
                  Click field to edit before confirming
                </span>
              </div>
              
              <div className="divide-y divide-[#D5DCE5]">
                {scanData.fields && scanData.fields.filter(f => f.field_name !== "_ocr_text").map((field) => {
                  
                  const isLocallyEdited = corrections[field.field_name] !== undefined;
                  const currentLocalEdit = corrections[field.field_name];
                  
                  const isUnreadable = isLocallyEdited 
                    ? currentLocalEdit.mark_unreadable 
                    : (field.correction_status === "user_marked_unreadable" || field.field_status === "UNREADABLE");
                  
                  const displayValue = isLocallyEdited
                    ? (currentLocalEdit.mark_unreadable ? "" : (currentLocalEdit.corrected_value || ""))
                    : (field.display_value || "");

                  const confPct = field.confidence ? Math.round(field.confidence * 100) : null;
                  
                  const labels = {
                    "product_name": "Product / Commodity Name",
                    "mrp": "Maximum Retail Price (MRP)",
                    "net_quantity": "Net Quantity (Standard Metric Unit)",
                    "manufacturing_date": "Date of Packaging / Manufacture",
                    "best_before": "Best Before / Expiry Period",
                    "expiry_date": "Expiry Date",
                    "fssai": "FSSAI Licence Number (Food)",
                    "manufacturer": "Manufacturer Name",
                    "manufacturer_address": "Manufacturer Registered Address",
                    "address": "Packer / Manufacturer Address",
                    "consumer_care": "Consumer Care Details (Phone / Email)"
                  };
                  
                  const label = labels[field.field_name] || field.field_name.replace(/_/g, " ");

                  return (
                    <div key={field.field_name} className="p-4 hover:bg-[#F5F7FA] transition-colors">
                      <div className="flex justify-between items-center mb-1.5">
                        <label className="text-xs font-bold text-[#183153] capitalize">
                          {label}
                        </label>
                        <div className="flex items-center gap-1.5">
                          {confPct !== null && !isLocallyEdited && (
                            <span className={`text-[11px] px-2 py-0.5 rounded font-semibold border ${
                              confPct >= 80 ? 'bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]' : 
                              confPct >= 50 ? 'bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]' : 
                              'bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]'
                            }`}>
                              {confPct}% Confidence
                            </span>
                          )}
                          {isLocallyEdited && (
                            <span className="text-[11px] px-2 py-0.5 rounded font-semibold bg-[#EDF2F7] text-[#174A7E] border border-[#CBD5E1]">
                              Modified
                            </span>
                          )}
                          {field.field_status === "UNREADABLE" && (
                            <span className="text-[11px] px-2 py-0.5 rounded font-semibold bg-[#F1F5F9] text-[#64748B] border border-[#CBD5E1]">
                              Unreadable
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-stretch mt-1">
                        <input
                          type="text"
                          value={displayValue}
                          disabled={isUnreadable}
                          onChange={(e) => handleCorrectionChange(field.field_name, e.target.value)}
                          className={`block w-full text-xs sm:text-sm px-3 py-2 border border-[#D5DCE5] rounded-l bg-white text-[#183153] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E] ${
                            isUnreadable ? 'bg-[#F1F5F9] text-[#94A3B8] italic' : ''
                          }`}
                          placeholder={isUnreadable ? "Marked as unreadable" : "Not detected on label"}
                        />
                        <button
                          type="button"
                          onClick={() => handleMarkUnreadable(field.field_name)}
                          className="px-3 py-2 border-y border-r border-[#D5DCE5] text-xs font-semibold text-[#64748B] bg-[#F5F7FA] hover:bg-[#EDF2F7] hover:text-[#183153] flex items-center gap-1.5 transition-colors"
                          title="Mark declaration unreadable on package"
                        >
                          <EyeOff size={13} />
                          <span className="hidden sm:inline">Unreadable</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleReset(field.field_name)}
                          disabled={!isLocallyEdited}
                          className="px-3 py-2 border-y border-r border-[#D5DCE5] rounded-r text-xs font-semibold text-[#64748B] bg-[#F5F7FA] hover:bg-[#EDF2F7] hover:text-[#183153] disabled:opacity-40 flex items-center gap-1.5 transition-colors"
                          title="Reset to original OCR extraction"
                        >
                          <RefreshCcw size={13} />
                          <span className="hidden sm:inline">Reset</span>
                        </button>
                      </div>
                      
                      {/* Preserved Audit Trail display */}
                      {isLocallyEdited && field.original_ocr_value && (
                        <div className="mt-1.5 text-[11px] text-[#64748B] flex items-center gap-2">
                          <span>Original OCR value:</span>
                          <span className="line-through text-[#94A3B8] font-mono">{field.original_ocr_value}</span>
                          <span className="text-[#15803D] font-medium">• Preserved in statutory audit trail</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Action Box at bottom of fields card */}
              <div className="p-4 bg-[#F5F7FA] border-t border-[#D5DCE5] flex flex-wrap items-center justify-between gap-3">
                <div className="text-xs text-[#64748B] flex items-center gap-1.5">
                  <Info size={14} className="text-[#174A7E]" />
                  <span>Manual corrections are logged with user ID & timestamp</span>
                </div>

                <button
                  onClick={handleConfirm}
                  disabled={confirming}
                  className="px-5 py-2.5 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs sm:text-sm font-semibold rounded shadow-sm flex items-center gap-2 transition-colors disabled:opacity-70"
                >
                  {confirming ? <RefreshCcw size={15} className="animate-spin" /> : <ShieldCheck size={15} />}
                  Confirm & Generate Compliance Report
                </button>
              </div>

            </div>

          </div>

        </div>

      </main>

      <Footer />
    </div>
  );
};

export default OCRReview;
