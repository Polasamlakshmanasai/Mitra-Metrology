package com.mitra.metrology.classifier

import android.content.Context
import android.graphics.Bitmap

class FoodLabelClassifier private constructor(context: Context) {

    private var activeClassifier: IClassifier = TensorFlowLiteClassifier()

    init {
        activeClassifier.initialize(context)
    }

    companion object {
        @Volatile
        private var instance: FoodLabelClassifier? = null

        fun getInstance(context: Context): FoodLabelClassifier {
            return instance ?: synchronized(this) {
                instance ?: FoodLabelClassifier(context.applicationContext).also { instance = it }
            }
        }
    }

    fun classifyFrame(bitmap: Bitmap, rotationDegrees: Int = 0): List<ClassificationResult> {
        return activeClassifier.classify(bitmap, rotationDegrees)
    }

    fun setConfidenceThreshold(threshold: Float) {
        activeClassifier.confidenceThreshold = threshold.coerceIn(0.1f, 0.99f)
    }

    fun getConfidenceThreshold(): Float = activeClassifier.confidenceThreshold
    fun getModelName(): String = activeClassifier.getModelName()
    fun isModelLoaded(): Boolean = activeClassifier.isModelLoaded()

    fun switchClassifier(newClassifier: IClassifier, context: Context) {
        activeClassifier.close()
        activeClassifier = newClassifier
        activeClassifier.initialize(context)
    }
}
