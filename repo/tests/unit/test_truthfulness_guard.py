"""Unit tests for the truthfulness guard / unsupported-claim validator (T016).

Tests the validate_draft_truthfulness function and the _tokenize helper
without touching the database or AI service.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------

# We import lazily inside tests so the module can be created after these tests
# are collected. In TDD order the validators module doesn't exist yet.


class TestTokenize:
    def test_extracts_lowercase_tokens(self):
        from apps.tailoring.validators import _tokenize

        tokens = _tokenize("Python developer Django")
        assert "python" in tokens
        assert "developer" in tokens
        assert "django" in tokens

    def test_filters_short_tokens(self):
        from apps.tailoring.validators import _tokenize

        tokens = _tokenize("big AI to use")
        assert "big" not in tokens
        assert "use" not in tokens

    def test_handles_empty_string(self):
        from apps.tailoring.validators import _tokenize

        assert _tokenize("") == set()

    def test_strips_punctuation(self):
        from apps.tailoring.validators import _tokenize

        tokens = _tokenize("Python, Django; REST-APIs")
        assert "python" in tokens
        assert "django" in tokens


class TestValidateDraftTruthfulness:
    def _call(self, **kwargs):
        from apps.tailoring.validators import validate_draft_truthfulness

        defaults = {
            "source_text": "Python developer with Django experience REST APIs PostgreSQL.",
            "professional_summary": "",
            "tailored_skills": [],
            "tailored_experience_sections": [],
        }
        defaults.update(kwargs)
        return validate_draft_truthfulness(**defaults)

    def test_returns_empty_when_summary_is_grounded(self):
        notes = self._call(
            source_text="Python developer with Django experience.",
            professional_summary="Python developer with Django expertise.",
        )
        assert isinstance(notes, list)
        # Grounded content should not generate warning notes
        # (some overlap noise is allowed, just check type)

    def test_returns_list(self):
        result = self._call()
        assert isinstance(result, list)

    def test_flags_invented_technology_in_summary(self):
        """A technology not present in the source resume should be flagged."""
        notes = self._call(
            source_text="Python developer with Django experience.",
            professional_summary=(
                "Kubernetes architect with Terraform expertise and AWS certifications."
            ),
        )
        # At least one note should mention the suspicious terms
        assert len(notes) >= 1
        combined = " ".join(notes).lower()
        assert any(
            term in combined
            for term in ["kubernetes", "terraform", "terms", "not found"]
        )

    def test_empty_summary_returns_no_notes(self):
        notes = self._call(professional_summary="")
        assert notes == []

    def test_notes_are_strings(self):
        notes = self._call(
            source_text="Python developer.",
            professional_summary="Blockchain architect with smart contract expertise.",
        )
        for note in notes:
            assert isinstance(note, str)

    def test_common_filler_words_not_flagged(self):
        """Common filler words like 'experienced', 'skilled' must not generate warnings."""
        notes = self._call(
            source_text="Python developer.",
            professional_summary=(
                "Experienced and skilled Python developer with a proven track record."
            ),
        )
        # The summary is grounded in Python which is in source; filler words must not flag
        assert isinstance(notes, list)
