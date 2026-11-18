import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import DATA


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect():
    connection = sqlite3.connect(DATA / 'library.sqlite3', timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, filename TEXT NOT NULL, title TEXT NOT NULL,
            authors TEXT DEFAULT '', abstract TEXT DEFAULT '', year TEXT DEFAULT '',
            arxiv_id TEXT DEFAULT '', doi TEXT DEFAULT '', sha256 TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'queued', progress INTEGER DEFAULT 0,
            page_count INTEGER DEFAULT 0, chunk_count INTEGER DEFAULT 0,
            error TEXT DEFAULT '', warnings TEXT DEFAULT '[]', metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL, source_url TEXT DEFAULT '', starred INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            page INTEGER NOT NULL, ordinal INTEGER NOT NULL, text TEXT NOT NULL,
            bbox TEXT NOT NULL, kind TEXT DEFAULT 'paragraph', heading TEXT DEFAULT '',
            embedding BLOB, embedding_model TEXT DEFAULT '', UNIQUE(doc_id, ordinal)
        );
        CREATE INDEX IF NOT EXISTS chunk_document ON chunks(doc_id,page);
        CREATE TABLE IF NOT EXISTS paper_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            label TEXT NOT NULL, text TEXT NOT NULL, page INTEGER NOT NULL,
            chunk_id INTEGER REFERENCES chunks(id) ON DELETE SET NULL,
            target_doc_id TEXT REFERENCES documents(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS translations (
            chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
            text TEXT NOT NULL, model TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL,
            sources TEXT DEFAULT '[]', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tracking_topics (
            topic TEXT PRIMARY KEY, enabled INTEGER DEFAULT 1, interval_hours INTEGER DEFAULT 24,
            next_run REAL DEFAULT 0, last_run TEXT DEFAULT '', error TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS discoveries (
            topic TEXT NOT NULL, arxiv_id TEXT NOT NULL, payload TEXT NOT NULL,
            found_at TEXT NOT NULL, is_new INTEGER DEFAULT 1, PRIMARY KEY(topic,arxiv_id)
        );
        CREATE TABLE IF NOT EXISTS formulas (
            chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
            latex TEXT NOT NULL, model TEXT NOT NULL, reviewed INTEGER DEFAULT 0, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY, kind TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS translation_jobs (
            doc_id TEXT PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
            status TEXT NOT NULL, completed INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
            error TEXT DEFAULT '', updated_at TEXT NOT NULL
        );
        ''')
        db.execute("UPDATE documents SET status='interrupted',error='上次解析被中断，请重试解析' WHERE status IN ('parsing','indexing')")
        db.execute("UPDATE translation_jobs SET status='interrupted',error='服务重启，已完成译文仍保留，可继续' WHERE status IN ('running','queued')")


def record(kind, message):
    with connect() as db:
        db.execute('INSERT INTO activity(kind,message,created_at) VALUES(?,?,?)', (kind, message, now()))


def document(doc_id):
    with connect() as db:
        row = db.execute('SELECT * FROM documents WHERE id=?', (doc_id,)).fetchone()
    return decode_document(row) if row else None


def decode_document(row):
    result = dict(row)
    for key in ('metadata', 'warnings'):
        result[key] = json.loads(result[key])
    return result
