from flask import Flask
import os
from .core.models import db




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = "uploads"

db.init_app(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)