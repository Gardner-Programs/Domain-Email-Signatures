"""Unit tests for scripts/email_templates.py — set_html_template()."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.email_templates import set_html_template, CONFIGS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build(**kwargs):
    """Call set_html_template with sane defaults, overriding via kwargs."""
    defaults = dict(
        template="default",
        fullname="Jane Smith",
        title="Account Manager",
        location="HQ - Fort Wayne, IN",
        email="jane.smith@company.com",
        ext="1234",
        cell="",
        direct="",
        ltl=False,
        about="",
    )
    defaults.update(kwargs)
    return set_html_template(**defaults)


# ---------------------------------------------------------------------------
# Return type & basic structure
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_string(self):
        assert isinstance(build(), str)

    def test_nonempty(self):
        assert len(build()) > 0

    def test_is_html_div(self):
        result = build()
        assert result.startswith("<div") or "<div" in result

    def test_no_raw_newlines(self):
        """Minification must strip newlines."""
        result = build()
        assert "\n" not in result

    def test_no_raw_tabs(self):
        result = build()
        assert "\t" not in result


# ---------------------------------------------------------------------------
# User data appears in output
# ---------------------------------------------------------------------------

class TestUserDataInOutput:
    def test_fullname_present(self):
        result = build(fullname="Alice Tester")
        assert "Alice Tester" in result

    def test_title_present(self):
        result = build(title="Senior Engineer")
        assert "Senior Engineer" in result

    def test_location_present(self):
        result = build(location="Branch A - Chicago, IL")
        assert "Branch A - Chicago, IL" in result

    def test_email_present(self):
        result = build(email="alice@company.com")
        assert "alice@company.com" in result

    def test_ext_appended_to_phone(self):
        result = build(ext="9999")
        assert "9999" in result

    def test_cell_shown_when_provided(self):
        result = build(cell="260-555-0123")
        assert "260-555-0123" in result

    def test_cell_absent_when_not_provided(self):
        result = build(cell="")
        assert "Cell Phone" not in result

    def test_direct_shown_when_provided(self):
        result = build(direct="260-555-0199")
        assert "260-555-0199" in result

    def test_about_link_shown_when_provided(self):
        result = build(about="https://company.com/about/jane")
        assert "About me" in result
        assert "https://company.com/about/jane" in result

    def test_about_absent_when_not_provided(self):
        result = build(about="")
        assert "About me" not in result


# ---------------------------------------------------------------------------
# HTML escaping (XSS prevention)
# ---------------------------------------------------------------------------

class TestHtmlEscaping:
    def test_fullname_escaped(self):
        result = build(fullname="<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_title_escaped(self):
        # html.escape turns < into &lt;, so <img> cannot be injected as a runnable tag
        result = build(title='"><img src=x onerror=alert(1)>')
        assert '<img src=x' not in result       # literal tag must be absent
        assert '&lt;img' in result              # escaped form must be present

    def test_ampersand_in_name_escaped(self):
        result = build(fullname="Smith & Jones")
        assert "Smith & Jones" not in result
        assert "Smith &amp; Jones" in result


# ---------------------------------------------------------------------------
# Template routing
# ---------------------------------------------------------------------------

class TestTemplateRouting:
    def test_unknown_template_falls_back_to_default(self):
        """An unrecognised template key must not raise — falls back to default."""
        result = build(template="nonexistent_template_xyz")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_known_templates_produce_output(self):
        for key in CONFIGS:
            result = build(template=key)
            assert isinstance(result, str), f"Template '{key}' returned non-string"
            assert len(result) > 0, f"Template '{key}' returned empty string"

    def test_corp_billing_uses_billing_phone(self):
        result = build(template="corp_billing")
        assert "Carrier Settlements" in result

    def test_corp_transportation_uses_transport_name(self):
        result = build(template="corp_transportation")
        assert "Transportation" in result

    def test_regional_template_has_no_reply_all(self):
        """regional_template sets show_reply_all=False."""
        result = build(template="regional_template")
        assert "REPLY ALL" not in result

    def test_default_template_omits_reply_all(self):
        """default CONFIGS entry explicitly sets show_reply_all=False."""
        result = build(template="default")
        assert "REPLY ALL" not in result

    def test_template_without_show_reply_all_shows_it(self):
        """Templates that don't set show_reply_all inherit True (the fallback)."""
        # corp_billing has no show_reply_all key — falls back to True
        result = build(template="corp_billing")
        assert "REPLY ALL" in result


# ---------------------------------------------------------------------------
# LTL legal disclaimer
# ---------------------------------------------------------------------------

class TestLtlDisclaimer:
    def test_ltl_included_when_flag_true(self):
        result = build(ltl=True)
        assert "LTL" in result

    def test_ltl_excluded_when_flag_false_and_no_force(self):
        result = build(template="default", ltl=False)
        assert "$0.50 per pound" not in result

    def test_ltl_forced_by_office_template(self):
        """office_template sets force_ltl=True."""
        result = build(template="office_template", ltl=False)
        assert "LTL" in result


# ---------------------------------------------------------------------------
# Extension append logic
# ---------------------------------------------------------------------------

class TestExtAppend:
    def test_ext_not_appended_when_append_ext_false(self):
        """branch_c sets append_ext=False — ext should not appear in phone line."""
        result = build(template="branch_c", ext="8888")
        # The config overrides the phone number entirely; ext must not be appended
        assert "ext. 8888" not in result

    def test_ext_not_double_appended_when_phone_already_has_ext(self):
        """If phone_num already contains 'ext.', do not append a second ext."""
        # corp_claims phone_num is "555-000-0001 ext. 1701"
        # passing ext="1701" must NOT produce "ext. 1701 ext. 1701"
        result = build(template="corp_claims", ext="1701")
        assert "ext. 1701 ext." not in result
