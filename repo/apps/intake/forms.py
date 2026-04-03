from __future__ import annotations

from django import forms

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class ResumeUploadForm(forms.Form):
    file = forms.FileField(
        error_messages={"required": "Please select a resume file to upload."}
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError(
                f"Unsupported file type '{uploaded.content_type}'. "
                "Please upload a PDF, DOC, or DOCX file."
            )
        if uploaded.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError(
                "File is too large. Maximum upload size is 10 MB."
            )
        return uploaded
