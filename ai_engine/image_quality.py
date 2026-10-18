# image_quality.py
"""
Image Quality Assessment for Packaged Commodity OCR.

v2 changes:
  - check_image_quality() now returns a rich quality_summary dict with:
      quality_tier: "GOOD" | "POOR" | "VERY_POOR"
      needs_retake_prompt: bool
      can_proceed: bool  (always True — user decides)
      quality_score: 0.0–1.0
      rejection_reasons, warning_reasons
  - Thresholds are deliberately non-aggressive:
      GOOD      — quality_score >= 0.55
      POOR      — quality_score  0.25–0.54  (show single retake prompt)
      VERY_POOR — quality_score  < 0.25    (strongly recommend retake, still allow proceed)
  - assess_image_quality() (used by food_label.py) is unchanged.
"""

import cv2
import numpy as np


MIN_WIDTH = 300        # relaxed from 500 — real phone photos are usually fine
MIN_HEIGHT = 300
BLUR_THRESHOLD_GOOD = 60.0    # Laplacian variance — GOOD if >= 60
BLUR_THRESHOLD_POOR = 20.0    # below 20 → VERY_POOR


def _to_gray(image):
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def check_image_quality(image_path: str) -> dict:
    """
    Gate check returning a rich quality summary.

    Quality tiers (non-aggressive):
      GOOD      — quality_score >= 0.55  → proceed normally
      POOR      — quality_score  0.25–0.54 → show one retake prompt
      VERY_POOR — quality_score < 0.25   → strongly recommend retake; still allow proceed

    Returns:
    {
        "valid":               bool,      # True if GOOD or POOR (can_proceed covers VERY_POOR)
        "quality_tier":        str,       # "GOOD" | "POOR" | "VERY_POOR"
        "quality_score":       float,     # 0.0 – 1.0 composite
        "blur_score":          float,     # Laplacian variance
        "brightness":          float,     # mean pixel brightness 0–255
        "contrast_score":      float,     # stddev / 128 clamped 0–1
        "resolution_ok":       bool,
        "width":               int,
        "height":              int,
        "rejection_reasons":   list[str], # hard failures
        "warning_reasons":     list[str], # soft warnings
        "needs_retake_prompt": bool,      # True if POOR or VERY_POOR
        "can_proceed":         bool,      # always True (user decides)
        "reason":              str,       # backward-compat single reason string
    }
    """
    image = cv2.imread(image_path)
    if image is None:
        return _make_result(
            tier="VERY_POOR", score=0.0,
            blur=0.0, brightness=0.0, contrast=0.0,
            width=0, height=0,
            rejections=["Unable to read image file"],
            warnings=[]
        )

    gray = _to_gray(image)
    height, width = gray.shape[:2]

    rejection_reasons = []
    warning_reasons = []
    score_penalties = 0.0   # subtract from 1.0

    # ── Resolution ────────────────────────────────────────────────
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        rejection_reasons.append(
            f"Resolution too low ({width}×{height}px). Minimum: {MIN_WIDTH}×{MIN_HEIGHT}px."
        )
        score_penalties += 0.40
    elif width < 500 or height < 500:
        warning_reasons.append(
            f"Resolution is acceptable but low ({width}×{height}px). Higher resolution improves accuracy."
        )
        score_penalties += 0.12

    # ── Blur (Laplacian variance) ──────────────────────────────────
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_score < BLUR_THRESHOLD_POOR:
        rejection_reasons.append(
            f"Image is severely blurry (sharpness score: {blur_score:.1f}). Minimum recommended: {BLUR_THRESHOLD_GOOD}."
        )
        score_penalties += 0.45
    elif blur_score < BLUR_THRESHOLD_GOOD:
        warning_reasons.append(
            f"Image is slightly blurry (sharpness score: {blur_score:.1f}). Try a steadier capture."
        )
        score_penalties += 0.20

    # ── Brightness ─────────────────────────────────────────────────
    brightness = float(np.mean(gray))
    if brightness < 30:
        rejection_reasons.append(
            f"Image is too dark (brightness: {brightness:.1f}/255). Move to better lighting."
        )
        score_penalties += 0.30
    elif brightness < 55:
        warning_reasons.append(
            f"Image is somewhat dark (brightness: {brightness:.1f}/255). Better lighting will improve OCR."
        )
        score_penalties += 0.10
    elif brightness > 235:
        rejection_reasons.append(
            f"Image is overexposed/washed out (brightness: {brightness:.1f}/255)."
        )
        score_penalties += 0.25
    elif brightness > 210:
        warning_reasons.append(
            f"Image has slight overexposure (brightness: {brightness:.1f}/255). Reduce glare if possible."
        )
        score_penalties += 0.08

    # ── Contrast ───────────────────────────────────────────────────
    contrast_score = float(np.std(gray)) / 128.0
    contrast_score = min(1.0, contrast_score)
    if contrast_score < 0.15:
        warning_reasons.append(
            f"Very low contrast detected (score: {contrast_score:.2f}). Text may be hard to distinguish."
        )
        score_penalties += 0.15
    elif contrast_score < 0.25:
        warning_reasons.append(
            f"Low contrast (score: {contrast_score:.2f}). Label text may be faint."
        )
        score_penalties += 0.07

    quality_score = round(max(0.0, 1.0 - score_penalties), 3)

    return _make_result(
        tier=_tier_from_score(quality_score),
        score=quality_score,
        blur=round(blur_score, 2),
        brightness=round(brightness, 2),
        contrast=round(contrast_score, 3),
        width=width,
        height=height,
        rejections=rejection_reasons,
        warnings=warning_reasons
    )


def _tier_from_score(score: float) -> str:
    if score >= 0.55:
        return "GOOD"
    elif score >= 0.25:
        return "POOR"
    else:
        return "VERY_POOR"


def _make_result(tier, score, blur, brightness, contrast,
                 width, height, rejections, warnings) -> dict:
    needs_prompt = tier in ("POOR", "VERY_POOR")
    # backward-compat "valid" field: True unless we literally cannot read the file
    # or the image is so bad OCR is pointless. We set valid=False only for VERY_POOR.
    valid = (tier != "VERY_POOR")

    # Compose backward-compat single reason
    reason = "; ".join(rejections) if rejections else ("; ".join(warnings) if warnings else "")

    return {
        "valid":               valid,
        "quality_tier":        tier,
        "quality_score":       score,
        "blur_score":          blur,
        "brightness":          brightness,
        "contrast_score":      contrast,
        "resolution_ok":       (width >= MIN_WIDTH and height >= MIN_HEIGHT),
        "width":               width,
        "height":              height,
        "rejection_reasons":   rejections,
        "warning_reasons":     warnings,
        "needs_retake_prompt": needs_prompt,
        "can_proceed":         True,   # always — user decides
        "reason":              reason,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Legacy / food_label.py compatible functions below — ALL UNCHANGED
# ══════════════════════════════════════════════════════════════════════════════

def calculate_brightness(image):
    gray = _to_gray(image)
    return float(np.mean(gray))


def calculate_blur(image):
    gray = _to_gray(image)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def check_resolution(image):
    height, width = image.shape[:2]
    passed = (width >= 500 and height >= 500)
    return {"width": width, "height": height, "passed": passed}


def check_brightness(image):
    brightness = calculate_brightness(image)
    if brightness < 50:
        status = "too_dark"
        passed = False
    elif brightness > 220:
        status = "too_bright"
        passed = False
    else:
        status = "good"
        passed = True
    return {"value": round(brightness, 2), "status": status, "passed": passed}


def check_blur(image):
    blur_score = calculate_blur(image)
    return {"score": round(blur_score, 2), "passed": blur_score >= 80.0}


def detect_perspective(image):
    gray = _to_gray(image)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_area = 0
    largest_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > largest_area:
            largest_area = area
            largest_contour = contour
    if largest_contour is None:
        return {"detected": False, "passed": True}
    perimeter = cv2.arcLength(largest_contour, True)
    approximation = cv2.approxPolyDP(largest_contour, 0.02 * perimeter, True)
    is_rectangle_like = len(approximation) == 4
    return {"detected": is_rectangle_like, "passed": True, "vertices": len(approximation)}


def check_text_visibility(image):
    gray = _to_gray(image)
    threshold = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 11
    )
    contours, _ = cv2.findContours(threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    text_like_regions = 0
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if 5 <= w <= 500 and 5 <= h <= 100 and w / max(h, 1) >= 1.2:
            text_like_regions += 1
    return {"text_regions": text_like_regions, "passed": text_like_regions >= 5}


def assess_image_quality(image):
    """
    Comprehensive image quality assessment — used by food_label.py.
    UNCHANGED from v1.
    """
    resolution = check_resolution(image)
    brightness = check_brightness(image)
    blur = check_blur(image)
    perspective = detect_perspective(image)
    text_visibility = check_text_visibility(image)

    passed_checks = sum([
        resolution["passed"],
        brightness["passed"],
        blur["passed"],
        perspective["passed"],
        text_visibility["passed"]
    ])
    total_checks = 5
    quality_score = passed_checks / total_checks

    return {
        "resolution":      resolution,
        "brightness":      brightness,
        "blur":            blur,
        "perspective":     perspective,
        "text_visibility": text_visibility,
        "quality_score":   round(quality_score, 2)
    }