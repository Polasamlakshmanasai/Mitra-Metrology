package com.mitra.metrology

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.android.material.slider.Slider
import com.mitra.metrology.camera.CameraManager
import com.mitra.metrology.camera.GuidanceState
import com.mitra.metrology.classifier.FoodLabelClassifier
import com.mitra.metrology.rules.FSSAIRuleEngine
import com.mitra.metrology.ui.ComplianceReportBottomSheet

class MainActivity : AppCompatActivity() {

    private lateinit var previewView: PreviewView
    private lateinit var tvGuidancePill: TextView
    private lateinit var btnCaptureAudit: TextView
    private lateinit var sliderThreshold: Slider
    private lateinit var tvConfidenceValue: TextView

    private var cameraManager: CameraManager? = null
    private val ruleEngine = FSSAIRuleEngine()
    private lateinit var classifier: FoodLabelClassifier

    companion object {
        private const val CAMERA_PERMISSION_REQUEST = 101
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        previewView = findViewById(R.id.cameraPreview)
        tvGuidancePill = findViewById(R.id.tvGuidancePill)
        btnCaptureAudit = findViewById(R.id.btnCaptureAudit)
        sliderThreshold = findViewById(R.id.sliderThreshold)
        tvConfidenceValue = findViewById(R.id.tvConfidenceValue)

        classifier = FoodLabelClassifier.getInstance(this)

        sliderThreshold.value = classifier.getConfidenceThreshold()
        tvConfidenceValue.text = "${(sliderThreshold.value * 100).toInt()}%"

        sliderThreshold.addOnChangeListener { _, value, _ ->
            classifier.setConfidenceThreshold(value)
            tvConfidenceValue.text = "${(value * 100).toInt()}%"
        }

        btnCaptureAudit.setOnClickListener {
            runSampleAudit()
        }

        findViewById<Button>(R.id.btnPresetGhee).setOnClickListener {
            loadGheePreset()
        }
        findViewById<Button>(R.id.btnPresetBiscuits).setOnClickListener {
            loadBiscuitPreset()
        }

        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.CAMERA),
                CAMERA_PERMISSION_REQUEST
            )
        }
    }

    private fun startCamera() {
        cameraManager = CameraManager(
            context = this,
            lifecycleOwner = this,
            previewView = previewView
        ) { metrics ->
            runOnUiThread {
                tvGuidancePill.text = metrics.guidanceState.message
                val bgColor = when (metrics.guidanceState) {
                    GuidanceState.READY -> 0xFF15803D.toInt()
                    GuidanceState.REDUCE_GLARE -> 0xFFB45309.toInt()
                    GuidanceState.HOLD_STEADY -> 0xFF3B82F6.toInt()
                    else -> 0xFFB91C1C.toInt()
                }
                tvGuidancePill.setBackgroundColor(bgColor)
            }
        }
        cameraManager?.startCamera()
    }

    private fun runSampleAudit() {
        val sampleLabel = "AMUL PURE GHEE - 100% PURE MILK FAT\nINGREDIENTS: MILK FAT (100%). NO PRESERVATIVES OR COLOUR ADDED.\nNUTRITIONAL INFORMATION PER 100g: ENERGY 900 kcal, TOTAL FAT 99.7 g, TRANS FAT 2.0 g\nCONTAINS MILK. FORTIFIED WITH VITAMIN A AND D (+F LOGO)\nNET QUANTITY: 1 L (905 g), MRP Rs. 610\nBATCH NO: AGH2408, MFD: 15/08/2024\nFSSAI LIC. NO. 10012021000071\nAGMARK SPECIAL GRADE REGD. CA NO. 12345/A"
        val report = ruleEngine.evaluate(sampleLabel, isGheeOrDairy = true)
        val sheet = ComplianceReportBottomSheet(report)
        sheet.show(supportFragmentManager, "ComplianceSheet")
    }

    private fun loadGheePreset() {
        Toast.makeText(this, "Auditing Amul Pure Ghee Preset...", Toast.LENGTH_SHORT).show()
        runSampleAudit()
    }

    private fun loadBiscuitPreset() {
        val sampleLabel = "BRITANNIA CHOCO CRUNCH COOKIES - GREEN DOT VEGETARIAN\nINGREDIENTS: REFINED WHEAT FLOUR (45%), SUGAR (24%), PALM OIL, CHOCOLATE CHIPS (10%) [EMULSIFIER (INS 322)], RAISING AGENTS [INS 500(ii)]\nCONTAINS WHEAT, MILK, SOY. MAY CONTAIN TRACES OF NUTS.\nNUTRITIONAL INFORMATION PER 100g: ENERGY 495 kcal, PROTEIN 6.5g, SUGARS 28.5g\nNET WEIGHT: 120 g, MRP Rs. 40.00, BATCH: B240901, MFD: 01/09/2024\nFSSAI LIC. NO. 10015043001129"
        val report = ruleEngine.evaluate(sampleLabel, isGheeOrDairy = false)
        val sheet = ComplianceReportBottomSheet(report)
        sheet.show(supportFragmentManager, "ComplianceSheet")
    }

    private fun allPermissionsGranted() = ContextCompat.checkSelfPermission(
        this, Manifest.permission.CAMERA
    ) == PackageManager.PERMISSION_GRANTED

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == CAMERA_PERMISSION_REQUEST && allPermissionsGranted()) {
            startCamera()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraManager?.shutdown()
    }
}
