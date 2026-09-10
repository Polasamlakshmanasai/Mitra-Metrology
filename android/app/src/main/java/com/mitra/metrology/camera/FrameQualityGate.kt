package com.mitra.metrology.camera

import androidx.camera.core.ImageProxy
import kotlin.math.abs

enum class GuidanceState(val message: String, val canCapture: Boolean) {
    MOVE_CLOSER("Move closer — fill frame with label", false),
    HOLD_STEADY("Hold steady — stabilizing focus", false),
    REDUCE_GLARE("Excessive glare — tilt package slightly", false),
    TOO_DARK("Too dark — turn on torch or increase light", false),
    READY("Good lighting & focus — Ready to Audit", true)
}

data class FrameQualityMetrics(
    val brightness: Float,
    val glarePercentage: Float,
    val sharpnessVariance: Float,
    val guidanceState: GuidanceState
)

object FrameQualityGate {

    fun evaluate(image: ImageProxy): FrameQualityMetrics {
        val plane = image.planes[0]
        val buffer = plane.buffer
        val rowStride = plane.rowStride
        val pixelStride = plane.pixelStride
        val width = image.width
        val height = image.height

        var totalLuminance = 0L
        var glareCount = 0
        var sampledPixels = 0
        var laplacianDiffSum = 0L

        buffer.rewind()
        val step = 8
        for (y in 0 until height - step step step) {
            for (x in 0 until width - step step step) {
                val index = y * rowStride + x * pixelStride
                if (index < buffer.limit()) {
                    val p = buffer.get(index).toInt() and 0xFF
                    totalLuminance += p
                    if (p >= 245) glareCount++
                    sampledPixels++

                    val nextXIndex = y * rowStride + (x + step) * pixelStride
                    val nextYIndex = (y + step) * rowStride + x * pixelStride
                    if (nextXIndex < buffer.limit() && nextYIndex < buffer.limit()) {
                        val px = buffer.get(nextXIndex).toInt() and 0xFF
                        val py = buffer.get(nextYIndex).toInt() and 0xFF
                        laplacianDiffSum += abs(p - px) + abs(p - py)
                    }
                }
            }
        }

        val avgBrightness = if (sampledPixels > 0) totalLuminance.toFloat() / sampledPixels else 128f
        val glarePercent = if (sampledPixels > 0) (glareCount.toFloat() / sampledPixels) * 100f else 0f
        val avgSharpness = if (sampledPixels > 0) laplacianDiffSum.toFloat() / sampledPixels else 0f

        val state = when {
            avgBrightness < 45f -> GuidanceState.TOO_DARK
            glarePercent > 18f -> GuidanceState.REDUCE_GLARE
            avgSharpness < 8f -> GuidanceState.HOLD_STEADY
            avgSharpness < 14f -> GuidanceState.MOVE_CLOSER
            else -> GuidanceState.READY
        }

        return FrameQualityMetrics(avgBrightness, glarePercent, avgSharpness, state)
    }
}
