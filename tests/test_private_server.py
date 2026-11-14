"""Pruebas del servicio privado sin MySQL ni credenciales reales."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from private_server import app


class PrivateServerTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "AUTH_USERNAME": "neutrinitoo",
            "AUTH_PASSWORD_HASH": generate_password_hash("a very long password 987"),
            "SESSION_SECRET": "x" * 48,
        })
        self.env.start()
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = app.test_client()

    def tearDown(self):
        self.env.stop()

    def test_redirect_and_block_private_json(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertEqual(self.client.get("/data/live.json").status_code, 401)
        self.assertEqual(self.client.get("/app.js").status_code, 302)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_login_and_logout(self):
        self.client.get("/login")
        with self.client.session_transaction() as session:
            token = session["csrf_token"]
        response = self.client.post("/login", data={
            "username": "neutrinitoo", "password": "a very long password 987",
            "csrf_token": token,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/data/live.json").status_code, 200)
        response = self.client.get("/api/session")
        self.assertEqual(response.json["username"], "neutrinitoo")
        token = response.json["csrf_token"]
        self.assertEqual(self.client.post("/logout", data={"csrf_token": token}).status_code, 302)
        self.assertEqual(self.client.get("/data/live.json").status_code, 401)

    def test_missing_password_hash_is_fail_closed(self):
        with patch.dict(os.environ, {"AUTH_PASSWORD_HASH": ""}):
            self.assertEqual(self.client.get("/").status_code, 503)
            self.assertEqual(self.client.get("/login").status_code, 503)


if __name__ == "__main__":
    unittest.main()
