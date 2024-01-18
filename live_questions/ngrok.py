import ngrok

from live_questions.settings import Settings


def start_ngrok(settings: Settings):
    listener = ngrok.forward(
        f"http://localhost:{settings.port}",
        authtoken=settings.ngrok_auth_token,
        domain=settings.ngrok_domain,
    )

    print("NGROK Tunnel Started")

    return listener
