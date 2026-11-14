"""Pruebas locales de la autenticación sin MySQL."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from werkzeug.security import generate_password_hash

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))
from auth import valid_login, configured, check_csrf, csrf_token, blocked, failed, clear_attempts
from flask import Flask


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.values = patch.dict(os.environ, {
            "AUTH_USERNAME": "neutrinitoo",
            "AUTH_PASSWORD_HASH": generate_password_hash("very-long-password-12345"),
            "SESSION_SECRET": "x" * 64,
        })
        self.values.start()

    def tearDown(self):
        self.values.stop()

    def test_user(self):
        self.assertTrue(configured())
        self.assertTrue(valid_login("neutrinitoo", "very-long-password-12345"))
        self.assertFalse(valid_login("Neutrinitoo", "very-long-password-12345"))
        self.assertFalse(valid_login("neutrinitoo", "incorrect"))

    def test_missing_configuration_is_denied(self):
        with patch.dict(os.environ, {"AUTH_PASSWORD_HASH": ""}):
            self.assertFalse(configured())
            self.assertFalse(valid_login("neutrinitoo", "very-long-password-12345"))

    def test_csrf(self):
        app=Flask(__name__)
        app.secret_key="test-only"
        with app.test_request_context("/"):
            token=csrf_token()
            self.assertTrue(check_csrf(token))
            self.assertFalse(check_csrf("bad"))

    def test_throttle(self):
        key="test-throttle-unique"
        clear_attempts(key)
        for _ in range(8):
            failed(key)
        self.assertTrue(blocked(key))
        clear_attempts(key)
        self.assertFalse(blocked(key))


if __name__=="__main__":
    unittest.main()
