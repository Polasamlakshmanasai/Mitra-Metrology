package com.mitra.metrology.classifier

import android.graphics.RectF

data class ClassificationResult(
    val label: String,
    val confidence: Float,
    val index: Int = -1,
    val boundingBox: RectF? = null
)
