package com.mitra.metrology.nlp

import java.util.regex.Pattern

data class ParsedIngredient(
    val rawText: String,
    val name: String,
    val quidPercentage: Float? = null,
    val insCodes: List<String> = emptyList(),
    val isAdditive: Boolean = false
)

object IngredientParser {
    private val INS_REGEX = Pattern.compile("(?i)\\b(?:INS|E)\\s*[-:]?\\s*([0-9]{3,4}(?:\\([a-z0-9]+\\)|[a-z])?)\\b")
    private val QUID_REGEX = Pattern.compile("(\\d+(?:\\.\\d+)?)\\s*%")

    fun parse(declarationText: String): List<ParsedIngredient> {
        val cleaned = declarationText.replace(Regex("(?i)^(?:ingredients?|contains)\\s*[:\\-]\\s*"), "").trim()
        val items = splitSafely(cleaned)

        return items.map { item ->
            val quid = extractQUID(item)
            val ins = extractINSCodes(item)
            ParsedIngredient(
                rawText = item,
                name = item.replace(Regex("\\([^)]*\\)"), "").trim(),
                quidPercentage = quid,
                insCodes = ins,
                isAdditive = ins.isNotEmpty()
            )
        }
    }

    private fun extractQUID(text: String): Float? {
        val matcher = QUID_REGEX.matcher(text)
        return if (matcher.find()) matcher.group(1)?.toFloatOrNull() else null
    }

    private fun extractINSCodes(text: String): List<String> {
        val list = mutableListOf<String>()
        val matcher = INS_REGEX.matcher(text)
        while (matcher.find()) {
            matcher.group(1)?.let { list.add("INS $it") }
        }
        return list
    }

    private fun splitSafely(text: String): List<String> {
        val result = mutableListOf<String>()
        var depth = 0
        val current = StringBuilder()

        for (ch in text.toCharArray()) {
            when (ch) {
                '(', '[', '{' -> { depth++; current.append(ch) }
                ')', ']', '}' -> { if (depth > 0) depth--; current.append(ch) }
                ',', ';' -> {
                    if (depth == 0) {
                        val s = current.toString().trim()
                        if (s.isNotEmpty()) result.add(s)
                        current.clear()
                    } else current.append(ch)
                }
                else -> current.append(ch)
            }
        }
        val last = current.toString().trim()
        if (last.isNotEmpty()) result.add(last)
        return result
    }
}
