package com.mitra.metrology.classifier

import android.content.Context
import android.graphics.Bitmap

interface IClassifier {
    var confidenceThreshold: Float

    fun initialize(context: Context)
    fun classify(bitmap: Bitmap, rotationDegrees: Int = 0): List<ClassificationResult>
    fun isModelLoaded(): Boolean
    fun getModelName(): String
    fun close()
}
