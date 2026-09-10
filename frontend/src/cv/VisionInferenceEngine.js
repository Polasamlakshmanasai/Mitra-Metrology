import { ImagePreprocessor } from "./ImagePreprocessor";
import { PlaceholderVisionModel } from "./PlaceholderVisionModel";
import { applyNMS } from "./NonMaximumSuppression";
import { TemporalConfirmation } from "./TemporalConfirmation";
import { VisionConfig } from "./VisionConfig";
import axios from "axios";

/**
 * VisionInferenceEngine: Central controller orchestrating:
 * Camera Frame -> Preprocessing -> Inference -> Thresholding -> NMS -> Temporal Confirmation -> Telemetry
 */
export class VisionInferenceEngine {
  constructor(model = null) {
    this.model = model || new PlaceholderVisionModel();
    this.preprocessor = new ImagePreprocessor(VisionConfig.inputWidth, VisionConfig.inputHeight);
    this.temporalTracker = new TemporalConfirmation(VisionConfig.requiredStableFrames);

    // Concurrency & Backpressure control
    this.isBusy = false;
    this.lastFrameTimestamp = 0;
    this.droppedFrames = 0;
    this.totalProcessedFrames = 0;

    // Telemetry & Developer Diagnostics
    this.diagnostics = {
      fps: 0,
      inferenceLatencyMs: 0,
      preprocessLatencyMs: 0,
      postprocessLatencyMs: 0,
      droppedFrames: 0,
      totalFrames: 0,
    };

    this.fpsWindow = [];
  }

  async initialize() {
    await this.model.loadModel();
  }

  /**
   * Main processing loop entry point called per video frame or for a static image.
   * @param {HTMLVideoElement | HTMLImageElement | HTMLCanvasElement} frameSource
   * @param {Object} overrideConfig - optional dynamic overrides
   * @returns {Object|null} result object or null if frame was dropped
   */
  async processFrame(frameSource, overrideConfig = {}) {
    const config = { ...VisionConfig, ...overrideConfig };
    const now = performance.now();

    // 1. Frame Throttling check (target 10–30 FPS)
    const minFrameIntervalMs = 1000 / (config.targetInferenceFps || 15);
    if (now - this.lastFrameTimestamp < minFrameIntervalMs) {
      return null; // Skip frame to match target FPS
    }

    // 2. Backpressure / Frame dropping check
    if (this.isBusy) {
      this.droppedFrames++;
      this.diagnostics.droppedFrames = this.droppedFrames;
      return null; // Drop frame if neural network is still running
    }

    this.isBusy = true;
    this.lastFrameTimestamp = now;

    try {
      // 3. Preprocessing
      const tPreprocessStart = performance.now();
      const preprocessed = this.preprocessor.preprocess(frameSource);
      const preprocessLatencyMs = performance.now() - tPreprocessStart;

      let rawDetections = [];
      let inferenceLatencyMs = 0;

      // 4. Inference (Local vs Cloud Mode)
      if (config.mode === "CLOUD") {
        const tInferStart = performance.now();
        // Send frame to backend API
        const detections = await this._inferCloud(frameSource, config.confidenceThreshold);
        rawDetections = detections;
        inferenceLatencyMs = performance.now() - tInferStart;
      } else {
        const inferResult = await this.model.infer(preprocessed);
        rawDetections = this.model.postprocess(inferResult);
        inferenceLatencyMs = inferResult.inferenceLatencyMs || 0;
      }

      // 5. Postprocessing: Confidence Filtering + NMS + Temporal Confirmation
      const tPostprocessStart = performance.now();

      // Confidence filtering
      const filtered = rawDetections.filter((d) => d.confidence >= config.confidenceThreshold);

      // Non-Maximum Suppression
      const nmsDetections = applyNMS(filtered, config.iouThreshold, config.maxDetections);

      // Temporal Confirmation
      const temporalResult = this.temporalTracker.process(
        nmsDetections,
        config.confidenceThreshold,
        config.requiredStableFrames
      );

      const postprocessLatencyMs = performance.now() - tPostprocessStart;

      // 6. Update Telemetry
      this.totalProcessedFrames++;
      this._updateFps(now);

      this.diagnostics = {
        fps: this.diagnostics.fps,
        inferenceLatencyMs: Math.round(inferenceLatencyMs * 10) / 10,
        preprocessLatencyMs: Math.round(preprocessLatencyMs * 10) / 10,
        postprocessLatencyMs: Math.round(postprocessLatencyMs * 10) / 10,
        droppedFrames: this.droppedFrames,
        totalFrames: this.totalProcessedFrames,
        modelName: this.model.name,
        isPlaceholder: this.model.isPlaceholder,
      };

      return {
        allDetections: nmsDetections,
        temporalResult,
        diagnostics: this.diagnostics,
        originalDimensions: {
          width: preprocessed.originalWidth,
          height: preprocessed.originalHeight,
        },
      };
    } catch (err) {
      console.error("Vision inference error:", err);
      return null;
    } finally {
      this.isBusy = false;
    }
  }

  async _inferCloud(frameSource, threshold) {
    try {
      // Draw to temporary canvas to export blob
      const canvas = document.createElement("canvas");
      canvas.width = frameSource.videoWidth || frameSource.naturalWidth || 640;
      canvas.height = frameSource.videoHeight || frameSource.naturalHeight || 480;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(frameSource, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.8));
      const formData = new FormData();
      formData.append("image", blob, "frame.jpg");
      formData.append("confidence_threshold", threshold.toString());

      const res = await axios.post(VisionConfig.cloudApiUrl, formData);
      return res.data?.detections || [];
    } catch (e) {
      console.warn("Cloud fallback inference failed, returning empty:", e);
      return [];
    }
  }

  _updateFps(timestamp) {
    this.fpsWindow.push(timestamp);
    // Keep timestamps within last 1000ms
    const oneSecondAgo = timestamp - 1000;
    while (this.fpsWindow.length > 0 && this.fpsWindow[0] < oneSecondAgo) {
      this.fpsWindow.shift();
    }
    this.diagnostics.fps = this.fpsWindow.length;
  }

  reset() {
    this.temporalTracker.reset();
    this.droppedFrames = 0;
    this.totalProcessedFrames = 0;
    this.fpsWindow = [];
  }
}
