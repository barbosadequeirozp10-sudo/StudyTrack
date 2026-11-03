"""Testes automatizados sem dependências externas."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database as db


class StudyTrackDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(db, "DB_PATH", Path(self.temp.name) / "test.db")
        self.patch_db.start()
        db.initialize_database()

    def tearDown(self):
        self.patch_db.stop()
        self.temp.cleanup()

    def test_subjects_are_saved_and_case_insensitive_unique(self):
        db.add_subject("Python")
        self.assertEqual(db.list_subjects()[0]["name"], "Python")
        with self.assertRaises(ValueError):
            db.add_subject("python")

    def test_statistics_do_not_duplicate_study_minutes(self):
        db.add_subject("Matemática")
        subject_id = db.list_subjects()[0]["id"]
        db.add_study_session(subject_id, "2026-11-03", 30)
        db.add_study_session(subject_id, "2026-11-03", 45)
        db.add_question_record(subject_id, "2026-11-03", 10, 8)
        db.add_question_record(subject_id, "2026-11-03", 5, 4)
        stats = db.subject_statistics()[0]
        self.assertEqual(stats["minutes"], 75)
        self.assertEqual(stats["sessions"], 2)
        self.assertEqual(stats["questions"], 15)
        self.assertEqual(stats["correct"], 12)
        self.assertEqual(db.overview()["questions"], 15)

    def test_invalid_question_records_are_rejected(self):
        db.add_subject("Português")
        subject_id = db.list_subjects()[0]["id"]
        with self.assertRaises(ValueError):
            db.add_question_record(subject_id, "2026-11-03", 5, 6)
        with self.assertRaises(ValueError):
            db.add_question_record(subject_id, "2026-11-03", 0, 0)

    def test_history_shows_events(self):
        db.add_subject("Python")
        subject_id = db.list_subjects()[0]["id"]
        db.add_study_session(subject_id, "2026-11-03", 25)
        db.add_question_record(subject_id, "2026-11-03", 10, 7)
        events = db.recent_history()
        self.assertEqual(len(events), 2)
        self.assertEqual({event["event_type"] for event in events}, {"Estudo", "Questões"})


if __name__ == "__main__":
    unittest.main()


class StudyTrackDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(db, "DB_PATH", Path(self.temp.name) / "test.db")
        self.patch_db.start()
        db.initialize_database()
        db.add_subject("Python")
        db.add_subject("Português")
        self.subjects = {s["name"]: s["id"] for s in db.list_subjects()}

    def tearDown(self):
        self.patch_db.stop()
        self.temp.cleanup()

    def test_daily_minutes_sum_and_filter(self):
        python_id = self.subjects["Python"]
        portuguese_id = self.subjects["Português"]
        db.add_study_session(python_id, "2026-11-01", 25)
        db.add_study_session(python_id, "2026-11-01", 20)
        db.add_study_session(python_id, "2026-11-02", 30)
        db.add_study_session(portuguese_id, "2026-11-01", 45)
        self.assertEqual(db.daily_study_minutes(), [
            {"study_date": "2026-11-01", "minutes": 90},
            {"study_date": "2026-11-02", "minutes": 30},
        ])
        self.assertEqual(db.daily_study_minutes(
            start_date="2026-11-01", end_date="2026-11-01", subject_id=python_id
        ), [{"study_date": "2026-11-01", "minutes": 45}])

    def test_history_date_and_subject_filters(self):
        python_id = self.subjects["Python"]
        portuguese_id = self.subjects["Português"]
        db.add_study_session(python_id, "2026-11-01", 25)
        db.add_question_record(python_id, "2026-11-02", 10, 8)
        db.add_study_session(portuguese_id, "2026-11-02", 30)
        events = db.full_history("2026-11-02", "2026-11-02", python_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "Questões")
        self.assertEqual(events[0]["details"], "8/10")
