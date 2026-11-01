"""One process keeps conservative free-provider budgets shared by all request threads."""

import os

bind = "0.0.0.0:" + os.environ.get("PORT", "10000")
workers = 1
worker_class = "gthread"
threads = 4
timeout = 45
graceful_timeout = 30
keepalive = 5
accesslog = "-"
# Exclude query strings, headers and bodies (including geocoding query text).
access_log_format = "%(t)s %(m)s %(U)s %(s)s %(L)s"
errorlog = "-"
