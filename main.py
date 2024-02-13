from flask import Flask, render_template
import requests
from post import Post

app = Flask(__name__)
response = requests.get('https://api.npoint.io/c790b4d5cab58020d391')
all_posts = response.json()
posts = [Post(post['id'], post['title'], post['subtitle'], post['body']) for post in all_posts]

@app.route('/')
def home():
    return render_template("index.html", posts=posts)

if __name__ == "__main__":
    app.run(debug=True)
