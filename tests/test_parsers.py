import unittest

from abqjobpilot.parsers import classify_final_verdict, parse_console_status


class TestParsers(unittest.TestCase):
    def test_contact_force_error_tolerance_is_not_fatal(self):
        result = classify_final_verdict(msg_text="CONTACT FORCE ERROR TOLERANCE = 0.005")
        self.assertNotEqual(result["status"], "FAILED_FATAL")
        self.assertEqual(parse_console_status("force error tolerance")["fatal_detected"], False)

    def test_success_pattern(self):
        result = classify_final_verdict(sta_text="THE ANALYSIS HAS COMPLETED SUCCESSFULLY")
        self.assertEqual(result["status"], "COMPLETED_OK")
        self.assertEqual(result["final_verdict"], "SUCCESS")

    def test_too_many_attempts_is_failure(self):
        result = classify_final_verdict(log_text="Too many attempts made for this increment")
        self.assertEqual(result["status"], "FAILED_FATAL")
        self.assertEqual(result["final_verdict"], "FAILED")


if __name__ == "__main__":
    unittest.main()
