from flask import Flask, redirect, render_template, flash, request, url_for
from datetime import datetime
from flask_uploads import configure_uploads
from forms import *
from models import *
import os
import requests
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_uploads import configure_uploads
from sqlalchemy import func
from api import api

app = Flask(__name__)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/images'
app.config['SECRET_KEY'] = 'asddsglkjkl'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
db.init_app(app)
app.app_context().push()
db.create_all()
configure_uploads(app, photos)
login = LoginManager(app)
login.login_view = 'login'
api.init_app(app)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def who_to_watch(user):
    # Get a random 3 users from database
    return User.query.filter(User.id != user.id).order_by(func.random()).limit(3).all()

@app.route('/')
@app.route('/index')
@login_required
def index():
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    followed = current_user.followed.all()
    followed_ids = [user.id for user in followed]
    followed_ids.append(current_user.id)
    # posts = Post.query.filter(Post.user_id.in_(followed_ids)).all()
    posts = Post.query.filter(Post.user_id.in_(followed_ids)).order_by(Post.timestamp.desc()).all()
    whom_to_watch = who_to_watch(current_user)
    hour = datetime.now().hour
    return render_template('index.html', title='Home', posts=posts, who_to_watch=whom_to_watch, hour=hour)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignUpForm()
    if form.validate_on_submit():
        request.files['dp'].seek(0)
        dp = photos.save(request.files['dp'])
        user = User(username=form.username.data, email=form.email.data, dp=dp)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {user.username}! You can now log in')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/explore')
def explore():
    API_KEY = '261aca2698ca4bc0957e606fe5f16ae5'
    ENDPOINT_URL = 'https://newsapi.org/v2/top-headlines'
    params = {'country': 'in','apiKey': API_KEY, 'category':'technology'}
    response = requests.get(ENDPOINT_URL, params=params)
    if response.status_code == 200:
        headlines = response.json()['articles']
    else:
        headlines = []
    top_posts = Post.query.outerjoin(Like).group_by(Post.id).order_by(func.count(Like.id).desc()).limit(5).all()
    return render_template('explore.html', title='Explore', headlines=headlines, top_posts=top_posts)

@app.route('/post', methods=['Get', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        # image_filename = photos.save(form.image.data) # print(photos.save(request.files['image']))
        request.files['image'].seek(0)
        image_url = photos.save(request.files['image'])
        new_post = Post(title=form.title.data, body=form.description.data, image=image_url, author = current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully')
        return redirect(url_for('index'))  
    return render_template('new_post.html', title='Create post', form=form)

@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You can not edit others post')
        return redirect(url_for('index'))
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.description.data
        if form.image.data:
            request.files['image'].seek(0)
            image_url = photos.save(request.files['image'])
            post.image = image_url
        db.session.commit()
        flash('Your post has been updated')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.description.data = post.body
        form.image.data = post.image
    return render_template('update.html', title='Upadet post', form=form, post=post)

@app.route('/post/<int:post_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post.author != current_user:
        flash('You can not delete others post')
        return redirect(url_for('index'))
    os.remove(os.path.join(app.config['UPLOADED_PHOTOS_DEST'], post.image))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted')
    return redirect(url_for('index'))

@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
        followers_count = user.followers.count()
        following_count = user.followed.count()

        return render_template('profile.html', title=username, user=user, posts=posts, followers_count=followers_count, following_count=following_count, posts_count=len(posts))
    else:
        flash('User does not exist')
        return redirect(url_for('register'))

@app.route('/user/update', methods=['GET', 'POST'])
@login_required
def update_user():
    user = User.query.filter_by(username=current_user.username).first()
    if user:
        form = EditProfile()
        if form.validate_on_submit():
            user.email = form.email.data
            user.bio = form.bio.data
            if form.dp.data:
                request.files['dp'].seek(0)
                image_url = photos.save(request.files['dp'])
                user.dp = image_url
            db.session.commit()
            flash('Your profile has been updated')
            return redirect(url_for('user', username=current_user.username))
        elif request.method == 'GET':
            form.email.data = user.email
            form.bio.data = user.bio
            form.dp.data = user.dp
        return render_template('edit_profile.html', form=form)
    else:
        flash('User does not exist')
        return redirect(url_for('register'))

@app.route('/user/delete', methods=['GET', 'POST'])
@login_required
def delete_user():
    db.session.delete(current_user)
    # print("Done")
    db.session.commit()
    # print("Commited")
    flash('Your account has been deleted')
    return redirect(url_for('register'))

@app.route('/follow/<username>')
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return 'User not found'
    if user == current_user:
        return 'You cannot follow yourself'
    if current_user.is_following(user):
        return 'You are already following this user'

    current_user.followed.append(user)
    db.session.add(current_user)
    db.session.commit()
    flash(f'You are now following {username}')
    return redirect(url_for('index'))

@app.route('/unfollow/<username>')
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return 'User not found'
    if not current_user.is_following(user):
        return 'You are not following this user'

    current_user.followed.remove(user)
    db.session.add(current_user)
    db.session.commit()
    flash(f'You are no longer following {username}')
    return redirect(url_for('index'))

@app.route('/following/<username>')
def following(username):
    u = User.query.filter_by(username=username).first()
    following = u.followed.all()
    return render_template('following.html', title='following', users = following)

@app.route('/followers/<username>')
def followers(username):
    u = User.query.filter_by(username=username).first()
    followers = u.followers.all()
    return render_template('followers.html', title='followers', users = followers)


@app.route('/search', methods=['Post'])
@login_required
def search():
    input = request.form.get('input')
    users = User.query.filter(User.username.contains(input)).all()
    return render_template('search.html', title='search', users=users)

@app.route('/comment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(user_id=current_user.id, post_id=post.id, content=form.content.data)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('comment', post_id=post.id))
    all_comments = Comment.query.filter_by(post_id=post.id).all()
    return render_template('comment.html', form=form, post=post, all_comments=all_comments, User=User)

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    if comment.user_id != current_user.id:
        flash('You can not delete others comment')
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully')
    return redirect(url_for('comment', post_id=post_id))


@app.route('/like/<int:post_id>')
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like_post(post)
    flash(f'You liked the {post.title} post')
    return redirect(url_for('index'))

@app.route('/unlike/<int:post_id>')
@login_required
def unlike(post_id):
    post = Post.query.get_or_404(post_id)
    unlike_post(post)
    flash(f'You disliked the {post.title} post')
    return redirect(url_for('index'))

def like_post(post):
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like is None:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()

def unlike_post(post):
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like is not None:
        Like.query.filter_by(user_id=current_user.id, post_id=post.id).delete()
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)