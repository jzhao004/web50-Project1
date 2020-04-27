import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    db.execute("DROP TABLE IF EXISTS users, authors, books, reviews")
    db.execute("CREATE TABLE users(id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    db.execute("CREATE TABLE authors(id SERIAL PRIMARY KEY, author VARCHAR NOT NULL UNIQUE)")
    db.execute("CREATE TABLE books(id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL UNIQUE, title VARCHAR NOT NULL, authorid INT REFERENCES authors, year VARCHAR NOT NULL)")
    db.execute("CREATE TABLE reviews(id SERIAL PRIMARY KEY, userid INT REFERENCES users, bookid INT REFERENCES books, review VARCHAR NOT NULL, rating INT NOT NULL)")

    with open('books.csv') as f:
        reader = csv.reader(f)
        next(reader)

        for isbn, title, author, year in reader:
            db.execute("INSERT INTO authors (author) SELECT :author WHERE NOT EXISTS (SELECT author FROM authors WHERE author = :author)", {"author": author})
            db.execute("INSERT INTO books (isbn, title, authorid, year) VALUES (:isbn, :title, (SELECT id FROM authors WHERE author = :author), :year)", {"isbn": isbn, "title": title, "author": author, "year": year})

    db.commit()

if __name__ == "__main__":
    main()
