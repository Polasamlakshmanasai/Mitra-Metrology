import { VisionModel } from "./VisionModel";

/**
 * Placeholder / Test Vision Model Adapter.
 * Provides deterministic and realistic candidate detections for testing the entire
 * camera, throttling, NMS, and temporal smoothing pipeline before a custom trained .tflite is plugged in.
 *
 * NOTE: Clearly marked as a placeholder/test adapter as required by specifications.
 */
export class PlaceholderVisionModel extends VisionModel {
  constructor() {
    super("PlaceholderVisionModel (Test Adapter - Awaiting custom model.tflite)");
    this.isPlaceholder = true;
    this.labels = ["bottle", "cup", "packaged commodity", "cell phone", "book", "laptop"];
    this.activeScenarioIndex = 0;
    this.frameCounter = 0;
  }

  async loadModel(_modelPath = null, _labelsPath = null) {
    // Simulates model loading time
    await new Promise((resolve) => setTimeout(resolve, 80));
    this.isLoaded = true;
    return true;
  }

  preprocess(frameData) {
    return frameData;
  }

  /**
   * Generates candidate detections with realistic variation, confidence jitter,
   * and overlapping candidates for NMS testing.
   */
  async infer(preprocessedInput) {
    this.frameCounter++;
    const start = performance.now();

    // Small simulated neural execution delay (e.g. 8-15ms for lightweight model)
    await new Promise((resolve) => setTimeout(resolve, 10));

    const origW = preprocessedInput.originalWidth || 640;
    const origH = preprocessedInput.originalHeight || 480;

    // Deterministic scenario based on frame counter to test stability
    // Cycles every ~120 frames between objects to test transitions
    const cycle = Math.floor(this.frameCounter / 90) % 3;

    let candidateDetections;

    if (cycle === 0) {
      // Scenario A: Central Bottle with high confidence + duplicate overlapping box for NMS
      candidateDetections = [
        {
          label: "bottle",
          confidence: 0.93 + (Math.sin(this.frameCounter * 0.2) * 0.03),
          boundingBox: {
            x: Math.round(origW * 0.35),
            y: Math.round(origH * 0.20),
            width: Math.round(origW * 0.30),
            height: Math.round(origH * 0.60),
          },
        },
        // Overlapping duplicate to test NMS
        {
          label: "bottle",
          confidence: 0.78,
          boundingBox: {
            x: Math.round(origW * 0.36),
            y: Math.round(origH * 0.21),
            width: Math.round(origW * 0.28),
            height: Math.round(origH * 0.58),
          },
        },
      ];
    } else if (cycle === 1) {
      // Scenario B: Packaged Commodity / Box
      candidateDetections = [
        {
          label: "packaged commodity",
          confidence: 0.89 + (Math.cos(this.frameCounter * 0.15) * 0.04),
          boundingBox: {
            x: Math.round(origW * 0.25),
            y: Math.round(origH * 0.25),
            width: Math.round(origW * 0.50),
            height: Math.round(origH * 0.50),
          },
        },
        // Secondary lower-confidence detection: "cup"
        {
          label: "cup",
          confidence: 0.58, // Will test sensitivity threshold!
          boundingBox: {
            x: Math.round(origW * 0.08),
            y: Math.round(origH * 0.55),
            width: Math.round(origW * 0.18),
            height: Math.round(origH * 0.25),
          },
        },
      ];
    } else {
      // Scenario C: Cell phone / Device
      candidateDetections = [
        {
          label: "cell phone",
          confidence: 0.91 + (Math.sin(this.frameCounter * 0.1) * 0.04),
          boundingBox: {
            x: Math.round(origW * 0.32),
            y: Math.round(origH * 0.18),
            width: Math.round(origW * 0.36),
            height: Math.round(origH * 0.64),
          },
        },
      ];
    }

    const inferenceLatencyMs = performance.now() - start;

    return {
      rawDetections: candidateDetections,
      inferenceLatencyMs,
    };
  }

  postprocess(rawOutput) {
    return rawOutput.rawDetections || [];
  }

  close() {
    this.isLoaded = false;
  }
}
