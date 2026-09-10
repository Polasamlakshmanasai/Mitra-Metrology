/**
 * Automated Unit Test Suite for Computer Vision Pipeline.
 * Runs in Node.js to verify:
 * 1. Confidence threshold filtering
 * 2. Non-Maximum Suppression (IoU calculation and suppression)
 * 3. Temporal Confirmation state transitions (Searching -> Confirming -> Recognized)
 * 4. Empty and invalid detection handling
 */

import { calculateIoU, applyNMS } from "./NonMaximumSuppression.js";
import { TemporalConfirmation } from "./TemporalConfirmation.js";

let passedCount = 0;
let failedCount = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✓ PASS: ${message}`);
    passedCount++;
  } else {
    console.error(`  ✕ FAIL: ${message}`);
    failedCount++;
  }
}

console.log("\n==========================================");
console.log("RUNNING COMPUTER VISION UNIT TESTS");
console.log("==========================================\n");

// --- TEST 1: IoU Calculation ---
console.log("[1] Testing IoU Calculation:");
const box1 = { x: 10, y: 10, width: 20, height: 20 }; // Area = 400
const box2 = { x: 10, y: 10, width: 20, height: 20 }; // Identical -> IoU = 1.0
assert(Math.abs(calculateIoU(box1, box2) - 1.0) < 0.001, "Identical boxes have IoU of 1.0");

const boxDisjoint = { x: 100, y: 100, width: 20, height: 20 };
assert(calculateIoU(box1, boxDisjoint) === 0, "Disjoint boxes have IoU of 0.0");

const boxPartial = { x: 20, y: 10, width: 20, height: 20 }; // Overlap width 10, height 20 -> area 200. Union: 400+400-200=600 -> 200/600 = 0.333
const iouPartial = calculateIoU(box1, boxPartial);
assert(Math.abs(iouPartial - (1 / 3)) < 0.01, "Partially overlapping boxes calculate correct IoU (~0.33)");

// --- TEST 2: Non-Maximum Suppression (NMS) ---
console.log("\n[2] Testing Non-Maximum Suppression (NMS):");
const candidates = [
  { label: "bottle", confidence: 0.95, boundingBox: { x: 10, y: 10, width: 50, height: 50 } },
  { label: "bottle", confidence: 0.80, boundingBox: { x: 12, y: 12, width: 48, height: 48 } }, // Overlaps heavily with 0.95 bottle -> should be suppressed
  { label: "cup", confidence: 0.85, boundingBox: { x: 12, y: 12, width: 48, height: 48 } }, // Different class -> should NOT be suppressed
  { label: "bottle", confidence: 0.90, boundingBox: { x: 150, y: 150, width: 50, height: 50 } }, // Far away bottle -> should NOT be suppressed
];

const nmsResult = applyNMS(candidates, 0.45, 10);
assert(nmsResult.length === 3, "NMS suppresses duplicate high-overlap detection of same class (expected 3, got " + nmsResult.length + ")");
assert(nmsResult[0].confidence === 0.95, "NMS preserves the highest-confidence detection first");
assert(nmsResult.some((d) => d.label === "cup"), "NMS preserves distinct object classes");

// --- TEST 3: Temporal Confirmation State Machine ---
console.log("\n[3] Testing Temporal Confirmation (Searching -> Confirming -> Recognized):");
const tracker = new TemporalConfirmation(3);

// Frame 1: Low confidence or empty -> Should remain SEARCHING
let t1 = tracker.process([], 0.70, 3);
assert(t1.status === "SEARCHING", "Initial state is SEARCHING");

// Frame 2: Top detection with conf 0.92 -> Should enter CONFIRMING (1/3)
const bottleDet = [{ label: "bottle", confidence: 0.92, boundingBox: { x: 10, y: 10, width: 20, height: 40 } }];
let t2 = tracker.process(bottleDet, 0.70, 3);
assert(t2.status === "CONFIRMING" && t2.consecutiveHits === 1, "First valid detection transitions to CONFIRMING (1/3)");

// Frame 3: Same detection -> CONFIRMING (2/3)
let t3 = tracker.process(bottleDet, 0.70, 3);
assert(t3.status === "CONFIRMING" && t3.consecutiveHits === 2, "Second consecutive detection is CONFIRMING (2/3)");

// Frame 4: Same detection -> RECOGNIZED (3/3)
let t4 = tracker.process(bottleDet, 0.70, 3);
assert(t4.status === "RECOGNIZED" && t4.consecutiveHits === 3, "Third consecutive detection transitions to RECOGNIZED");
assert(t4.confirmedDetection.label === "bottle", "Confirmed detection matches tracked object");

// Frame 5: Object disappears -> Graceful degradation
let t5 = tracker.process([], 0.70, 3);
assert(t5.consecutiveHits === 2, "Disappearance decrements consecutive count without instant glitch");

// --- TEST 4: Edge Cases & Empty/Invalid Detections ---
console.log("\n[4] Testing Empty / Invalid Detections Handling:");
assert(applyNMS([], 0.45).length === 0, "applyNMS handles empty list safely");
assert(applyNMS(null, 0.45).length === 0, "applyNMS handles null safely");
const emptyTracker = new TemporalConfirmation(3);
const emptyRes = emptyTracker.process(null, 0.70, 3);
assert(emptyRes.status === "SEARCHING", "TemporalConfirmation handles null detections safely");

console.log("\n==========================================");
console.log(`TEST SUMMARY: ${passedCount} PASSED, ${failedCount} FAILED`);
console.log("==========================================\n");

if (failedCount > 0) {
  process.exit(1);
}
