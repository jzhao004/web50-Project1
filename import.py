import csv
import os

from flask import Flask, render_template, request
from models import *

app = Flask(__name__)

# Configure session to use filesystem
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    with open('books.csv') as f:
        reader = csv.reader(f)
        next(reader)

        for isbn, title, author, year in reader:
            if not Author.query.filter_by(author=author).first():
                a = Author(author=author)
                db.session.add(a)

            authorid = Author.query.filter_by(author=author).one().id

            b = Book(isbn=isbn, title=title, authorid=authorid, year=year)
            db.session.add(b)

            print(f"Added {title} by {author}")
        db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        main()
