import logging
import threading

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request

from live_questions.settings import Settings
from live_questions.storage import close_connection
from live_questions.storage import create_question
from live_questions.storage import get_questions
from live_questions.storage import upvote_question

app = Flask(__name__)


@app.teardown_appcontext
def teardown_app(exception):
    close_connection()


@app.route("/")
def home():
    return render_template("home.html", questions=get_questions())


@app.route("/question", methods=["POST"])
def post_question():
    question = request.form.get("question", None)
    create_question(question)
    return redirect("/")


@app.route("/question/<question_id>/upvote", methods=["POST"])
def post_vote(question_id):
    upvote_question(question_id)
    return redirect("/")


def app_run(settings: Settings):
    logging.getLogger("werkzeug").disabled = True
    app.run(port=settings.port)


def start_web(settings: Settings):
    threading.Thread(target=app_run, kwargs={"settings": settings}, daemon=True).start()

    print("Web Server Started")
    return app
