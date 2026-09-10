/**
 * Non-Maximum Suppression (NMS) for object detection bounding boxes.
 * Prevents redundant, overlapping detections of the same object.
 */

/**
 * Calculates Intersection-over-Union (IoU) of two bounding boxes.
 * Boxes are objects with { x, y, width, height } in coordinate space.
 */
export function calculateIoU(boxA, boxB) {
  const x1 = Math.max(boxA.x, boxB.x);
  const y1 = Math.max(boxA.y, boxB.y);
  const x2 = Math.min(boxA.x + boxA.width, boxB.x + boxB.width);
  const y2 = Math.min(boxA.y + boxA.height, boxB.y + boxB.height);

  const intersectionArea = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const areaA = boxA.width * boxA.height;
  const areaB = boxB.width * boxB.height;

  const unionArea = areaA + areaB - intersectionArea;
  if (unionArea <= 0) return 0;

  return intersectionArea / unionArea;
}

/**
 * Applies Non-Maximum Suppression to filter candidate detections.
 * @param {Array} detections - List of detections: [{ label, confidence, boundingBox }]
 * @param {number} iouThreshold - Overlap threshold above which lower-confidence boxes are suppressed (e.g. 0.45)
 * @param {number} maxDetections - Maximum number of detections to retain
 * @returns {Array} Suppressed detections
 */
export function applyNMS(detections, iouThreshold = 0.45, maxDetections = 10) {
  if (!detections || detections.length === 0) return [];

  // Sort descending by confidence
  const sorted = [...detections].sort((a, b) => b.confidence - a.confidence);
  const selected = [];

  while (sorted.length > 0 && selected.length < maxDetections) {
    const best = sorted.shift();
    selected.push(best);

    // Filter out remaining boxes that have high overlap with the chosen box
    for (let i = sorted.length - 1; i >= 0; i--) {
      const candidate = sorted[i];

      // Suppress if same class and IoU exceeds threshold
      if (candidate.label === best.label) {
        const iou = calculateIoU(best.boundingBox, candidate.boundingBox);
        if (iou >= iouThreshold) {
          sorted.splice(i, 1);
        }
      }
    }
  }

  return selected;
}
