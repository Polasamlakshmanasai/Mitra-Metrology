# preprocessing.py
"""
Image Preprocessing Pipeline for Packaged Commodity OCR & Computer Vision.
Handles illumination correction, noise filtering, contrast enhancement, and binarization.

v2 additions:
  - generate_preprocessing_variants(): produces 4 named variants for field-level multi-OCR
  - All existing functions and preprocess_image() are unchanged.
"""

import cv2
import numpy as np


MIN_WIDTH = 500
MIN_HEIGHT = 500
BLUR_THRESHOLD = 80.0


def convert_to_grayscale(image):
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def correct_illumination_and_brighten(gray):
    """
    Adaptive gamma & illumination boost for dark, shadowed, or under-exposed packaging images.
    If the average luminance is low (mean < 125), applies non-linear gamma expansion
    to lift dark shadows and reveal faint packaging declarations without washing out highlights.
    """
    mean_val = float(np.mean(gray))
    if mean_val < 125:
        gamma = max(0.40, min(0.95, mean_val / 130.0))
        table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype("uint8")
        return cv2.LUT(gray, table)
    return gray


def enhance_contrast(gray):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    to normalize lighting across curved or glossy packaging surfaces.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def denoise_image(gray):
    """
    Bilateral filter removes high-frequency surface noise while preserving sharp text edges.
    """
    return cv2.bilateralFilter(gray, 9, 75, 75)


def adaptive_threshold(gray):
    """
    Adaptive thresholding for high-contrast character segmentation.
    """
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )


def correct_skew(gray):
    """
    Detect text orientation and rotate image upright if skewed.
    """
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) < 100:
        return gray

    angle = 0.0
    try:
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) > 0.5 and abs(angle) < 45:
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            return cv2.warpAffine(
                gray,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
    except Exception:
        pass
    return gray


def _resize_for_ocr(image):
    """
    Ensures image is between 800–2400px on the longest side.
    Returns resized numpy array. Input can be color or grayscale.
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest < 800:
        scale = 800.0 / longest
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    elif longest > 2400:
        scale = 2400.0 / longest
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image


def _sharpen(gray):
    """
    Unsharp mask sharpening — makes fine printed text crisper.
    """
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def generate_preprocessing_variants(image):
    """
    Generates 4 named preprocessing variants for multi-variant OCR.
    Each variant is optimised for a different label/lighting condition.

    Returns dict:
    {
        "clahe":     <grayscale ndarray>  — standard pipeline (best for most labels)
        "otsu":      <grayscale ndarray>  — CLAHE + Otsu global threshold (high contrast)
        "sharp":     <grayscale ndarray>  — bilateral + unsharp mask (fine text)
        "inverted":  <grayscale ndarray>  — inverted (dark-background / white-text labels)
    }

    The returned images are ready to be passed directly to pytesseract or run_ocr().
    """
    # Ensure image is a color or grayscale numpy array
    if isinstance(image, str):
        image = cv2.imread(image)
        if image is None:
            raise ValueError(f"Cannot read image from path: {image}")

    image = _resize_for_ocr(image)
    gray = convert_to_grayscale(image)
    brightened = correct_illumination_and_brighten(gray)

    # Variant 1: CLAHE (standard — best all-rounder for packaging labels)
    denoised = denoise_image(brightened)
    clahe_img = enhance_contrast(denoised)
    clahe_img = correct_skew(clahe_img)

    # Variant 2: Otsu global threshold on CLAHE result (high-contrast / b&w labels)
    _, otsu_img = cv2.threshold(
        enhance_contrast(gray),
        0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Variant 3: Bilateral denoising + unsharp mask sharpening (fine print)
    sharp_img = _sharpen(denoise_image(brightened))
    sharp_img = enhance_contrast(sharp_img)

    # Variant 4: Inverted (white text on dark/coloured label backgrounds)
    inverted_img = cv2.bitwise_not(clahe_img)

    return {
        "clahe":    clahe_img,
        "otsu":     otsu_img,
        "sharp":    sharp_img,
        "inverted": inverted_img,
    }


def preprocess_image(image):
    """
    Main preprocessing entry point — UNCHANGED from v1 for backward compatibility.
    Accepts either an image path string or a numpy array.
    """
    if isinstance(image, str):
        image_path = image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Unable to read image from path: {image_path}")

    if image is None:
        raise ValueError("Input image is None")

    # Resize if needed to ensure optimal OCR resolution (minimum 800px width/height)
    h, w = image.shape[:2]
    scale = 1.0
    if max(h, w) < 800:
        scale = 800.0 / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    elif max(h, w) > 2400:
        scale = 2400.0 / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    gray = convert_to_grayscale(image)
    brightened = correct_illumination_and_brighten(gray)
    denoised = denoise_image(brightened)
    enhanced = enhance_contrast(denoised)
    skew_corrected = correct_skew(enhanced)
    thresholded = adaptive_threshold(skew_corrected)

    return {
        "original":    image,
        "gray":        gray,
        "brightened":  brightened,
        "enhanced":    skew_corrected,
        "thresholded": thresholded
    }
