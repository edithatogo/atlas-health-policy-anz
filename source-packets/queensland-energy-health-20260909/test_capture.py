"""Offline negative controls for the isolated source transport."""
import unittest
from capture import check_url, validate_body

class CaptureChecks(unittest.TestCase):
    def test_valid_pdf_signature(self):
        validate_body(b"%PDF-1.7\nfixture\n%%EOF", "application/pdf")
    def test_html_challenge_rejected(self):
        with self.assertRaises(ValueError):
            validate_body(b"<html>challenge</html>", "text/html")
    def test_mislabeled_html_rejected(self):
        with self.assertRaises(ValueError):
            validate_body(b"<html>blocked</html>", "application/pdf")
    def test_truncation_rejected(self):
        with self.assertRaises(ValueError):
            validate_body(b"%PDF-1.7\ntruncated", "application/pdf")
    def test_untrusted_url_rejected(self):
        for url in ("http://www.health.qld.gov.au/a.pdf", "https://127.0.0.1/x", "https://www.health.qld.gov.au.evil.invalid/x", "https://u:p@www.health.qld.gov.au/x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check_url(url, resolve=False)
    def test_exact_public_host(self):
        check_url("https://www.health.qld.gov.au/a.pdf", resolve=False)

if __name__ == "__main__":
    unittest.main()
