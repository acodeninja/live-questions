import io
import time
from typing import Union

import qrcode
from textual import on
from textual import work
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.events import Mount
from textual.widgets import Button
from textual.widgets import OptionList
from textual.widgets import Static
from textual.widgets._option_list import Option
from textual.widgets._option_list import Separator
from textual.worker import get_current_worker

from live_questions.storage import get_questions
from live_questions.storage import mark_question_answered


def get_qr_code(url):
    qr = qrcode.QRCode()
    qr.add_data(url)
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    return f.read()


class QRWidget(Vertical):
    DEFAULT_CSS = """
    QRWidget {
        width: 1fr;
        padding: 5;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="qr")
        yield Static("", id="url")

    def update(self, url):
        self.query_one("#qr", Static).update(get_qr_code(url))
        self.query_one("#url", Static).update(url.removeprefix("https://"))


class QuestionsWidget(Vertical):
    current_question: Union[int, None] = None

    DEFAULT_CSS = """
    QuestionsWidget {
        padding: 5;
    }
    QuestionsWidget OptionList {
        height: 90%;
        margin-bottom: 1;
    }
    QuestionsWidget Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield OptionList()
        yield Button("Answer", variant="success")

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected):
        self.current_question = event.option_index

    @on(Button.Pressed)
    def on_pressed(self, event: Button.Pressed):
        if self.current_question is not None:
            questions_list = self.query_one(OptionList)
            question = questions_list.get_option_at_index(self.current_question)
            mark_question_answered(question.id)
            self.current_question = None
            self.update_questions()

    def update_questions(self):
        questions_list = self.query_one(OptionList)
        questions_list.clear_options()
        questions_list.add_options(
            [
                x
                for xs in [
                    [
                        Option(
                            f"{question.get('question')} ({question.get('votes')})",
                            id=question.get("id"),
                        ),
                        Separator(),
                    ]
                    for question in get_questions()
                ]
                for x in xs
            ]
        )

        if self.current_question is not None:
            questions_list.highlighted = self.current_question


class ConsoleApp(App):
    url: str = None

    def compose(self) -> ComposeResult:
        yield Horizontal(
            QRWidget(),
            QuestionsWidget(),
        )

    @work(thread=True)
    def poll_questions(self):
        worker = get_current_worker()
        questions = self.query_one(QuestionsWidget)
        while not worker.is_cancelled:
            self.call_from_thread(questions.update_questions)
            time.sleep(1)

    @on(Mount)
    def on_mount_event(self, event: Mount) -> None:
        self.query_one(QRWidget).update(self.url)
        self.poll_questions()


def start_console(url):
    app = ConsoleApp()
    app.url = url
    app.run()
