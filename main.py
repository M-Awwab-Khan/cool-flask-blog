from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import smtplib
import os
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE FLASK LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

# LOAD USER
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# USER GRAVATAR
gravatar = Gravatar(app,
                size=100,
                rating='g',
                default='retro',
                force_default=False,
                force_lower=False,
                use_ssl=False,
                base_url=None)

def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return f(*args, **kwargs)
        return abort(403)
    return wrapper


# TODO: Create a User table for all your registered users. 
class User(UserMixin, db.Model):
    __tablename__ = "registered_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

# CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author = relationship("User", back_populates="posts")
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("registered_users.id"))
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

# COMMENT TABLE
class Comment(db.Model):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    comment_author = relationship("User", back_populates="comments")
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("registered_users.id"))
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

with app.app_context():
    db.create_all()

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        if db.session.execute(db.select(User).where(User.email == email)).scalar():
            flash("This email is already associated with an account. Please log in instead.")
            return redirect(url_for('login'))
        else:
            h_and_s_password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
            new_user = User(
                email = form.email.data,
                password = h_and_s_password,
                name = form.name.data
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        
    return render_template("register.html", form = form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            password = form.password.data
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
        flash("Incorrect email or password")
        return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated, current_user=current_user)

@app.route('/post/<int:post_id>', methods=['POST', 'GET'])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
            new_comment = Comment(
                text = form.comment_text.data,
                comment_author = current_user,
                author_id = current_user.id,
                post_id = post_id,
                parent_post = post
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
        else:
            flash("You need to log in to post a comment.")
            return redirect(url_for('login'))
    return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated, current_user=current_user, form=form, gravatar=gravatar)

@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=datetime.datetime.now().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, logged_in=current_user.is_authenticated)

@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route('/about')
def about():
    return render_template('about.html', logged_in=current_user.is_authenticated)

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
        return render_template('contact.html', msg_sent = True, logged_in=current_user.is_authenticated)
    else:
        return render_template('contact.html',  msg_sent = False, logged_in=current_user.is_authenticated)


if __name__ == "__main__":
    app.run(debug=True)
