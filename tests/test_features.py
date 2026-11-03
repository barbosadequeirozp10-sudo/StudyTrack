"""Testes do backend da versão final. Isolados do banco pessoal."""
from datetime import date, timedelta
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import database as db


class StudyTrackFinalTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "studytrack.db"
        self.patcher = patch.object(db, "DB_PATH", self.path)
        self.patcher.start()
        db.initialize_database()
        self.math = db.add_subject("Matemática")
        self.python = db.add_subject("Python")

    def tearDown(self):
        self.patcher.stop()
        self.folder.cleanup()

    def test_full_flow_and_overview(self):
        db.add_study_session(self.math, "2026-11-03", 45, "Porcentagens")
        db.add_study_session(self.math, "2026-11-03", 15)
        db.add_question_record(self.math, "2026-11-03", 10, 8)
        db.add_question_record(self.math, "2026-11-03", 5, 3)
        summary = db.overview()
        self.assertEqual(summary["minutes"], 60)
        self.assertEqual(summary["questions"], 15)
        self.assertEqual(summary["correct"], 11)
        self.assertEqual(len(db.full_history()), 4)
        self.assertEqual(db.subject_statistics()[0]["minutes"], 60)

    def test_edit_and_delete_session(self):
        record = db.add_study_session(self.python, "2026-11-03", 10)
        db.edit_study_session(record, self.math, "2026-11-01", 50, "editado")
        item = db.full_history()[0]
        self.assertEqual((item["minutes"], item["note"], item["subject_id"]), (50, "editado", self.math))
        db.delete_record("Estudo", record)
        self.assertEqual(db.overview()["minutes"], 0)
        with self.assertRaises(ValueError):
            db.delete_record("Estudo", record)

    def test_edit_and_delete_question_record(self):
        record = db.add_question_record(self.python, "2026-11-03", 10, 5)
        db.edit_question_record(record, self.math, "2026-11-01", 20, 18, "revisado")
        item = db.full_history()[0]
        self.assertEqual((item["total"], item["correct"], item["note"]), (20, 18, "revisado"))
        with self.assertRaises(ValueError):
            db.edit_question_record(record, self.math, "2026-11-01", 5, 10)
        db.delete_record("Questões", record)
        self.assertEqual(db.overview()["questions"], 0)

    def test_rename_and_guarded_delete(self):
        db.rename_subject(self.math, "Matemática aplicada")
        self.assertIn("Matemática aplicada", [x["name"] for x in db.list_subjects()])
        with self.assertRaises(ValueError):
            db.rename_subject(self.math, "Python")
        db.add_study_session(self.math, "2026-11-03", 5)
        with self.assertRaises(ValueError):
            db.delete_subject(self.math)
        db.delete_subject(self.python)
        self.assertEqual(len(db.list_subjects()), 1)

    def test_weekly_goals_and_progress(self):
        db.set_weekly_goal(self.math, 120)
        db.add_study_session(self.math, "2026-11-02", 45)
        db.add_study_session(self.math, "2026-11-08", 30)
        db.add_study_session(self.math, "2026-11-09", 100)
        progress = db.weekly_goal_progress("2026-11-03")
        self.assertEqual(progress[0]["minutes"], 75)
        self.assertEqual(progress[0]["target_minutes"], 120)
        db.set_weekly_goal(self.math, 100)
        self.assertEqual(db.weekly_goal_progress("2026-11-03")[0]["target_minutes"], 100)
        db.delete_weekly_goal(self.math)
        self.assertEqual(db.weekly_goal_progress("2026-11-03"), [])

    def test_task_lifecycle(self):
        task_id = db.add_task(self.python, "Revisar funções", "2026-11-05", "Alta")
        self.assertEqual(db.list_tasks()[0]["done"], 0)
        db.set_task_done(task_id, True)
        self.assertEqual(db.list_tasks(show_completed=False), [])
        self.assertEqual(db.list_tasks()[0]["done"], 1)
        db.set_task_done(task_id, False)
        db.delete_task(task_id)
        self.assertEqual(db.list_tasks(), [])

    def test_date_validation_and_invalid_values(self):
        for wrong in ("03/11/2026", "2026-02-30", "nao e data", None):
            with self.assertRaises(ValueError):
                db.add_study_session(self.math, wrong, 20)
        with self.assertRaises(ValueError):
            db.add_study_session(self.math, "2026-11-03", -20)
        with self.assertRaises(ValueError):
            db.add_question_record(self.math, "2026-11-03", 10, 11)
        with self.assertRaises(ValueError):
            db.add_study_session(99999, "2026-11-03", 20)
        with self.assertRaises(ValueError):
            db.add_task(self.math, " ")
        with self.assertRaises(ValueError):
            db.set_weekly_goal(self.math, 0)

    def test_filters_and_recent_history(self):
        db.add_study_session(self.math, "2026-10-31", 20)
        db.add_study_session(self.math, "2026-11-03", 40)
        db.add_question_record(self.python, "2026-11-03", 5, 4)
        self.assertEqual(db.overview("2026-11-01", "2026-11-03")["minutes"], 40)
        self.assertEqual(len(db.full_history("2026-11-03", "2026-11-03", self.math)), 1)
        self.assertEqual(len(db.recent_history(2)), 2)
        self.assertEqual(db.daily_study_minutes(subject_id=self.math)[1]["minutes"], 40)

    def test_snapshot_backup_is_readable_sqlite(self):
        db.add_study_session(self.math, "2026-11-03", 34)
        backup = db.database_backup_bytes()
        self.assertTrue(backup.startswith(b"SQLite format 3"))
        restored = Path(self.folder.name) / "restored.db"
        restored.write_bytes(backup)
        with sqlite3.connect(restored) as connection:
            self.assertEqual(connection.execute("SELECT SUM(minutes) FROM study_sessions").fetchone()[0], 34)

    def test_v1_schema_is_migrated_in_place(self):
        """Simula um banco anterior com tabelas antigas e uma sessão persistida."""
        self.path.unlink()
        with sqlite3.connect(self.path) as conn:
            conn.executescript("""
                CREATE TABLE subjects(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE COLLATE NOCASE);
                CREATE TABLE study_sessions(id INTEGER PRIMARY KEY, subject_id INTEGER, study_date TEXT,
                    minutes INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE question_records(id INTEGER PRIMARY KEY, subject_id INTEGER, study_date TEXT,
                    total INTEGER, correct INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
                INSERT INTO subjects VALUES (1, 'PORTUGUES');
                INSERT INTO study_sessions(id,subject_id,study_date,minutes) VALUES (1,1,'2026-11-03',45);
            """)
        db.initialize_database()
        db.initialize_database()
        self.assertEqual(db.overview()["minutes"], 45)
        db.add_study_session(1, "2026-11-03", 15, "Novo campo")
        self.assertEqual(db.overview()["minutes"], 60)
        self.assertEqual(db.full_history()[0]["note"], "Novo campo")


if __name__ == "__main__":
    unittest.main()
