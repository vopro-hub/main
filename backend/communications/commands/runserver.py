from django.core.management.base import BaseCommand
from django.conf import settings
import sys

class Command(BaseCommand):
    help = "Run the development server using Daphne (ASGI, supports WebSockets)."

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', help='Optional port number, e.g. 127.0.0.1:8000')
        parser.add_argument('--reload', action='store_true', help='Enable autoreload')

    def handle(self, *args, **options):
        import daphne.cli

        addrport = options.get("addrport") or "127.0.0.1:8000"
        reload = options.get("reload")

        args = [
            "daphne",
            "-b", addrport.split(":")[0],
            "-p", addrport.split(":")[1],
            settings.ASGI_APPLICATION,
        ]

        if reload:
            args.insert(1, "--reload")

        # Run Daphne directly
        sys.argv = args
        daphne.cli.CommandLineInterface().run()
