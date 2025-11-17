from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Initialize database (without configuring it yet)
db = SQLAlchemy()