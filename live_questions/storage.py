import sqlite3
from pathlib import Path

from flask import g

DATABASE = Path.cwd().joinpath("questions.sqlite3")


def get_read_connection():
    return sqlite3.connect(DATABASE)


def migrate(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question text NOT NULL,
            answered bool DEFAULT false,
            created datetime DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            question_id int NOT NULL, 
            created datetime DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    """
    )
    return db


def get_db():
    try:
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
        return migrate(db)
    except RuntimeError:
        return migrate(sqlite3.connect(DATABASE))


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def close_connection():
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def get_questions():
    return [
        {"id": q[0], "question": q[1], "created": q[2], "votes": q[3]}
        for q in query_db(
            """
        SELECT questions.id, questions.question, questions.created, COUNT(votes.id) vote_count
        FROM questions
        LEFT JOIN votes ON questions.id = votes.question_id
        WHERE questions.answered = 0
        GROUP BY questions.id
        ORDER BY vote_count DESC
        """
        )
    ]


def create_question(question):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO questions (question) VALUES (?)", [question])
    db.commit()


def upvote_question(question_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO votes (question_id) VALUES (?)", [question_id])
    db.commit()


def mark_question_answered(question_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE questions SET answered = 1 WHERE id = ?", [question_id])
    db.commit()
