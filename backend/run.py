"""Development entry point for the Flask + Socket.IO application."""

import eventlet

# Eventlet must patch the standard library before importing application modules.
eventlet.monkey_patch()

from app import app_with_socketio  # noqa: E402


def main() -> None:
    # Eventlet writes the raw request target directly to its log stream, which
    # would expose assessment capability tokens embedded in legacy URLs. The
    # Flask request logger already records a redacted, structured access line.
    eventlet.wsgi.server(
        eventlet.listen(("0.0.0.0", 5000)),
        app_with_socketio,
        log_output=False,
    )


if __name__ == "__main__":
    main()
