"""SQLite database for tracking published posts."""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "posts.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT,
            instagram_text TEXT,
            image_path TEXT,
            instagram_post_id TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_post(original_text, instagram_text, image_path, status="draft"):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO posts (original_text, instagram_text, image_path, status) VALUES (?, ?, ?, ?)",
        (original_text, instagram_text, image_path, status)
    )
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id


def update_post_published(post_id, instagram_post_id):
    conn = get_connection()
    conn.execute(
        "UPDATE posts SET status='published', instagram_post_id=?, published_at=? WHERE id=?",
        (instagram_post_id, datetime.now().isoformat(), post_id)
    )
    conn.commit()
    conn.close()


def update_post_status(post_id, status):
    conn = get_connection()
    conn.execute("UPDATE posts SET status=? WHERE id=?", (status, post_id))
    conn.commit()
    conn.close()


def get_recent_posts(limit=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM posts ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows
