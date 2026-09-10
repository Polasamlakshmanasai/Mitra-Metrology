package com.mitra.metrology.camera

import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy

class FoodLabelAnalyzer(
    private val onGuidanceUpdate: (FrameQualityMetrics) -> Unit
) : ImageAnalysis.Analyzer {

    private var lastAnalyzedTimestamp = 0L

    override fun analyze(image: ImageProxy) {
        val currentTimestamp = System.currentTimeMillis()
        if (currentTimestamp - lastAnalyzedTimestamp >= 100L) {
            val metrics = FrameQualityGate.evaluate(image)
            onGuidanceUpdate(metrics)
            lastAnalyzedTimestamp = currentTimestamp
        }
        image.close()
    }
}
