"""Regras de negócio e persistência SQLite do StudyTrack.

Compatível com os bancos das versões 1.0 e 2.0. Nenhuma dependência externa.
"""
from __future__ import annotations

from contextlib import contextmanager, closing
from datetime import date, timedelta
from pathlib import Path
import sqlite3
import tempfile

DB_PATH = Path(__file__).resolve().parent / "studytrack.db"


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    """Cria tabelas sem apagar registros anteriores e migra campos novos."""
    with connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                study_date TEXT NOT NULL,
                minutes INTEGER NOT NULL CHECK (minutes > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            );
            CREATE TABLE IF NOT EXISTS question_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                study_date TEXT NOT NULL,
                total INTEGER NOT NULL CHECK (total > 0),
                correct INTEGER NOT NULL CHECK (correct >= 0 AND correct <= total),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            );
            CREATE TABLE IF NOT EXISTS weekly_goals (
                subject_id INTEGER PRIMARY KEY,
                target_minutes INTEGER NOT NULL CHECK (target_minutes > 0),
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'Média',
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0,1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            );
            CREATE INDEX IF NOT EXISTS idx_study_subject_date
                ON study_sessions(subject_id, study_date);
            CREATE INDEX IF NOT EXISTS idx_questions_subject_date
                ON question_records(subject_id, study_date);
            CREATE INDEX IF NOT EXISTS idx_tasks_subject ON tasks(subject_id, done);
        """)
        for table in ("study_sessions", "question_records"):
            fields = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
            if "note" not in fields:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN note TEXT NOT NULL DEFAULT ''")


def _day(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError("Data inválida: use AAAA-MM-DD.") from exc


def _positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} deve ser um inteiro positivo.")
    return value


def _text(value, label, max_length=160):
    if not isinstance(value, str):
        raise ValueError(f"{label} deve ser um texto.")
    value = " ".join(value.split())
    if not value or len(value) > max_length:
        raise ValueError(f"{label} deve ter de 1 a {max_length} caracteres.")
    return value


def _note(value):
    if not isinstance(value, str) or len(value) > 1000:
        raise ValueError("A observação deve conter até 1.000 caracteres.")
    return value.strip()


def _subject_exists(conn, subject_id):
    _positive_int(subject_id, "ID da matéria")
    if conn.execute("SELECT 1 FROM subjects WHERE id = ?", (subject_id,)).fetchone() is None:
        raise ValueError("Matéria não encontrada.")


def add_subject(name):
    name = _text(name, "Nome da matéria", 80)
    try:
        with connection() as conn:
            cur = conn.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
            return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError("Essa matéria já está cadastrada.") from exc


def rename_subject(subject_id, name):
    name = _text(name, "Nome da matéria", 80)
    try:
        with connection() as conn:
            _subject_exists(conn, subject_id)
            conn.execute("UPDATE subjects SET name = ? WHERE id = ?", (name, subject_id))
    except sqlite3.IntegrityError as exc:
        raise ValueError("Já existe outra matéria com esse nome.") from exc


def delete_subject(subject_id):
    """Só apaga matérias sem histórico, tarefas ou metas."""
    with connection() as conn:
        _subject_exists(conn, subject_id)
        for table in ("study_sessions", "question_records", "weekly_goals", "tasks"):
            if conn.execute(f"SELECT 1 FROM {table} WHERE subject_id = ? LIMIT 1", (subject_id,)).fetchone():
                raise ValueError("Esta matéria tem registros ou metas. Remova-os antes de excluí-la.")
        conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))


def list_subjects():
    with connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT id, name FROM subjects ORDER BY name COLLATE NOCASE").fetchall()]


def add_study_session(subject_id, study_date, minutes, note=""):
    _positive_int(minutes, "Minutos")
    study_date = _day(study_date)
    note = _note(note)
    with connection() as conn:
        _subject_exists(conn, subject_id)
        cur = conn.execute(
            "INSERT INTO study_sessions(subject_id,study_date,minutes,note) VALUES (?,?,?,?)",
            (subject_id, study_date, minutes, note))
        return cur.lastrowid


def add_question_record(subject_id, study_date, total, correct, note=""):
    _positive_int(total, "Quantidade de questões")
    if isinstance(correct, bool) or not isinstance(correct, int) or correct < 0 or correct > total:
        raise ValueError("Acertos devem estar entre zero e o total de questões.")
    study_date = _day(study_date)
    note = _note(note)
    with connection() as conn:
        _subject_exists(conn, subject_id)
        cur = conn.execute(
            "INSERT INTO question_records(subject_id,study_date,total,correct,note) VALUES (?,?,?,?,?)",
            (subject_id, study_date, total, correct, note))
        return cur.lastrowid


def edit_study_session(record_id, subject_id, study_date, minutes, note=""):
    _positive_int(record_id, "ID")
    _positive_int(minutes, "Minutos")
    study_date = _day(study_date)
    note = _note(note)
    with connection() as conn:
        _subject_exists(conn, subject_id)
        cur = conn.execute(
            "UPDATE study_sessions SET subject_id=?, study_date=?, minutes=?, note=? WHERE id=?",
            (subject_id, study_date, minutes, note, record_id))
        if not cur.rowcount:
            raise ValueError("Registro de estudo não encontrado.")


def edit_question_record(record_id, subject_id, study_date, total, correct, note=""):
    _positive_int(record_id, "ID")
    _positive_int(total, "Quantidade de questões")
    if isinstance(correct, bool) or not isinstance(correct, int) or not 0 <= correct <= total:
        raise ValueError("Acertos devem estar entre zero e o total de questões.")
    study_date = _day(study_date)
    note = _note(note)
    with connection() as conn:
        _subject_exists(conn, subject_id)
        cur = conn.execute(
            "UPDATE question_records SET subject_id=?, study_date=?, total=?, correct=?, note=? WHERE id=?",
            (subject_id, study_date, total, correct, note, record_id))
        if not cur.rowcount:
            raise ValueError("Registro de questões não encontrado.")


def delete_record(record_type, record_id):
    table = {"Estudo": "study_sessions", "Questões": "question_records"}.get(record_type)
    if table is None:
        raise ValueError("Tipo de registro inválido.")
    _positive_int(record_id, "ID")
    with connection() as conn:
        cur = conn.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
        if not cur.rowcount:
            raise ValueError("Registro não encontrado.")


def _filters(start_date=None, end_date=None, subject_id=None, prefix=""):
    where = []
    params = []
    column = f"{prefix}study_date"
    if start_date:
        where.append(f"{column} >= ?")
        params.append(_day(start_date))
    if end_date:
        where.append(f"{column} <= ?")
        params.append(_day(end_date))
    if subject_id is not None:
        where.append(f"{prefix}subject_id = ?")
        params.append(_positive_int(subject_id, "ID da matéria"))
    return (" WHERE " + " AND ".join(where)) if where else "", params


def subject_statistics(start_date=None, end_date=None):
    """Subconsultas independentes impedem multiplicar totais em joins."""
    st_where, st_args = _filters(start_date, end_date)
    q_where, q_args = _filters(start_date, end_date)
    query = f"""
        SELECT s.id, s.name, COALESCE(st.minutes,0) AS minutes,
               COALESCE(st.sessions,0) AS sessions,
               COALESCE(q.total,0) AS questions, COALESCE(q.correct,0) AS correct
        FROM subjects s
        LEFT JOIN (
          SELECT subject_id, SUM(minutes) minutes, COUNT(*) sessions
          FROM study_sessions {st_where} GROUP BY subject_id
        ) st ON st.subject_id = s.id
        LEFT JOIN (
          SELECT subject_id, SUM(total) total, SUM(correct) correct
          FROM question_records {q_where} GROUP BY subject_id
        ) q ON q.subject_id = s.id
        ORDER BY s.name COLLATE NOCASE"""
    with connection() as conn:
        return [dict(row) for row in conn.execute(query, st_args + q_args).fetchall()]


def overview(start_date=None, end_date=None):
    rows = subject_statistics(start_date, end_date)
    return {
        "subjects": len(rows),
        "minutes": sum(row["minutes"] for row in rows),
        "sessions": sum(row["sessions"] for row in rows),
        "questions": sum(row["questions"] for row in rows),
        "correct": sum(row["correct"] for row in rows),
    }


def daily_study_minutes(start_date=None, end_date=None, subject_id=None):
    clause, params = _filters(start_date, end_date, subject_id)
    with connection() as conn:
        rows = conn.execute(
            f"SELECT study_date, SUM(minutes) minutes FROM study_sessions {clause} "
            "GROUP BY study_date ORDER BY study_date", params).fetchall()
    return [dict(row) for row in rows]


def full_history(start_date=None, end_date=None, subject_id=None):
    clause, params = _filters(start_date, end_date, subject_id)
    with connection() as conn:
        rows = conn.execute(f"""
            SELECT id, subject_id, study_date, subject, event_type, details,
                   minutes, total, correct, note FROM (
              SELECT ss.id, ss.subject_id, ss.study_date, s.name subject, 'Estudo' event_type,
                     CAST(ss.minutes AS TEXT) || ' min' details, ss.minutes minutes,
                     NULL total, NULL correct, ss.note note, ss.created_at created_at
              FROM study_sessions ss JOIN subjects s ON s.id = ss.subject_id
              UNION ALL
              SELECT qr.id, qr.subject_id, qr.study_date, s.name, 'Questões',
                     CAST(qr.correct AS TEXT) || '/' || CAST(qr.total AS TEXT),
                     NULL, qr.total, qr.correct, qr.note, qr.created_at
              FROM question_records qr JOIN subjects s ON s.id = qr.subject_id
            ) {clause}
            ORDER BY study_date DESC, created_at DESC, event_type DESC, id DESC
        """, params).fetchall()
    return [dict(row) for row in rows]


def recent_history(limit=15):
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("Limite inválido.")
    return [{k: r[k] for k in ("study_date", "subject", "event_type", "details")}
            for r in full_history()[:limit]]


def set_weekly_goal(subject_id, target_minutes):
    _positive_int(target_minutes, "Meta semanal em minutos")
    with connection() as conn:
        _subject_exists(conn, subject_id)
        conn.execute("INSERT INTO weekly_goals(subject_id,target_minutes) VALUES (?,?) "
                     "ON CONFLICT(subject_id) DO UPDATE SET target_minutes=excluded.target_minutes",
                     (subject_id, target_minutes))


def delete_weekly_goal(subject_id):
    with connection() as conn:
        conn.execute("DELETE FROM weekly_goals WHERE subject_id=?", (subject_id,))


def weekly_goal_progress(reference_day=None):
    today = date.fromisoformat(_day(reference_day)) if reference_day else date.today()
    monday = (today - timedelta(days=today.weekday())).isoformat()
    sunday = (today + timedelta(days=6-today.weekday())).isoformat()
    with connection() as conn:
        rows = conn.execute("""
            SELECT g.subject_id, s.name subject, g.target_minutes,
                   COALESCE(SUM(ss.minutes),0) minutes
            FROM weekly_goals g JOIN subjects s ON s.id=g.subject_id
            LEFT JOIN study_sessions ss ON ss.subject_id=g.subject_id
              AND ss.study_date BETWEEN ? AND ?
            GROUP BY g.subject_id ORDER BY s.name COLLATE NOCASE
        """, (monday, sunday)).fetchall()
    return [dict(r) for r in rows]


def add_task(subject_id, title, due_date=None, priority="Média"):
    title = _text(title, "Título da tarefa", 200)
    if priority not in ("Baixa", "Média", "Alta"):
        raise ValueError("Prioridade inválida.")
    due_date = _day(due_date) if due_date else None
    with connection() as conn:
        _subject_exists(conn, subject_id)
        return conn.execute("INSERT INTO tasks(subject_id,title,due_date,priority) VALUES (?,?,?,?)",
                            (subject_id, title, due_date, priority)).lastrowid


def list_tasks(show_completed=True):
    where = "" if show_completed else "WHERE t.done=0"
    with connection() as conn:
        rows = conn.execute(f"""
            SELECT t.id,t.subject_id,s.name subject,t.title,t.due_date,t.priority,t.done
            FROM tasks t JOIN subjects s ON s.id=t.subject_id {where}
            ORDER BY t.done ASC, CASE t.priority WHEN 'Alta' THEN 0 WHEN 'Média' THEN 1 ELSE 2 END,
                     COALESCE(t.due_date,'9999-12-31'),t.id DESC
        """).fetchall()
    return [dict(row) for row in rows]


def set_task_done(task_id, done=True):
    _positive_int(task_id, "ID")
    with connection() as conn:
        cur = conn.execute("UPDATE tasks SET done=? WHERE id=?", (int(bool(done)),task_id))
        if not cur.rowcount:
            raise ValueError("Tarefa não encontrada.")


def delete_task(task_id):
    _positive_int(task_id, "ID")
    with connection() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        if not cur.rowcount:
            raise ValueError("Tarefa não encontrada.")


def database_backup_bytes():
    """Snapshot SQLite consistente para download, inclusive com app aberto."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp:
            temp_path = Path(temp.name)
        with closing(sqlite3.connect(DB_PATH)) as source, closing(sqlite3.connect(temp_path)) as target:
            source.backup(target)
        return temp_path.read_bytes()
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
