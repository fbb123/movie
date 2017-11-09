from flask import render_template,redirect,url_for,flash,session,request
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from . import home

from app.home.forms import RegisterForm,LoginForm,UserDetailForm,PwdForm,CommentForm
from app.models import User,Userlog,Preview,Tag,Movie,Comment,MovieCol
from app import db,app

import datetime
import uuid
import os


#登录装饰器
def user_login_req(f):
    @wraps(f)
    def decorate_function(*args,**kwargs):
        if 'user' not in session.keys() or session['user'] is None:
            return redirect(url_for("home.login",next=request.url))
        return f(*args,**kwargs)
    return decorate_function




#修改上传文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S")+str(uuid.uuid4().hex)+fileinfo[-1]
    return filename


@home.route('/<int:page>/',methods=["GET"])
def index(page=None):
    tags = Tag.query.all()
    page_data = Movie.query.all()
    tid = request.args.get("tid",0)
    if int(tid)!=0:
        page_data = page_data.filter_by(tag_id=int(tid))
    star = request.args.get("star",0)
    if int(star)!=0:
        page_data = page_data.filter_by(star=int(star))
    time = request.args.get("time",0)
    if int(time)!=0:
        if int(time) == 1:
            page_data = page_data.order_by(Movie.add_time.desc())
        else:
            page_data = page_data.order_by(Movie.add_time.asc())
    pm = request.args.get("pm",0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data = page_data.order_by(Movie.play_num.desc())
        else:
            page_data = page_data.order_by(Movie.play_num.asc())
    cm = request.args.get("cm",0)
    if int(cm) != 0:
        if int(cm) == 1:
            page_data = page_data.order_by(Movie.comment_num.desc())
        else:
            page_data = page_data.order_by(Movie.comment_num.asc())
    if page == None:
        page = 1
    page_data = page_data.paginate(page=page,per_page=10)
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm,
    )
    return render_template('home/index.html',tags=tags,p=p,page_data=page_data)

@home.route('/login/',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data["name"]).first()
        if not user.check_pwd(data["pwd"]):
            flash("密码错误！","error")
            return redirect(url_for("home.login"))
        session["user"] = user.name
        session["user_id"] = user.id
        userlog = Userlog(
            user_id = user.id,
            ip = request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for("home.index"))
    return render_template('home/login.html',form=form)

@home.route('/logout/')
def logout():
    session.pop("user",None)
    session.pop("user_id",None)
    return redirect(url_for('home.login'))

@home.route('/register/',methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        data = form.data
        user = User(
            name = data["name"],
            email = data["email"],
            phone = data["phone"],
            pwd = generate_password_hash(data["pwd"]),
            uuzid = uuid.uuid4().hex
        )
        db.session.add(user)
        db.session.commit()
        flash("注册成功","success")
    return render_template('home/register.html',form=form)


@home.route('/user_info/',methods=["GET","POST"])
@user_login_req
def user_info():
    form = UserDetailForm()
    user = User.query.filter_by(id=int(session["user_id"]))
    form.face.validators=[]
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        if not os.path.exists(app.config["USER_DIR"]):
            os.mkdir(app.config["USER_DIR"])
            os.chmod(app.config["USER_DIR"], "rw")
        if form.face.data.filename != "":
            face_url = secure_filename(form.face.data.filename)
            user.face = change_filename(face_url)
            form.face.data.save(app.config["USER_DIR"] + user.face)
        name_count = User.query.filter_by(name=data["name"]).count()
        if data["name"] != user.name and name_count == 1:
            flash("昵称已经存在","error")
            return redirect(url_for("home.user_info"))
        email_count = User.query.filter_by(email=data["email"]).count()
        if data["email"] != user.email and email_count == 1:
            flash("邮箱已经被注册", "error")
            return redirect(url_for("home.user_info"))
        phone_count = User.query.filter_by(phone=data["phone"]).count()
        if data["phone"] != user.phone and phone_count == 1:
            flash("手机已经被注册", "error")
            return redirect(url_for("home.user_info"))
        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash("修改成功","success")
        return redirect(url_for("home.user_info"))
    return render_template('home/user_info.html',form=form,user=user)


@home.route('/change_pwd/',methods=["GET","POST"])
@user_login_req
def change_pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session["user"]).first()
        from werkzeug.security import generate_password_hash
        user.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(user)
        db.session.commit()
        flash("修改成功","success")
        return redirect(url_for("home.change_pwd"))
    return render_template('home/change_pwd.html',form=form)


@home.route('/comments/<int:page>/',methods=["GET"])
@user_login_req
def comments(page=None):
    if page is None:
        page = 1

    page_data = Comment.query.join(Movie).join(User).filter(Movie.id == Comment.movie_id, User.id == session["user_id"]
                                                            ).order_by(Comment.add_time.desc()
                                                                       ).paginate(page=page, per_page=10)
    return render_template('home/comments.html',page_data=page_data)


@home.route('/login_log/<int:page>/',methods=["GET"])
@user_login_req
def login_log(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.filter_by(user_id=session["user_id"]
    ).order_by(Userlog.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('home/login_log.html',page_data=page_data)



@home.route('/movie_col/add/',methods=["POST"])
@user_login_req
def movie_col_add():
    uid = request.args.get("uid","")
    mid = request.args.get("mid","")
    movie_col = MovieCol(
        user_id = int(uid),
        movie_id = int(mid)
    ).count()
    if movie_col == 1:
        data = dict(ok=0)
    else:
        movie_col = MovieCol(
            user_id = int(uid),
            movie_id = int(mid)
        )
        db.session.add(movie_col)
        db.session.commit()
        data = dict(ok=1)
    import json
    return json.dumps(data)



@home.route('/movie_col/<int:page>/',methods=["GET"])
@user_login_req
def movie_col(page=None):
    if page is None:
        page = 1

    page_data = MovieCol.query.join(Movie).join(User).filter(Movie.id == MovieCol.movie_id, User.id == session["user_id"]
                                                            ).order_by(MovieCol.add_time.desc()
                                                                       ).paginate(page=page, per_page=10)
    return render_template('home/movie_col.html',page_data=page_data)

@home.route('/animation/',methods=["GET"])
def animation():
    data = Preview.query.all()
    return render_template('home/animation.html',data=data)

@home.route('/search/<int:page>/',methods=["GET"])
def search(page=None):
    if page is None:
        page = 1
    key = request.args.get("key","")
    movie_count = Movie.query.filter(Movie.title.ilike('%'+key+'%')).count()
    page_data = Movie.query.filter(Movie.title.ilike('%'+key+'%')
                                        ).order_by(Movie.add_time.desc()).paginate(page=page, per_page=10)
    return render_template('home/search.html',key=key,page_data=page_data,movie_count=movie_count)

@home.route('/play/<int:id>/<int:page>/',methods=["GET","POST"])
def play(id=None,page=None):
    movie = Movie.query.get_or_404(int(id))
    movie.play_num += 1
    form = CommentForm()
    if page is None:
        page = 1

    page_data = Comment.query.join(Movie).join(User).filter(Movie.id==movie.id,User.id==Comment.user_id
                                                                ).order_by(Comment.add_time.desc()
                                                                           ).paginate(page=page,per_page=10)
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content = data["content"],
            movie_id = movie.id,
            user_id = session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        db.session.add(movie)
        db.session.commit()
        movie.comment_num += 1
        flash("评论成功","success")
        return redirect(url_for('home.play',id=movie.id,page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template('home/play.html',movie=movie,form=form,page_data=page_data)


@home.route('/video/<int:id>/<int:page>/', methods=["GET", "POST"])
def video(id=None, page=None):
    movie = Movie.query.get_or_404(int(id))
    movie.play_num += 1
    form = CommentForm()
    if page is None:
        page = 1

    page_data = Comment.query.join(Movie).join(User).filter(Movie.id == movie.id, User.id == Comment.user_id
                                                            ).order_by(Comment.add_time.desc()
                                                                       ).paginate(page=page, per_page=10)
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        db.session.add(movie)
        db.session.commit()
        movie.comment_num += 1
        flash("评论成功", "success")
        return redirect(url_for('home.video', id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template('home/video.html', movie=movie, form=form, page_data=page_data)

