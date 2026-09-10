/**
 * Temporal Confirmation & Stability Tracker.
 * Mitigates camera noise and flicker by requiring an object detection to remain
 * consistently observed across N consecutive frames before confirming recognition.
 */
export class TemporalConfirmation {
  constructor(requiredStableFrames = 3) {
    this.requiredStableFrames = requiredStableFrames;
    this.currentCandidate = null;
    this.consecutiveHits = 0;
    this.status = "SEARCHING"; // 'SEARCHING' | 'CONFIRMING' | 'RECOGNIZED'
    this.confirmedDetection = null;
  }

  /**
   * Evaluates new frame detections against historical stability.
   * @param {Array} detections - List of NMS-filtered detections for current frame
   * @param {number} confidenceThreshold
   * @param {number} requiredFrames
   * @returns {Object} { status, confirmedDetection, candidateLabel, consecutiveHits, requiredFrames, statusMessage }
   */
  process(detections, confidenceThreshold = 0.70, requiredFrames = 3) {
    this.requiredStableFrames = requiredFrames;

    // Filter by threshold
    const validDetections = (detections || []).filter(
      (d) => d.confidence >= confidenceThreshold
    );

    // If no detection passes threshold:
    if (validDetections.length === 0) {
      if (this.consecutiveHits > 0) {
        this.consecutiveHits--; // Graceful decay to avoid sudden dropout
      }
      if (this.consecutiveHits === 0) {
        this.status = "SEARCHING";
        this.currentCandidate = null;
        this.confirmedDetection = null;
      }
      return {
        status: this.status,
        confirmedDetection: this.confirmedDetection,
        candidateLabel: this.currentCandidate?.label || null,
        consecutiveHits: this.consecutiveHits,
        requiredFrames: this.requiredStableFrames,
        statusMessage: "Searching...",
      };
    }

    // Pick top detection
    const topDetection = validDetections[0];

    // Check if same class as candidate in previous frame
    if (this.currentCandidate && this.currentCandidate.label === topDetection.label) {
      this.consecutiveHits++;
    } else {
      // New candidate class detected
      this.currentCandidate = topDetection;
      this.consecutiveHits = 1;
    }

    // Determine state
    if (this.consecutiveHits >= this.requiredStableFrames) {
      this.status = "RECOGNIZED";
      this.confirmedDetection = topDetection;
      return {
        status: "RECOGNIZED",
        confirmedDetection: topDetection,
        candidateLabel: topDetection.label,
        consecutiveHits: this.consecutiveHits,
        requiredFrames: this.requiredStableFrames,
        statusMessage: `Recognized: ${topDetection.label.toUpperCase()} (${Math.round(topDetection.confidence * 100)}%)`,
      };
    } else {
      this.status = "CONFIRMING";
      return {
        status: "CONFIRMING",
        confirmedDetection: null,
        candidateLabel: topDetection.label,
        consecutiveHits: this.consecutiveHits,
        requiredFrames: this.requiredStableFrames,
        statusMessage: `Confirming (${this.consecutiveHits}/${this.requiredStableFrames})...`,
      };
    }
  }

  reset() {
    this.status = "SEARCHING";
    this.currentCandidate = null;
    this.consecutiveHits = 0;
    this.confirmedDetection = null;
  }
}
