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

@app.route('/post/<int:id>')
def show_post(id):
    requested_post = None
    for post in posts:
        if post.id == id:
            requested_post = post
    return render_template('post.html', post=requested_post)

if __name__ == "__main__":
    app.run(debug=True)
