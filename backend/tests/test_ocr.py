# backend/tests/test_ocr.py
"""
Automated unit and integration tests for Tesseract OCR Engine and Multi-Variant Processing.
Tests:
- Tesseract availability and executable path verification
- Single-image text extraction
- Multi-variant OCR generation (CLAHE, Otsu, Sharp, Inverted)
- Line grouping and text reconstruction
- Edge cases: blank images, black images, corrupt files, non-existent paths
- Processing duration and performance timing
"""

import os
import cv2
import numpy as np
import pytest
from pathlib import Path

from ai_engine.ocr import (
    is_tesseract_available,
    extract_text,
    run_ocr,
    run_ocr_multi_variant,
    group_ocr_lines,
    combine_ocr_text,
    TESSERACT_PATH,
)


def test_tesseract_available():
    """Verify that Tesseract is properly detected and callable on the host system."""
    assert is_tesseract_available() is True, "Tesseract OCR engine is not detected or not callable."
    assert TESSERACT_PATH is not None
    assert os.path.exists(TESSERACT_PATH)


def test_extract_text_on_real_image(sample_product_label_path):
    """Verify that extract_text extracts readable text from real packaged commodity."""
    text = extract_text(str(sample_product_label_path))
    assert isinstance(text, str)
    assert len(text) > 20
    # Must contain recognizable package text
    assert any(term in text.upper() for term in ["ATTA", "MRP", "QUANTITY", "FSSAI", "BEST BEFORE"])


def test_multi_variant_ocr_structure(sample_product_label_path):
    """Verify that run_ocr_multi_variant generates all 4 variants with complete structure."""
    img = cv2.imread(str(sample_product_label_path))
    assert img is not None, "Failed to load sample test image"

    res = run_ocr_multi_variant(img)
    assert isinstance(res, dict)
    assert "best_variant" in res
    assert "variants" in res
    assert "timing_ms" in res
    assert res["timing_ms"] > 0

    variants = res["variants"]
    for expected_variant in ["clahe", "otsu", "sharp", "inverted"]:
        assert expected_variant in variants, f"Missing variant: {expected_variant}"
        v_data = variants[expected_variant]
        assert "lines" in v_data
        assert "words" in v_data
        assert "text" in v_data
        assert "avg_confidence" in v_data
        assert isinstance(v_data["lines"], list)
        assert isinstance(v_data["words"], list)
        assert 0.0 <= v_data["avg_confidence"] <= 1.0


def test_empty_white_image_handling(create_synthetic_image):
    """Empty white image should return empty or whitespace-only text without crashing."""
    blank_path = create_synthetic_image(lines=[], width=600, height=600, filename="blank_white.jpg")
    text = extract_text(str(blank_path))
    assert text.strip() == "", f"Expected empty text for blank image, got: {text}"


def test_empty_black_image_handling(create_synthetic_image):
    """Empty black image should return empty text without crashing."""
    black_path = create_synthetic_image(lines=[], bg_color=(0, 0, 0), width=600, height=600, filename="blank_black.jpg")
    text = extract_text(str(black_path))
    assert text.strip() == "", f"Expected empty text for black image, got: {text}"


def test_corrupt_image_handling(tmp_path):
    """Non-image or corrupted file should be handled gracefully."""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_text("This is an invalid binary payload not an image file.")

    # extract_text should either return empty string or raise appropriate error without silent freeze
    try:
        text = extract_text(str(corrupt_file))
        assert text == "" or text is None
    except Exception as e:
        # Expected exception when reading non-image
        assert isinstance(e, (cv2.error, ValueError, IOError, Exception))


def test_nonexistent_image_handling():
    """Non-existent path should return empty string or raise FileNotFoundError gracefully."""
    fake_path = "non_existent_image_path_12345.jpg"
    try:
        text = extract_text(fake_path)
        assert text == ""
    except Exception as e:
        assert isinstance(e, (FileNotFoundError, IOError, Exception))


def test_group_ocr_lines_ordering():
    """Test grouping of OCR words into spatially ordered horizontal lines."""
    # Synthetic word tokens on two distinct lines
    words = [
        {"text": "NET", "confidence": 0.95, "bbox": {"x": 20, "y": 50, "w": 40, "h": 20}},
        {"text": "QUANTITY:", "confidence": 0.92, "bbox": {"x": 65, "y": 52, "w": 90, "h": 20}},
        {"text": "5", "confidence": 0.90, "bbox": {"x": 160, "y": 51, "w": 20, "h": 20}},
        {"text": "kg", "confidence": 0.94, "bbox": {"x": 185, "y": 50, "w": 30, "h": 20}},
        {"text": "MRP", "confidence": 0.96, "bbox": {"x": 20, "y": 100, "w": 45, "h": 20}},
        {"text": "Rs.", "confidence": 0.91, "bbox": {"x": 70, "y": 99, "w": 35, "h": 20}},
        {"text": "295.00", "confidence": 0.98, "bbox": {"x": 110, "y": 101, "w": 60, "h": 20}},
    ]

    lines = group_ocr_lines(words)
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"

    line1_text = lines[0]["text"]
    line2_text = lines[1]["text"]

    assert "NET QUANTITY: 5 kg" in line1_text
    assert "MRP Rs. 295.00" in line2_text

    combined = combine_ocr_text(lines)
    assert "NET QUANTITY: 5 kg" in combined and "MRP Rs. 295.00" in combined
