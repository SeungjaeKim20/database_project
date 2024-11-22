from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

@app.route('/')
def show_movies():
    return render_template('index.html')

if __name__ == '__main__':
    app.debug = True
    app.run(host="127.0.0.1", port=5000)