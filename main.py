from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
import datetime
import smtplib
import os

# GMAIL CREDENTIALS
GMAIL_USER = 'mawwabkhank2006@gmail.com'
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# APP CONFIG
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# CKEDITOR CONFIG
ckeditor = CKEditor()
ckeditor.init_app(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

# ADD POST FORM
class BlogPostForm(FlaskForm):
    title = StringField('Blog Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    author = StringField('Your name', validators=[DataRequired()])
    bg_url = StringField('Background image link', validators=[URL()])
    body = CKEditorField('Post Content', validators=[DataRequired()])
    submit = SubmitField('Submit')

with app.app_context():
    db.create_all()

@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)

# TODO: Add a route so that you can click on individual posts.
@app.route('/post/<int:post_id>')
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post)

@app.route('/add-post', methods=['GET', 'POST'])
def add_new_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title= form.title.data,
            subtitle= form.subtitle.data,
            author= form.author.data,
            date = datetime.datetime.now().strftime("%B %d, %Y"),
            img_url= form.bg_url.data,
            body= form.body.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect('/')
    return render_template('make-post.html', form=form, purpose='new')

@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id==post_id)).scalar()
    form = BlogPostForm(
        title=post.title,
        subtitle=post.subtitle,
        author=post.author,
        bg_url=post.img_url,
        body=post.body
    )
    return render_template('make-post.html', form=form, purpose='edit')


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
