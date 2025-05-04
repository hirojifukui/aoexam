# AO/app/__init__.py

from flask import Flask

# create your Flask app, telling it where to find static & template folders
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# import your routes (so decorators get registered)
from app.interview import *    # noqa
