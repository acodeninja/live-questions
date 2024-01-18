import json
import os
import random
import subprocess
from pathlib import Path

import click
import dotenv
import inquirer
import yaml


class Settings:
    port: int = None
    ngrok_domain: str = None
    ngrok_auth_token: str = None
    ngrok_api_key: str = None


def load_settings(port: int = None, domain: str = None) -> Settings:
    dotenv.load_dotenv()

    settings = Settings()
    settings.port = (
        port if port else int(os.environ.get("PORT", random.randint(9001, 9999)))
    )
    settings.ngrok_domain = domain if domain else os.environ.get("NGROK_DOMAIN")
    settings.ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
    settings.ngrok_api_key = os.environ.get("NGROK_API_KEY")

    if not settings.ngrok_domain or not settings.ngrok_auth_token:
        try:
            ngrok_config = subprocess.run(
                ["ngrok", "config", "check"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            ngrok_config_output = ngrok_config.stdout.decode("utf-8")
            ngrok_config_file = Path(
                ngrok_config_output.replace("\n", "").removeprefix(
                    "Valid configuration file at "
                )
            )

            ngrok_config = yaml.safe_load(ngrok_config_file.read_text())

            if not settings.ngrok_auth_token and "authtoken" in ngrok_config:
                settings.ngrok_auth_token = ngrok_config.get("authtoken")

            if not settings.ngrok_api_key and "api_key" in ngrok_config:
                settings.ngrok_api_key = ngrok_config.get("api_key")

            if not settings.ngrok_domain:
                domains = []
                if "tunnels" in ngrok_config:
                    for tunnel in ngrok_config.get("tunnels").values():
                        if "domain" in tunnel:
                            domains.append(tunnel.get("domain"))

                if settings.ngrok_api_key:
                    domain_list_output = subprocess.run(
                        [
                            "ngrok",
                            "api",
                            "reserved-domains",
                            "list",
                            "--api-key",
                            settings.ngrok_api_key,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    response = json.loads(domain_list_output.stdout.decode("utf-8"))
                    reserved_domains = response.get("reserved_domains", [])
                    for domain in reserved_domains:
                        domains.append(domain.get("domain"))

                if domains:
                    settings.ngrok_domain = inquirer.prompt(
                        [
                            inquirer.List(
                                "domain",
                                "Which NGROK domain would you like to use?",
                                choices=domains,
                            ),
                        ]
                    ).get("domain")

        except FileNotFoundError:
            click.secho("NGROK auth token not found!", fg="red")
            click.echo(
                "Either set NGROK_AUTH_TOKEN, or install and configure NGROK "
                "https://ngrok.com/docs/getting-started/"
            )
            exit(2)

    return settings
