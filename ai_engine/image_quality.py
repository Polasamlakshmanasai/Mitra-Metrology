# image_quality.py

import cv2
import numpy as np


MIN_WIDTH = 500
MIN_HEIGHT = 500
BLUR_THRESHOLD = 80.0


def check_image_quality(image_path: str):
    image = cv2.imread(image_path)

    if image is None:
        return {
            "valid": False,
            "reason": "Unable to read image"
        }

    height, width = image.shape[:2]

    # Resolution check
    if width < 500 or height < 500:
        return {
            "valid": False,
            "reason": "Image resolution is too low"
        }

    # Blur detection
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    blur_score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    if blur_score < 80:
        return {
            "valid": False,
            "reason": "Image is too blurry",
            "blur_score": round(blur_score, 2)
        }

    return {
        "valid": True,
        "width": width,
        "height": height,
        "blur_score": round(blur_score, 2)
    }


def calculate_brightness(image):
    """
    Returns average brightness from 0 to 255.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def calculate_blur(image):
    """
    Variance of Laplacian is a common blur metric.
    Higher = sharper.
    Lower = blurrier.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return float(
        cv2.Laplacian(gray, cv2.CV_64F).var()
    )


def check_resolution(image):
    """
    Checks whether image has enough pixels for OCR.
    """
    height, width = image.shape[:2]

    passed = (
        width >= MIN_WIDTH
        and height >= MIN_HEIGHT
    )

    return {
        "width": width,
        "height": height,
        "passed": passed
    }


def check_brightness(image):
    """
    Checks whether image is too dark or too bright.
    """
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

    return {
        "value": round(brightness, 2),
        "status": status,
        "passed": passed
    }


def check_blur(image):
    """
    Checks image sharpness.
    """
    blur_score = calculate_blur(image)

    return {
        "score": round(blur_score, 2),
        "passed": blur_score >= BLUR_THRESHOLD
    }


def detect_perspective(image):
    """
    Attempts to detect whether the main object/text area
    has strong perspective distortion.

    This is a heuristic, not a legal/compliance decision.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    largest_area = 0
    largest_contour = None

    for contour in contours:

        area = cv2.contourArea(contour)

        if area > largest_area:
            largest_area = area
            largest_contour = contour

    if largest_contour is None:
        return {
            "detected": False,
            "passed": True
        }

    perimeter = cv2.arcLength(
        largest_contour,
        True
    )

    approximation = cv2.approxPolyDP(
        largest_contour,
        0.02 * perimeter,
        True
    )

    # A four-sided contour can represent the product/package.
    is_rectangle_like = len(approximation) == 4

    return {
        "detected": is_rectangle_like,
        "passed": True,
        "vertices": len(approximation)
    }


def check_text_visibility(image):
    """
    Rough estimate of whether enough text-like regions exist.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    threshold = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    text_like_regions = 0

    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)

        if (
            5 <= w <= 500
            and 5 <= h <= 100
            and w / max(h, 1) >= 1.2
        ):
            text_like_regions += 1

    passed = text_like_regions >= 5

    return {
        "text_regions": text_like_regions,
        "passed": passed
    }


def assess_image_quality(image):
    """
    Complete image-quality assessment.
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
        "resolution": resolution,
        "brightness": brightness,
        "blur": blur,
        "perspective": perspective,
        "text_visibility": text_visibility,
        "quality_score": round(quality_score, 2)
    }