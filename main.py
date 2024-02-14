from flask import Flask, render_template, request
import requests
from post import Post
import smtplib
import os

GMAIL_USER = 'mawwabkhank2006@gmail.com'
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

app = Flask(__name__)
response = requests.get('https://api.npoint.io/674f5423f73deab1e9a7')
all_posts = response.json()
posts = [Post(post['id'], post['title'], post['subtitle'], post['body'], post['image_url']) for post in all_posts]

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

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        msg = f"Subject:New Message\n\nName: {request.form['name']}\nEmail: {request.form['email']}\nPhone: {request.form['phone']}\nMessage: {request.form['message']}"
        with smtplib.SMTP('smtp.gmail.com') as connection:
            connection.starttls()
            connection.login(
                user=GMAIL_USER,
                password=GMAIL_PASSWORD
            )
            connection.sendmail(
                from_addr=request.form['email'],
                to_addrs=GMAIL_USER,
                msg=msg
            )
        return render_template('contact.html', msg_sent = True)
    else:
        return render_template('contact.html',  msg_sent = False)


if __name__ == "__main__":
    app.run(debug=True)
