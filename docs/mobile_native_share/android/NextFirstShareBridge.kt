package com.nextfirst.share

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File

/*
Purpose:
- Convert NextFirst share payload into Android native ACTION_SEND flow.

Input/Output:
- Input: SharePayload(title, body, optional url, optional imageRef).
- Output: chooser intent with proper MIME type and content URI grants.

Debugging:
- Ensure FileProvider is configured in AndroidManifest for local files.
- Verify granted URI permission for target apps.
*/

data class SharePayload(
    val title: String,
    val body: String,
    val url: String? = null,
    val imageRef: String? = null,
)

class NextFirstShareBridge(
    private val context: Context,
    private val fileProviderAuthority: String,
) {
    fun share(payload: SharePayload) {
        val text = buildString {
            append(payload.body)
            if (!payload.url.isNullOrBlank()) {
                if (isNotBlank()) append("\n\n")
                append(payload.url)
            }
        }.ifBlank { payload.title }

        val imageUri = resolveImageUri(payload.imageRef)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = if (imageUri != null) "image/*" else "text/plain"
            putExtra(Intent.EXTRA_SUBJECT, payload.title)
            putExtra(Intent.EXTRA_TEXT, text)
            if (imageUri != null) {
                putExtra(Intent.EXTRA_STREAM, imageUri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
        }

        val chooser = Intent.createChooser(intent, payload.title)
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(chooser)
    }

    private fun resolveImageUri(ref: String?): Uri? {
        val value = ref?.trim().orEmpty()
        if (value.isEmpty()) return null
        if (value.startsWith("content://")) return Uri.parse(value)
        if (value.startsWith("file://")) return Uri.parse(value)

        val localFile = File(value)
        if (localFile.exists()) {
            return FileProvider.getUriForFile(context, fileProviderAuthority, localFile)
        }

        if (value.startsWith("http://") || value.startsWith("https://")) {
            // Remote URLs cannot be put as stream directly; keep them in EXTRA_TEXT.
            return null
        }
        return null
    }
}
