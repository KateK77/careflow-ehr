"""Serve the real Django app on a private loopback port using a fresh SQLite file."""
import os
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def main():
    directory = Path(sys.argv[1]).resolve(strict=True)
    database = directory / "computer-use-qa.sqlite3"
    database.touch(exist_ok=False)
    os.environ["CAREFLOW_DB_PATH"] = str(database)
    os.environ["DJANGO_SETTINGS_MODULE"] = "careflow.settings"
    application = StaticFilesHandler(get_wsgi_application())
    call_command("migrate", verbosity=0, interactive=False)
    with make_server("127.0.0.1", 0, application, handler_class=QuietHandler) as server:
        ready = directory / "server-port"
        staging = ready.with_suffix(".tmp")
        staging.write_text(str(server.server_port), encoding="ascii")
        staging.replace(ready)
        server.serve_forever()


if __name__ == "__main__":
    main()
