import unittest
import os

from app import app, init_db


class LegacyBankAppTests(unittest.TestCase):
    def setUp(self):
        if os.path.exists("leads.db"):
            os.remove("leads.db")
        self.client = app.test_client()
        init_db()

    def test_root_and_service_worker_routes_exist(self):
        response_root = self.client.get("/", follow_redirects=True)
        self.assertEqual(response_root.status_code, 200)
        self.assertIn("text/html", response_root.content_type)
        self.assertIn("DCA Systems", response_root.get_data(as_text=True))

        response_sw = self.client.get("/sw.js")
        self.assertEqual(response_sw.status_code, 200)
        self.assertIn("DCA Systems API service worker stub", response_sw.get_data(as_text=True))

    def test_interface_route_serves_html(self):
        response = self.client.get("/interface")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        self.assertIn("DCA Systems", response.get_data(as_text=True))

    def test_list_leads_returns_empty_list_from_db(self):
        response = self.client.get("/api/leads")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["leads"], [])
        self.assertEqual(data["total_cadastrados"], 0)

    def test_migrate_sample_returns_json_payload_with_decimal_saldo(self):
        legacy_text = "001JOAO SILVA                   joao.silva@oraclebank.com       00000000012345A"
        response = self.client.post(
            "/api/migrar-amostra",
            json={"dados_legados": legacy_text},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["saldo"], "123.45")
        self.assertEqual(data["status"], "ativo")


if __name__ == "__main__":
    unittest.main()
