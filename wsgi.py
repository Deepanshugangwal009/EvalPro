import os
import sys

project_directory = os.path.dirname(os.path.abspath(__file__))

if project_directory not in sys.path:
    sys.path.insert(0, project_directory)

from app import app as application  # noqa: E402

app = application
