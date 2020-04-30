from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    reviews = db.relationship("Review", backref="user", lazy=True)

class Author(db.Model):
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String, nullable=False)
    books = db.relationship("Book", backref="author", lazy=True)

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    authorid = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    year = db.Column(db.String, nullable=False)
    reviews = db.relationship("Review", backref="book", lazy=True)

    def add_review(self, userid, review, rating):
        r = Review(userid=userid, bookid=self.id, review=review, rating=rating)
        db.session.add(r)
        db.session.commit()

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bookid = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    review = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
