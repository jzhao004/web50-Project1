## Project 1

Web Programming with Python and JavaScript

This project aims to build a book review website using Flask.

#### Files
This repository contains the following files:
1. application.py
2. import.py: import books.csv to database
3. index.html: login page
4. register.html: registration page
5. successful.html: successful registration page
6. books.html: search page
7. book.html: book page
8. signout.html: successful sign out page

#### Data
1. books.csv: Contains ISBN number, title, author, and publication year of 5000 books
2. Rating data of individual books pulled from goodreads.com

#### Before running Flask
1. set FLASK_APP=application.py
2. set FLASK_DEBUG=1
3. set DATABASE_URL = "Database URL"
4. set Goodreads API key
