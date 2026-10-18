# backend/tests/test_image_quality.py
"""
Automated unit and integration tests for Image Quality Assessment (image_quality.py).
Tests:
- Clear image assessment (Tier GOOD, can_proceed True, no retake prompt)
- Blurry image detection (Laplacian variance threshold, retake prompt)
- Low resolution image detection
- Dark / underexposed image detection
- Overexposed / washed-out image detection
- Force proceed / Continue anyway behavior
- Quality warning persistence into compliance pipeline
"""

import cv2
import numpy as np
import pytest

from ai_engine.image_quality import check_image_quality
from app.services.compliance_service import analyze_product


def test_clear_image_quality(compliant_package_path):
    """Verify that a high-contrast, sharp package image is rated GOOD."""
    q = check_image_quality(str(compliant_package_path))
    assert isinstance(q, dict)
    assert q["quality_tier"] == "GOOD"
    assert q["can_proceed"] is True
    assert q["needs_retake_prompt"] is False
    assert q["blur_score"] > 60.0
    assert q["resolution_ok"] is True


def test_blurry_image_detection(blurry_package_path):
    """Verify that a severely blurry image is rated VERY_POOR with retake prompt."""
    q = check_image_quality(str(blurry_package_path))
    assert q["quality_tier"] in ("POOR", "VERY_POOR")
    assert q["needs_retake_prompt"] is True
    assert q["blur_score"] < 60.0
    assert any("blurry" in r.lower() for r in q["rejection_reasons"] + q["warning_reasons"])


def test_synthetic_severe_blur_detection(create_synthetic_image):
    """Generate synthetic image with strong Gaussian blur and verify detection."""
    lines = ["ORGANIC WHEAT FLOUR", "MRP Rs 150.00", "NET QTY: 1 kg"]
    blurry_path = create_synthetic_image(lines=lines, blur_radius=14, filename="severe_blur.jpg")

    q = check_image_quality(str(blurry_path))
    assert q["quality_tier"] in ("POOR", "VERY_POOR")
    assert q["needs_retake_prompt"] is True
    assert q["blur_score"] < 30.0


def test_low_resolution_image_detection(create_synthetic_image):
    """Images below 300x300 should trigger resolution warnings."""
    low_res_path = create_synthetic_image(lines=["ATTA 1kg"], width=180, height=180, filename="low_res.jpg")

    q = check_image_quality(str(low_res_path))
    assert q["resolution_ok"] is False
    assert any("resolution" in r.lower() for r in q["rejection_reasons"] + q["warning_reasons"])


def test_dark_underexposed_image_detection(create_synthetic_image):
    """Images with very low mean brightness should trigger underexposed rejection."""
    dark_path = create_synthetic_image(
        lines=["NET QTY 500g"],
        bg_color=(20, 20, 20),
        text_color=(60, 60, 60),
        filename="dark_image.jpg"
    )

    q = check_image_quality(str(dark_path))
    assert q["brightness"] < 40.0
    assert any("dark" in r.lower() for r in q["rejection_reasons"] + q["warning_reasons"])


def test_overexposed_washed_out_detection(create_synthetic_image):
    """Images with extremely high brightness and low contrast should trigger overexposed warning."""
    overexposed_path = create_synthetic_image(
        lines=["MRP Rs 200"],
        bg_color=(255, 255, 255),
        text_color=(235, 235, 235),
        filename="overexposed.jpg"
    )

    q = check_image_quality(str(overexposed_path))
    assert q["brightness"] > 240.0
    assert any("overexposed" in r.lower() or "contrast" in r.lower() for r in q["rejection_reasons"] + q["warning_reasons"])


def test_force_proceed_continue_anyway(blurry_package_path):
    """Test that force_proceed=True bypasses the quality gate and completes the analysis pipeline."""
    res_normal = analyze_product(str(blurry_package_path), force_proceed=False)
    # Even if blocked or prompted, force_proceed=True should complete
    res_forced = analyze_product(str(blurry_package_path), force_proceed=True)

    assert isinstance(res_forced, dict)
    assert res_forced["can_proceed"] is True
    assert "status" in res_forced
    assert "fields" in res_forced
    assert "violations" in res_forced
    assert res_forced["image_quality_warning"] is not None
