import { useState, useRef, useEffect } from "react";
import axios from "axios";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import FSSAIChecklistReport from "./FSSAIChecklistReport";

import API_BASE_URL from "../../config";


// Pre-packaged Food Samples for Instant Demonstration
const FOOD_SAMPLES = [
  {
    id: "ghee",
    name: "Pure Desi Cow Ghee (Dairy Fat)",
    category: "Dairy & Fats",
    desc: "100% Milk Fat, Fortified with Vitamin A & D, Agmark Special Grade",
    sampleText: `SHREE KRISHNA PURE DESI COW GHEE
AGMARK SPECIAL GRADE (C.A. NO. 45892)
INGREDIENTS: 100% Milk Fat (Clarified Butter). Contains no added preservatives, colours or artificial flavours. Free from added vegetable fats.
ALLERGEN ADVICE: Contains Milk.
NUTRITIONAL INFORMATION (Approx. values per 100ml):
Energy: 897 kcal
Protein: 0 g
Carbohydrate: 0 g
Total Sugars: 0 g
Added Sugars: 0 g
Total Fat: 99.7 g
Saturated Fat: 65.0 g
Trans Fat: 2.5 g
Sodium: 0 mg
Vitamin A: 750 mcg
Vitamin D: 5 mcg
FORTIFIED WITH VITAMIN A & D (+F LOGO)
NET QUANTITY: 1 Litre (905 g)
MRP: Rs 720.00 (INCL. OF ALL TAXES)
MFD: 01/02/2025
BEST BEFORE: 9 MONTHS FROM MANUFACTURE
BATCH NO: GHEE-2502
MANUFACTURED & PACKED BY: Shree Krishna Dairy Cooperative Ltd., Dairy Nagar, Anand, Gujarat - 388001
FSSAI LIC NO: 10012021000456
100% VEGETARIAN`,
  },
  {
    id: "biscuits",
    name: "Choco Crunch Biscuits",
    category: "Bakery & Biscuits",
    desc: "Wheat flour (54%), Milk solids, INS 322, INS 500(ii), Allergen advice",
    sampleText: `CHOCO CRUNCH BISCUITS
INGREDIENTS: Refined Wheat Flour (Maida) (54%), Sugar, Edible Vegetable Oil (Palm), Milk Solids (4.5%), Cocoa Solids (2.8%), Emulsifier (INS 322), Raising Agents [INS 500(ii), INS 503(ii)], Iodized Salt, Natural Identical Flavouring Substances.
ALLERGEN ADVICE: Contains Wheat (Gluten), Milk and Soy. May contain traces of Tree Nuts.
NUTRITIONAL INFORMATION (Approx. values per 100g):
Energy: 480 kcal
Protein: 7.2 g
Carbohydrate: 68.0 g
Total Sugars: 28.5 g
Added Sugars: 24.0 g
Total Fat: 20.0 g
Saturated Fat: 9.5 g
Trans Fat: 0.1 g
Sodium: 320 mg
NET QUANTITY: 120 g
MRP: Rs 30.00 (INCL. OF ALL TAXES)
MFD: 10/01/2025
BEST BEFORE: 6 MONTHS FROM PACKAGING
BATCH NO: B250109
MANUFACTURED BY: Mitra Food Products Ltd., Plot 12, Sector 8, Industrial Estate, Bengaluru - 560058
FSSAI LIC NO: 10015042001234
100% VEGETARIAN`,
  },
  {
    id: "namkeen",
    name: "Spicy Aloo Bhujia Namkeen",
    category: "Packaged Snacks",
    desc: "Tepary bean flour, gram flour, spices, edible vegetable oil",
    sampleText: `ROYAL ALOO BHUJIA NAMKEEN
INGREDIENTS: Potatoes (42%), Edible Vegetable Oil (Palmolein), Gram Flour (Besan) (15%), Tepary Bean Flour (Moth Dal), Iodised Salt, Red Chilli Powder, Black Pepper, Dry Mango Powder, Clove, Acidity Regulator (INS 330), Flavour Enhancer (INS 627, INS 631).
ALLERGEN ADVICE: May contain traces of Peanuts and Gluten.
NUTRITIONAL INFORMATION (Approx. values per 100g):
Energy: 565 kcal
Protein: 9.0 g
Carbohydrate: 42.5 g
Total Sugars: 1.5 g
Added Sugars: 0.0 g
Total Fat: 40.0 g
Saturated Fat: 17.0 g
Trans Fat: 0.1 g
Sodium: 680 mg
NET QUANTITY: 200 g
MRP: Rs 55.00
MFD: 15/01/2025
EXPIRY DATE: 14/07/2025
LOT NO: AB-994
MANUFACTURED BY: Royal Snacks Pvt. Ltd., RIICO Industrial Area, Bikaner, Rajasthan - 334001
FSSAI LIC NO: 10013013000543
100% VEGETARIAN`,
  },
];

function FoodLabelScanner() {
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);
  const animFrameRef = useRef(null);

  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraGuidance, setCameraGuidance] = useState("Align label inside camera frame");
  const [guidanceStatus, setGuidanceStatus] = useState("HOLD"); // 'HOLD', 'CLOSER', 'GLARE', 'READY'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState("");
  const [analysisReport, setAnalysisReport] = useState(null);
  const [qualityRejection, setQualityRejection] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const stopCamera = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
    }
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((t) => t.stop());
    }
    setIsCameraActive(false);
  };

  // Clean up camera on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      setErrorMsg("");
      setQualityRejection(null);
      setIsCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          runRealtimeCameraGuidance();
        };
      }
    } catch (_err) {
      setErrorMsg("Camera access denied or unavailable. Please upload a photo instead.");
      setIsCameraActive(false);
    }
  };

  // Real-time camera quality heuristics
  const runRealtimeCameraGuidance = () => {
    if (!videoRef.current || videoRef.current.paused || videoRef.current.ended) return;

    // Simple canvas sampling
    const video = videoRef.current;
    if (video.videoWidth > 0 && video.videoHeight > 0) {
      const canvas = document.createElement("canvas");
      canvas.width = 160;
      canvas.height = 120;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, 160, 120);
      const imgData = ctx.getImageData(0, 0, 160, 120);
      const data = imgData.data;

      let brightnessSum = 0;
      let glareCount = 0;
      for (let i = 0; i < data.length; i += 4) {
        const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
        brightnessSum += avg;
        if (avg > 245) glareCount++;
      }
      const avgBrightness = brightnessSum / (data.length / 4);

      if (avgBrightness < 45) {
        setCameraGuidance("Too dark — move into better lighting");
        setGuidanceStatus("HOLD");
      } else if (glareCount > 400) {
        setCameraGuidance("Reduce glare — tilt package slightly");
        setGuidanceStatus("GLARE");
      } else {
        setCameraGuidance("Good label alignment — tap Capture");
        setGuidanceStatus("READY");
      }
    }

    animFrameRef.current = requestAnimationFrame(runRealtimeCameraGuidance);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      const file = new File([blob], "food_label.jpg", { type: "image/jpeg" });
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(blob));
      stopCamera();
    }, "image/jpeg", 0.92);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setQualityRejection(null);
      setErrorMsg("");
    }
  };

  // Quick sample loader
  const handleLoadSample = (sample) => {
    // Generate a temporary canvas rendering the sample label
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 1000;
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, 800, 1000);

    ctx.fillStyle = "#111827";
    ctx.font = "bold 24px sans-serif";
    ctx.fillText(sample.name, 40, 50);

    ctx.font = "14px monospace";
    const lines = sample.sampleText.split("\n");
    let y = 100;
    for (const line of lines) {
      ctx.fillText(line, 40, y);
      y += 24;
    }

    canvas.toBlob((blob) => {
      const file = new File([blob], `${sample.id}_label.jpg`, { type: "image/jpeg" });
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(blob));
      setQualityRejection(null);
      setErrorMsg("");
    }, "image/jpeg", 0.95);
  };

  const handleAnalyze = async (forceProceed = false) => {
    if (!selectedFile) {
      setErrorMsg("Please upload or capture a pre-packaged food label.");
      return;
    }

    setIsAnalyzing(true);
    setQualityRejection(null);
    setErrorMsg("");
    setAnalysisStage("Assessing package clarity, glare & text resolution...");

    setTimeout(() => {
      setAnalysisStage("Running packaging-optimized OCR & character segmentation...");
    }, 600);

    setTimeout(() => {
      setAnalysisStage("Parsing ingredients list & resolving INS additive codes...");
    }, 1200);

    setTimeout(() => {
      setAnalysisStage("Cross-checking 8 mandatory allergens & extracting nutrition facts...");
    }, 1800);

    setTimeout(() => {
      setAnalysisStage("Evaluating Versioned FSSAI Labelling & Display Regulations, 2020...");
    }, 2400);

    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      formData.append("panel_type", "all");
      
      if (forceProceed) {
          formData.append("force_proceed", "true");
      }

      const response = await axios.post(`${API_BASE_URL}/food-label/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = response.data;

      // Check if rejected by Image Quality Gate
      if (!forceProceed && (data.status === "QUALITY_CHECK_FAILED" || !data.can_proceed_with_analysis || data.needs_retake_prompt)) {
        setQualityRejection(data);
      } else {
        setAnalysisReport(data);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(
        err?.response?.data?.detail || "Food label analysis failed. Verify backend service is running."
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setAnalysisReport(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setQualityRejection(null);
    setErrorMsg("");
  };

  return (
    <div className="min-h-screen bg-white text-[#183153] flex flex-col justify-between">
      <Navbar role="user" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded font-bold uppercase tracking-wider bg-[#E8F0FE] text-[#174A7E] border border-[#B9D5F4]">
              Food Safety & Standards Authority of India (FSSAI)
            </span>
            <span className="text-xs text-slate-500 font-medium">Labelling & Display Regulations, 2020</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#183153] mt-2 flex items-center gap-3">
            <span>🥗</span> Indian Pre-Packaged Food Label Inspector
          </h2>
          <p className="text-slate-600 text-sm mt-1 max-w-3xl leading-relaxed">
            Point camera at the back or side of packaged foods (Biscuits, Dairy/Ghee, Namkeen, Snacks, Noodles, Beverages) to verify mandatory FSSAI statutory declarations, INS additives, allergens, and nutritional standards.
          </p>
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-center justify-between shadow-sm">
            <span>⚠️ {errorMsg}</span>
            <button onClick={() => setErrorMsg("")} className="text-red-600 hover:text-red-800 font-bold">✕</button>
          </div>
        )}

        {/* QUALITY REJECTION NOTIFICATION */}
        {qualityRejection && (
          <div className="mb-8 p-6 rounded-2xl bg-amber-50 border border-amber-300 shadow-sm">
            <div className="flex items-start gap-4">
              <div className="text-3xl">📸</div>
              <div className="w-full">
                <span className="text-xs font-bold uppercase tracking-widest text-amber-800">
                  Image Quality Warning
                </span>
                <h3 className="text-lg font-bold text-amber-950 mt-1">
                  The image is blurry or poorly lit
                </h3>
                <p className="text-amber-800 text-sm mt-1 max-w-xl">
                  {qualityRejection.image_quality_warning || "OCR accuracy may be reduced. It is highly recommended to retake the photo under better lighting."}
                </p>

                <div className="mt-5 flex items-center gap-3">
                  <button
                    onClick={() => {
                      setQualityRejection(null);
                      startCamera();
                    }}
                    className="bg-amber-600 hover:bg-amber-700 text-white px-5 py-2.5 rounded-xl font-bold text-sm shadow-sm transition flex items-center gap-2"
                  >
                    <span>📷</span> Open Camera to Retake
                  </button>
                  <button
                    onClick={() => {
                        setQualityRejection(null);
                        handleAnalyze(true);
                    }}
                    className="bg-white hover:bg-amber-100 border border-amber-400 text-amber-900 px-4 py-2.5 rounded-xl font-bold text-sm transition"
                  >
                    Continue Anyway
                  </button>
                  <button
                    onClick={() => setQualityRejection(null)}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 px-4 py-2.5 rounded-xl font-bold text-sm transition"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MAIN SCANNING INTERFACE (IF NO REPORT LOADED YET) */}
        {!analysisReport ? (
          <div className="grid lg:grid-cols-12 gap-8">
            {/* Left Col: Camera & Photo Upload */}
            <div className="lg:col-span-6 flex flex-col gap-6">
              <div className="bg-white border border-[#D5DCE5] rounded-2xl p-6 shadow-sm">
                <h3 className="text-base font-bold text-[#183153] mb-4 flex items-center justify-between">
                  <span>1. Capture or Upload Back/Side Label</span>
                  {previewUrl && (
                    <span className="text-xs px-2.5 py-0.5 rounded bg-[#E8F0FE] text-[#174A7E] border border-[#B9D5F4] font-medium font-mono">
                      Image Ready
                    </span>
                  )}
                </h3>

                {isCameraActive ? (
                  <div className="relative rounded-2xl overflow-hidden bg-black aspect-[4/3] flex flex-col items-center justify-center border border-slate-300 shadow-md">
                    <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />

                    {/* Camera Guidance Overlay */}
                    <div className="absolute top-4 inset-x-4 flex justify-center">
                      <div
                        className={`px-4 py-1.5 rounded-full text-xs font-bold tracking-wide shadow-md backdrop-blur flex items-center gap-2 border ${
                          guidanceStatus === "READY"
                            ? "bg-white/95 text-green-800 border-green-500"
                            : guidanceStatus === "GLARE"
                            ? "bg-white/95 text-amber-800 border-amber-500"
                            : "bg-white/95 text-slate-800 border-slate-300"
                        }`}
                      >
                        <span className="w-2 h-2 rounded-full animate-ping bg-[#174A7E]" />
                        {cameraGuidance}
                      </div>
                    </div>

                    {/* Alignment Reticle */}
                    <div className="absolute inset-8 border-2 border-dashed border-white/60 rounded-2xl pointer-events-none" />

                    {/* Bottom Camera Controls */}
                    <div className="absolute bottom-4 flex gap-3">
                      <button
                        onClick={capturePhoto}
                        className="bg-[#174A7E] hover:bg-[#133D68] text-white px-6 py-2.5 rounded-xl font-bold text-sm shadow-md flex items-center gap-2 transition"
                      >
                        <span>📸</span> Capture Label
                      </button>
                      <button
                        onClick={stopCamera}
                        className="bg-slate-800/90 hover:bg-slate-700 text-white px-4 py-2.5 rounded-xl text-xs font-semibold backdrop-blur"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : previewUrl ? (
                  <div className="relative rounded-2xl overflow-hidden bg-[#F5F7FA] border border-[#D5DCE5] flex items-center justify-center p-3 group min-h-[300px]">
                    <img
                      src={previewUrl}
                      alt="Food label preview"
                      className="max-h-[380px] w-auto object-contain rounded-xl shadow-sm border border-[#D5DCE5]"
                    />

                    {isAnalyzing && (
                      <div className="absolute inset-0 bg-white/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
                        <div className="animate-spin text-4xl mb-4 text-[#174A7E]">⚙️</div>
                        <h4 className="font-bold text-[#183153] text-base">Analyzing Food Package</h4>
                        <p className="text-xs text-[#174A7E] mt-2 max-w-sm font-semibold">{analysisStage}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-[#D5DCE5] hover:border-[#174A7E] rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition bg-[#F5F7FA] hover:bg-white min-h-[280px]"
                  >
                    <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center text-3xl mb-3 border border-[#D5DCE5] shadow-sm">
                      🥗
                    </div>
                    <p className="font-bold text-[#183153] text-sm text-center">
                      Point camera or drop photo of food packaging
                    </p>
                    <p className="text-xs text-slate-500 mt-1 text-center">
                      Supports ingredients panel, nutrition table, FSSAI logo, dates
                    </p>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                <div className="grid grid-cols-2 gap-3 mt-4">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-white hover:bg-[#F5F7FA] text-[#183153] text-xs font-bold py-3 px-4 rounded-xl border border-[#D5DCE5] transition flex items-center justify-center gap-2 shadow-sm"
                  >
                    <span>📂</span> Upload Photo
                  </button>

                  {!isCameraActive ? (
                    <button
                      type="button"
                      onClick={startCamera}
                      className="bg-white hover:bg-[#F5F7FA] text-[#183153] text-xs font-bold py-3 px-4 rounded-xl border border-[#D5DCE5] transition flex items-center justify-center gap-2 shadow-sm"
                    >
                      <span>📷</span> Open Live Camera
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={stopCamera}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold py-3 px-4 rounded-xl border border-slate-300"
                    >
                      Close Camera
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  disabled={!selectedFile || isAnalyzing}
                  onClick={handleAnalyze}
                  className="mt-4 w-full bg-[#174A7E] hover:bg-[#133D68] disabled:bg-slate-100 disabled:text-slate-400 text-white py-3.5 rounded-xl font-bold transition shadow-sm text-sm flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <span>Evaluating FSSAI Requirements...</span>
                  ) : (
                    <>
                      <span>🔍</span> Run FSSAI Label Audit
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Right Col: Instant Sample Presets & Food Categories */}
            <div className="lg:col-span-6 flex flex-col gap-6">
              <div className="bg-white border border-[#D5DCE5] rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-base font-bold text-[#183153] flex items-center gap-2">
                      <span>⚡</span> Quick Sample Presets (1-Click Test)
                    </h3>
                    <p className="text-xs text-slate-600 mt-0.5">
                      Select real Indian pre-packaged food labels to test the complete pipeline instantly:
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {FOOD_SAMPLES.map((sample) => (
                    <div
                      key={sample.id}
                      onClick={() => handleLoadSample(sample)}
                      className="p-4 rounded-xl bg-[#F5F7FA] border border-[#D5DCE5] hover:border-[#174A7E] cursor-pointer transition flex items-center justify-between group"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-[#183153] group-hover:text-[#174A7E] transition">
                            {sample.name}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-white text-slate-600 border border-[#D5DCE5] font-mono">
                            {sample.category}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1 line-clamp-1">{sample.desc}</p>
                      </div>

                      <button className="bg-white group-hover:bg-[#174A7E] text-[#183153] group-hover:text-white border border-[#D5DCE5] group-hover:border-[#174A7E] px-3 py-1.5 rounded-lg text-xs font-bold transition shrink-0 ml-3">
                        Load Sample →
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Regulatory Scope Information */}
              <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded-2xl p-6">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#183153] mb-3">
                  Audited Food Categories & Key FSSAI Checks
                </h4>
                <div className="grid grid-cols-2 gap-2.5 text-xs text-slate-700">
                  <div className="p-3 bg-white rounded-xl border border-[#D5DCE5]">
                    <span className="font-bold text-[#174A7E] block mb-0.5">Dairy & Ghee:</span>
                    <span>Milk fat min 99.7%, Agmark grade, Fortification +F</span>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-[#D5DCE5]">
                    <span className="font-bold text-[#174A7E] block mb-0.5">Biscuits & Bakery:</span>
                    <span>QUID %, INS additives, Allergen declarations</span>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-[#D5DCE5]">
                    <span className="font-bold text-[#174A7E] block mb-0.5">Snacks & Namkeen:</span>
                    <span>Saturated fat, Trans fat & Sodium per 100g</span>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-[#D5DCE5]">
                    <span className="font-bold text-[#174A7E] block mb-0.5">Beverages:</span>
                    <span>Added sugars declaration & fruit content %</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* DISPLAY FULL FSSAI AUDIT REPORT */
          <FSSAIChecklistReport reportData={analysisReport} onReset={handleReset} />
        )}
      </main>

      <Footer />
    </div>
  );
}

export default FoodLabelScanner;
