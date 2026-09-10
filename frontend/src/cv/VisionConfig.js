import API_BASE_URL from "../config";

/**
 * Centralized Computer Vision Pipeline Configuration.
 * Holds user-configurable and model-specific hyperparameters.
 */
export const VisionConfig = {
  // Confidence Threshold presets
  PRESETS: {
    SENSITIVE: 0.50,
    BALANCED: 0.70,
    STRICT: 0.85,
  },

  // Active runtime parameters
  confidenceThreshold: 0.70,
  iouThreshold: 0.45,
  inputWidth: 300,
  inputHeight: 300,
  maxDetections: 10,
  targetInferenceFps: 15,
  requiredStableFrames: 3,

  // Inference mode: 'LOCAL' (browser on-device) or 'CLOUD' (backend POST /predict)
  mode: "LOCAL",

  // Model backend details
  cloudApiUrl: `${API_BASE_URL}/predict`,


  update(newConfig) {
    Object.assign(this, newConfig);
    if (this.confidenceThreshold < 0.1) this.confidenceThreshold = 0.1;
    if (this.confidenceThreshold > 0.99) this.confidenceThreshold = 0.99;
    if (this.iouThreshold < 0.1) this.iouThreshold = 0.1;
    if (this.iouThreshold > 0.99) this.iouThreshold = 0.99;
  },
};
