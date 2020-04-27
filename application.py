import os

from flask import Flask, render_template, session, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

key = "1E51H5cFx7m5bNHzJQJKg"

@app.route("/", methods=["GET", "POST"])
def index():
    # If signed out display sign in page, else display search page
    if session.get("userid") is None:
        if request.method == "POST":
            # Authenticate sign in information
            username = request.form.get("username")
            password = request.form.get("password")

            existing_user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

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

            existing_user = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchone()

            if not existing_user:
                db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
                db.commit()
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

        if search_option == "title":
            books = db.execute("SELECT isbn, title, author, year FROM (SELECT * FROM books WHERE LOWER(title) LIKE LOWER(:search_query)) AS r LEFT JOIN authors ON authorid = authors.id", {"search_query": '%' + search_query + '%'}).fetchall()
        elif search_option == "author":
            books = db.execute("SELECT isbn, title, author, year FROM (SELECT * FROM books WHERE authorid IN (SELECT id FROM authors WHERE LOWER(author) LIKE LOWER(:search_query))) AS r LEFT JOIN authors ON authorid = authors.id", {"search_query": '%' + search_query + '%'}).fetchall()
        elif search_option == "isbn":
            books = db.execute("SELECT isbn, title, author, year FROM (SELECT * FROM books WHERE LOWER(isbn) LIKE LOWER(:search_query)) AS r LEFT JOIN authors ON authorid = authors.id", {"search_query": '%' + search_query + '%'}).fetchall()
        else:
            books = db.execute("SELECT isbn, title, author, year FROM (SELECT * FROM books WHERE LOWER(title) LIKE LOWER(:search_query) OR LOWER(isbn) LIKE LOWER(:search_query) OR authorid IN (SELECT id FROM authors WHERE LOWER(author) LIKE LOWER(:search_query))) AS r LEFT JOIN authors ON authorid = authors.id", {"search_query": '%' + search_query + '%'}).fetchall()

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
        book = db.execute("SELECT isbn, title, author, year FROM (SELECT * FROM books WHERE isbn=:isbn) AS r LEFT JOIN authors ON authorid = authors.id", {"isbn": isbn}).fetchone()

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
            review_exist = db.execute("SELECT * FROM (SELECT bookid FROM reviews WHERE userid=:userid) AS r1 INNER JOIN (SELECT id FROM books WHERE isbn=:isbn) AS r2 ON bookid = id", {"userid": session["userid"], "isbn": isbn}).fetchone()

            if not review_exist:
                review = request.form.get("review")
                rating = request.form.get("rating")
                db.execute("INSERT INTO reviews (userid, bookid, review, rating) VALUES (:userid, (SELECT id FROM books WHERE isbn=:isbn), :review, :rating)", {"userid": session["userid"], "isbn": isbn, "review": review, "rating": rating})
                db.commit()
            else:
                message="You have already submitted a review for this book."

        reviews = db.execute("SELECT username, review, rating FROM (SELECT * FROM reviews INNER JOIN (SELECT id FROM books WHERE isbn=:isbn) AS r1 ON bookid=r1.id) AS r2 INNER JOIN users ON userid = users.id", {"isbn": isbn}).fetchall()

        return render_template("book.html", book=book, reviews=reviews, ratings_count=ratings_count, average_rating=average_rating, message=message)


@app.route("/api/<isbn>", methods=["GET", "POST"])
def book_api(isbn):
    # Generate API response
    book = db.execute("SELECT isbn, title, author, year FROM (SELECT * FROM books WHERE isbn=:isbn) AS r LEFT JOIN authors ON authorid = authors.id", {"isbn": isbn}).fetchone()

    if not book:
        return jsonify({"error": "Invalid ISBN"}), 404

    review = db.execute("SELECT COUNT(review) AS review_count, CAST(ROUND(AVG(rating),2) AS float) as average_score FROM reviews INNER JOIN (SELECT id FROM books WHERE isbn=:isbn) AS r ON bookid=r.id", {"isbn": isbn}).fetchone()

    return jsonify({
    "title": book.title,
    "author": book.author,
    "year": book.year,
    "isbn": book.isbn,
    "review_count": review.review_count,
    "average_score": review.average_score
    })
