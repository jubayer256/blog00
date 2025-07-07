import sys
import os

# Add your project directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import your Flask app as WSGI application
from main import app as application
