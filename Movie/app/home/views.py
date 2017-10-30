from flask import render_template,redirect,url_for
from . import home

@home.route('/')
def index():
    return render_template('home/index.html')

@home.route('/login/')
def login():
    return render_template('home/login.html')

@home.route('/logout/')
def logout():
    return redirect(url_for('home.login'))

@home.route('/register/')
def register():
    return render_template('home/register.html')


@home.route('/user_info/')
def user_info():
    return render_template('home/user_info.html')


@home.route('/change_pwd/')
def change_pwd():
    return render_template('home/change_pwd.html')


@home.route('/comments/')
def comments():
    return render_template('home/comments.html')


@home.route('/login_log/')
def login_log():
    return render_template('home/login_log.html')


@home.route('/movie_col/')
def movie_col():
    return render_template('home/movie_col.html')

@home.route('/animation/')
def animation():
    return render_template('home/animation.html')

@home.route('/search/')
def search():
    return render_template('home/search.html')

@home.route('/play/')
def play():
    return render_template('home/play.html')

