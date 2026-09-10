# preprocessing.py
"""
Image Preprocessing Pipeline for Packaged Commodity OCR & Computer Vision.
Handles illumination correction, noise filtering, contrast enhancement, and binarization.
"""

import cv2
import numpy as np


def convert_to_grayscale(image):
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


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


def preprocess_image(image):
    """
    Main preprocessing entry point.
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
    denoised = denoise_image(gray)
    enhanced = enhance_contrast(denoised)
    skew_corrected = correct_skew(enhanced)
    thresholded = adaptive_threshold(skew_corrected)

    return {
        "original": image,
        "gray": gray,
        "enhanced": skew_corrected,
        "thresholded": thresholded
    }
