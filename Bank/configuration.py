import os


LOOKUP_HOST = os.environ.get("LOOKUP_HOST", "lookup")
LOOKUP_PORT = int(os.environ.get("LOOKUP_PORT", 22000))