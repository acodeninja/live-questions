import click

from live_questions.console import start_console
from live_questions.ngrok import start_ngrok
from live_questions.settings import load_settings
from live_questions.web import start_web


@click.command(name="live-questions")
@click.option("--port", type=int, default=None, help="Port to run web server on.")
@click.option("--domain", type=str, default=None, help="NGROK Domain to run on.")
def start(port, domain):
    """
    Start a live questions session.
    """
    settings = load_settings(port, domain)

    start_web(settings)
    ngrok = start_ngrok(settings)
    start_console(ngrok.url())


if __name__ == "__main__":
    start()
