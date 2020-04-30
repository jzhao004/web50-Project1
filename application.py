import os

from flask import Flask, render_template, session, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
import requests
from models import *

app = Flask(__name__)

# Configure session to use filesystem
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = '\xcd\xf3\x81A9\xe2\xfby=\xcd\xc5?\x1e\xb8\xd2\xc8;{\x82"\xf7@\x84\xa3\x07'
db.init_app(app)

key = "1E51H5cFx7m5bNHzJQJKg"

@app.route("/", methods=["GET", "POST"])
def index():
    # If signed out display sign in page, else display search page
    if session.get("userid") is None:
        if request.method == "POST":
            # Authenticate sign in information
            username = request.form.get("username")
            password = request.form.get("password")

            existing_user = User.query.filter_by(username=username).first()

            if not existing_user:
                return render_template("index.html", message="Username does not exist.")
            elif password != existing_user.password:
                return render_template("index.html", message="Incorrect password.")
            else:
                    session["userid"] = existing_user.id
                    return render_template("books.html")
        else:
            return render_template("index.html")
    else:
        return render_template("books.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # If signed out display registration page, else display search page
    if session.get("userid") is None:
        if request.method == "POST":
            # Create new user account
            username = request.form.get("username")
            password = request.form.get("password")

            existing_user = User.query.filter_by(username=username).first()

            if not existing_user:
                u = User(username=username, password=password)
                db.session.add(u)
                db.session.commit()
                return render_template("success.html")
            else:
                return render_template("register.html", message="This username is already taken.")
        else:
                return render_template("register.html")
    else:
        return render_template("books.html")

@app.route("/signout")
def signout():
    # If signed out display sign in page, else display successful sign out page
    if session.get("userid") is None:
        return render_template("index.html")
    else:
        session.pop("userid", None)
        return render_template("signout.html")

@app.route("/books", methods=["GET", "POST"])
def books():
    # If signed out display sign in page, else display search page
    if session.get("userid") is None:
        return render_template("index.html")
    elif request.method == "POST":
        # Generate search results
        search_query = request.form.get("search_query")
        search_option = request.form.get("search_option")

        books = None
        if search_option in ["title", "all"]:
            books = Book.query.filter(func.lower(Book.title).like("%" + func.lower(search_query) + "%")).all()

        if search_option in ["author", "all"]:
            authorid = [a.id for a in Author.query.filter(func.lower(Author.author).like("%" + func.lower(search_query) + "%")).all()]
            b = Book.query.filter(Book.authorid.in_(authorid)).all()
            books = b if not books else books + b

        if search_option in ["isbn", "all"]:
            b = Book.query.filter(func.lower(Book.isbn).like("%" + func.lower(search_query) + "%")).all()
            books = b if not books else books + b


        if not books:
            return render_template("books.html", message="No matches found.")
        else:
            return render_template("books.html", books=books)
    else:
        return render_template("books.html")


@app.route("/books/<isbn>", methods=["GET", "POST"])
def book(isbn):
    # If signed out display sign in page, else display book page
    if session.get("userid") is None:
        return render_template("index.html")
    else:
        # Retrieve book information
        book = Book.query.filter_by(isbn=isbn).one()

        if not book:
            return render_template("error.html", message="Book not found.")

        goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
        goodreads_data = goodreads.json()

        if goodreads.status_code != 200:
            ratings_count = "Not Available"
            average_rating = "Not Available"
        else:
            ratings_count = goodreads_data["books"][0]["work_ratings_count"]
            average_rating = goodreads_data["books"][0]["average_rating"]

        message = None

        if request.method == "POST":
            # Check if user has already submitted review. If not, add review to page.
            review_exist = Review.query.filter_by(userid=session["userid"], bookid=book.id).first()

            if not review_exist:
                review = request.form.get("review")
                rating = request.form.get("rating")
                book.add_review(userid=session["userid"], review=review, rating=rating)
            else:
                message="You have already submitted a review for this book."

        reviews = Review.query.filter_by(bookid=book.id).all()
        return render_template("book.html", book=book, reviews=reviews, ratings_count=ratings_count, average_rating=average_rating, message=message)


@app.route("/api/<isbn>", methods=["GET", "POST"])
def book_api(isbn):
    # Generate API response
    book = Book.query.filter_by(isbn=isbn).one()
    if not book:
        return jsonify({"error": "Invalid ISBN"}), 404

    review_count = Review.query.filter_by(bookid=book.id).count()
    average_score = db.session.query(func.avg(Review.rating)).filter_by(bookid=book.id).scalar()

    return jsonify({
    "title": book.title,
    "author": book.author.author,
    "year": book.year,
    "isbn": book.isbn,
    "review_count": review_count,
    "average_score": round(float(average_score), 2)
    })
