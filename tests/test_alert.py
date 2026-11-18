import unittest
from datetime import datetime, timedelta, timezone
from warframe_alert import target, alert_payload, format_kst

class AlertTests(unittest.TestCase):
    def test_exact_target(self):
        f = {"isHard": True, "isStorm": False, "node": "Tuvul Commons (Zariman)", "missionType": "Void Cascade"}
        self.assertTrue(target(f))
        self.assertFalse(target({**f, "isHard": False}))
        self.assertFalse(target({**f, "node": "Everview Arc (Zariman)"}))
        self.assertFalse(target({**f, "isStorm": True}))
        self.assertFalse(target({**f, "missionType": "Void Flood"}))

    def test_kst_conversion(self):
        self.assertEqual(format_kst("2026-11-18T12:00:00Z"), "2026-11-18 21:00:00 KST")

    def test_expiry_discord_format(self):
        expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        p = alert_payload({"activation": "2026-11-18T12:00:00Z", "expiry": expiry})
        self.assertIn("등장 시간:", p["embeds"][0]["description"])
        self.assertIn("종료 시간:", p["embeds"][0]["description"])
        self.assertIn("<t:", p["embeds"][0]["description"])

if __name__ == "__main__":
    unittest.main()
