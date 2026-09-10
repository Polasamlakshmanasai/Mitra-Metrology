# main.py

import cv2
import json
import os

from image_quality import assess_image_quality
from preprocessing import preprocess_image
from ocr import run_ocr, group_ocr_lines, combine_ocr_text
from extraction import extract_fields
from confidence import add_confidence_to_fields
from barcode import detect_barcodes


def process_product_image(image_path):

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            "Could not read image."
        )

    # --------------------------------------------------
    # 1. IMAGE QUALITY
    # --------------------------------------------------

    quality = assess_image_quality(image)

    # --------------------------------------------------
    # 2. PREPROCESSING
    # --------------------------------------------------

    processed = preprocess_image(image)

    # Use enhanced image for OCR.
    ocr_image = processed["enhanced"]

    # --------------------------------------------------
    # 3. OCR
    # --------------------------------------------------

    ocr_results = run_ocr(ocr_image)

    ocr_lines = group_ocr_lines(
        ocr_results
    )

    complete_text = combine_ocr_text(
        ocr_results
    )

    # --------------------------------------------------
    # 4. FIELD EXTRACTION
    # --------------------------------------------------

    fields = extract_fields(
        ocr_lines
    )

    # --------------------------------------------------
    # 5. CONFIDENCE
    # --------------------------------------------------

    fields_with_confidence = (
        add_confidence_to_fields(
            fields,
            quality["quality_score"]
        )
    )

    # --------------------------------------------------
    # 6. BARCODE
    # --------------------------------------------------

    barcodes = detect_barcodes(
        image
    )

    # --------------------------------------------------
    # 7. FINAL RESULT
    # --------------------------------------------------

    result = {
        "image": {
            "source": image_path,
            "quality": quality
        },

        "ocr": {
            "text": complete_text,
            "words": ocr_results,
            "lines": ocr_lines
        },

        "fields": fields_with_confidence,

        "barcodes": barcodes
    }

    return result


def main():

    image_path = "sample_images/product.jpg"

    result = process_product_image(
        image_path
    )

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )

    with open(
        "output.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False
        )


if __name__ == "__main__":
    main()