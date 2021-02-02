#!/bin/bash
source ./local_vars.sh
exec poetry run gunicorn -k flask_sockets.worker --bind 0.0.0.0:$PORT  "src.__main__:app" \
"$@"
