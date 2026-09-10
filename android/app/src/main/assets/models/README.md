# Neural Network Model Directory (TensorFlow Lite)

## Quick Start
Place your trained TensorFlow Lite model file in this directory with the name:
`model.tflite`

Full file path:
`Mitra-Metrology/android/app/src/main/assets/models/model.tflite`

## Model Specifications & Input Tensor Shape
- **Expected Dimensions**: `1 x 224 x 224 x 3` (or `1 x 300 x 300 x 3` / `1 x 640 x 640 x 3` depending on architecture)
- **Data Type**: Float32 (normalized [0, 1] or [-1, 1]) or Uint8 (quantized)
- **Output Classes**: Maps to `labels.txt` in the same directory:
  1. `Nutrition_Facts_Table`
  2. `Ingredients_List`
  3. `Veg_Green_Dot`
  4. `NonVeg_Brown_Triangle`
  5. `FSSAI_License_Logo`
  6. `AGMARK_Seal`
  7. `Fortified_F_Logo`
  8. `Net_Quantity_MRP_Box`
  9. `Barcode_EAN13`
  10. `Batch_Date_Stamp`
  11. `Manufacturer_Address_Block`

## Clean Architecture - How to Replace the Model
The Android app uses the `IClassifier` interface located in:
`app/src/main/java/com/mitra/metrology/classifier/IClassifier.kt`

To replace or swap models at runtime or compile time:
1. Implement `IClassifier` or extend `TensorFlowLiteClassifier`.
2. Update the model asset filename in `FoodLabelClassifier.kt` (or call `switchModel(...)`).
3. Set your desired confidence threshold in code via `classifier.confidenceThreshold = 0.65f` or via the interactive in-app threshold slider.
