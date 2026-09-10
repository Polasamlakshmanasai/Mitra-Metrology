# barcode.py

import cv2


def detect_barcodes(image):

    results = []

    try:

        detector = cv2.barcode.BarcodeDetector()

        decoded_info, decoded_type, points = (
            detector.detectAndDecode(image)
        )

        if decoded_info is None:
            return results

        if isinstance(decoded_info, str):
            decoded_info = [decoded_info]

        if decoded_type is None:
            decoded_type = []

        for index, value in enumerate(decoded_info):

            if not value:
                continue

            barcode_type = (
                decoded_type[index]
                if index < len(decoded_type)
                else "UNKNOWN"
            )

            bbox = None

            if points is not None and index < len(points):

                point_set = points[index]

                x_values = [
                    int(point[0])
                    for point in point_set
                ]

                y_values = [
                    int(point[1])
                    for point in point_set
                ]

                x1 = min(x_values)
                y1 = min(y_values)
                x2 = max(x_values)
                y2 = max(y_values)

                bbox = {
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1
                }

            results.append({
                "value": value,
                "type": barcode_type,
                "bbox": bbox
            })

    except Exception as error:
        # Barcode detector is optional/heuristic; return empty list gracefully
        return []

    return results