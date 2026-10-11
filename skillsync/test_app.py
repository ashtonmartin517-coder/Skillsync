"""Smoke tests. Run with:  python -m unittest test_app.py"""
import os
import tempfile
import unittest

os.environ["SKILLSYNC_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import app as skillsync  # noqa: E402
import content  # noqa: E402


def signup(client, name, email, college="ABC College", course="BCA", year=1):
    return client.post("/api/register", json={
        "name": name, "email": email, "password": "password123",
        "college": college, "course": course, "year": year, "contact": "@" + name.lower()})


def assess(client, levels):
    answers = {s["id"]: levels.get(s["id"], 0) for s in content.SKILLS}
    return client.post("/api/assessment", json={"answers": answers})


class SkillSyncTests(unittest.TestCase):
    def setUp(self):
        skillsync.app.config["TESTING"] = True
        skillsync._attempts.clear()
        import sqlite3
        conn = sqlite3.connect(skillsync.DB_PATH)
        for table in ("connections", "tasks_done", "answers", "users"):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        self.a = skillsync.app.test_client()
        self.b = skillsync.app.test_client()

    def test_auth_and_validation(self):
        self.assertEqual(self.a.get("/api/me").status_code, 401)
        self.assertEqual(signup(self.a, "Weak", "weak@x.com").status_code, 201)
        self.assertEqual(signup(self.b, "Dup", "weak@x.com").status_code, 409)
        bad = self.b.post("/api/register", json={"name": "X", "email": "nope", "password": "1"})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.b.post("/api/login", json={"email": "weak@x.com", "password": "wrong"}).status_code, 401)
        self.assertEqual(self.b.post("/api/login", json={"email": "weak@x.com", "password": "password123"}).status_code, 200)

    def test_assessment_roadmap_and_xp(self):
        signup(self.a, "Newbie", "newbie@x.com")
        self.assertEqual(assess(self.a, {}).status_code, 200)
        me = self.a.get("/api/me").get_json()
        self.assertEqual(me["analysis"]["stage"], "Starter")
        first_week = [s["id"] for s in me["roadmap"][0]["skills"]]
        self.assertIn("terminal", first_week)
        # prerequisites must appear before dependants
        flat = [s["id"] for w in me["roadmap"] for s in w["skills"]]
        self.assertLess(flat.index("terminal"), flat.index("git"))
        self.assertEqual(me["xp"], 50)
        task = me["mission"]["id"]
        self.assertTrue(self.a.post(f"/api/tasks/{task}/toggle").get_json()["done"])
        me = self.a.get("/api/me").get_json()
        self.assertEqual(me["xp"], 70)
        self.assertEqual(me["streak"], 1)
        self.assertEqual(self.a.post("/api/tasks/nope:9/toggle").status_code, 404)

    def test_incomplete_assessment_rejected(self):
        signup(self.a, "Half", "half@x.com")
        r = self.a.post("/api/assessment", json={"answers": {"git": 2}})
        self.assertEqual(r.status_code, 400)

    def test_peer_matching_and_connection(self):
        signup(self.a, "Beginner", "beg@x.com")
        assess(self.a, {})
        signup(self.b, "Expert", "exp@x.com")
        assess(self.b, {s["id"]: 3 for s in content.SKILLS})
        peers = self.a.get("/api/peers").get_json()["items"]
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]["name"], "Expert")
        self.assertEqual(peers[0]["contact"], "")
        pid = peers[0]["id"]
        self.assertEqual(self.a.post(f"/api/connect/{pid}").get_json()["status"], "sent")
        beginner_id = self.b.get("/api/peers").get_json()["items"][0]["id"]
        self.assertEqual(self.b.post(f"/api/connect/{beginner_id}").get_json()["status"], "mutual")
        peers = self.a.get("/api/peers").get_json()["items"]
        self.assertEqual(peers[0]["contact"], "@expert")

    def test_leaderboard_glossary_pages(self):
        signup(self.a, "Lea", "lea@x.com")
        assess(self.a, {})
        board = self.a.get("/api/leaderboard").get_json()
        self.assertEqual(board["my_rank"], 1)
        self.assertTrue(self.a.get("/api/glossary?q=git").get_json()["items"])
        self.assertEqual(self.a.get("/dashboard").status_code, 200)
        self.assertEqual(self.b.get("/dashboard").status_code, 302)
        self.assertEqual(self.b.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
