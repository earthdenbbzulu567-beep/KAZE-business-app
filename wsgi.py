"""
PythonAnywhere WSGI entry.

1. Change YOUR_USERNAME and the folder name if needed.
2. Prefer setting DATABASE_URL and SECRET_KEY in the Web tab
   (Environment variables), not in this file.
3. In the Web tab, set:
      Source code:  /home/YOUR_USERNAME/kaze-business-manager
      WSGI file:    /home/YOUR_USERNAME/kaze-business-manager/wsgi.py
   Or paste this same code into /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
"""
import os
import sys

project_home = "/home/YOUR_USERNAME/kaze-business-manager"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Optional local overrides (leave commented on PythonAnywhere if you use the Web tab):
# os.environ.setdefault("DATABASE_URL", "postgresql://USER:PASS@HOST:PORT/DBNAME")
# os.environ.setdefault("SECRET_KEY", "change-me")

from app import app as application  # noqa: E402
