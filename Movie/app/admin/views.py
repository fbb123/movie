from flask import render_template,redirect,url_for,flash,session,request,abort
from functools import wraps
from werkzeug.utils import secure_filename
from . import admin
from app.admin.forms import LoginForm,TagForm,MovieForm,PreviewForm,PwdForm,AuthForm,RoleForm,AdminForm
from app.models import Admin,Tag,Movie,Preview,User,Comment,MovieCol,OperationLog,AdminLog,Userlog,Auth,Role
from app import db,app

import os
import uuid
import datetime

#上下文应用处理器
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return data

#登录装饰器
def admin_login_req(f):
    @wraps(f)
    def decorate_function(*args,**kwargs):
        if 'admin' not in session.keys() or session['admin'] is None:
            return redirect(url_for("admin.login"))
        return f(*args,**kwargs)
    return decorate_function


#权限控制装饰器
def admin_auth(f):
    @wraps(f)
    def decorate_function(*args,**kwargs):
        admin = Admin.query.join(Role).filter(Role.id==Admin.role_id,Admin.id==session["admin_id"]).first()
        auths = admin.role.auths
        auths = list(map(lambda v:int(v),auths.split(",")))
        auth_list = Auth.query.all()
        urls = [v.url for v in auth_list for val in auths if val==v.id]
        rule = request.url_rule
        if str(rule) not in urls:
            abort(404)
        return f(*args,**kwargs)
    return decorate_function


#修改上传文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S")+str(uuid.uuid4().hex)+fileinfo[-1]
    return filename


@admin.route("/")
@admin_login_req
@admin_auth
def index():
    return render_template('admin/index.html')

@admin.route("/login/",methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin.check_pwd(data['pwd']):
            flash("密码错误")
            return redirect(url_for("admin.login"))
        session['admin'] = data['account']
        session['admin_id'] = admin.id
        admin_log = AdminLog(
            admin_id = admin.id,
            ip = request.remote_addr,
        )
        db.session.add(admin_log)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html',form=form)

@admin.route("/logout/")
@admin_login_req
def logout():
    session.pop("admin",None)
    session.pop("admin_id",None)
    return redirect(url_for('admin.login'))

@admin.route("/change_pwd/")
@admin_login_req
def change_pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改成功")
        return redirect(url_for("admin.change_pwd"))
    return render_template('admin/change_pwd.html',form=form)

@admin.route("/tag/add/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag==1:
            flash("标签已经存在！","error")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(
            name = data["name"]
        )
        db.session.add(tag)
        db.session.commit()
        flash("添加成功","success")
        oplog = OperationLog(
            admin_id = session["admin_id"],
            ip = request.remote_addr,
            reason = "添加标签%s" %data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
    return render_template('admin/tag_add.html',form=form)

@admin.route("/tag/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def tag_list(page=None):
    if page is None:
        page = 1
    page_data = Tag.query.order_by(Tag.add_time.desc()).paginate(page=page,per_page=1)
    return render_template('admin/tag_list.html',page_data=page_data)


@admin.route("/tag/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def tag_del(id=None):
     tag = Tag.query.filter_by(id=id).first_or_404()
     db.session.delete(tag)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.tag_list",page=1))


@admin.route("/tag/edit/<int:id>/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def tag_edit(id=None):
     form = TagForm()
     data = form.data
     tag = Tag.query.filter_by(id=id).first_or_404()
     if form.validate_on_submit():
         exist_tag = Tag.query.filter_by(name=data["name"]).first()
         if exist_tag and exist_tag.name != tag.name:
             flash("标签已经存在！", "error")
             return redirect(url_for("admin.tag_edit", id=id))
         tag.name = data["name"]
         db.session.add(tag)
         db.session.commit()
         flash("修改成功！","success")
         return redirect(url_for("admin.tag_edit",id=id))
     return render_template("admin/tag_edit.html",form=form,tag=tag)


@admin.route("/movie/add/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.mkdir(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"],"rw")
        url = change_filename(file_url)
        logo = change_filename(file_logo)
        form.url.data.save(app.config["UP_DIR"]+url)
        form.logo.data.save(app.config["UP_DIR"]+logo)
        movie = Movie(
            title = data["title"],
            url = url,
            info = data["info"],
            logo = logo,
            star = int(data["star"]),
            play_num = 0,
            comment_num = 0,
            tag_id = int(data["tag"]),
            area = data["area"],
            release_time = data["release_time"],
            length = data["length"],
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加成功！","success")
        return redirect(url_for("admin.movie_add"))
    return render_template('admin/movie_add.html',form=form)

@admin.route("/movie/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def movie_list(page=None):
    if page is None:
        page = 1
    page_data = Movie.query.join(Tag).filter(Tag.id==Movie.tag_id).order_by\
        (Movie.add_time.desc()).paginate(page=page,per_page=10)

    return render_template('admin/movie_list.html',page_data=page_data)


@admin.route("/movie/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def movie_del(id=None):
     movie = Movie.query.filter_by(id=id).first_or_404()
     db.session.delete(movie)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.movie_list",page=1))


@admin.route("/movie/edit/<int:id>/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.filter_by(id=id).first_or_404()
    if request.method == "GET":
        form.info.data = movie.info
        form.tag.data = movie.tag_id
        form.star.data = movie.star
    if form.validate_on_submit():
        data = form.data
        existed_movie = Movie.query.filter_by(title=data["title"]).first()
        if existed_movie and existed_movie.title != movie.title:
            flash("电影已经存在","error")
            return redirect(url_for("admin.movie_edit", id=movie.id))
        if not os.path.exists(app.config["UP_DIR"]):
            os.mkdir(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        if form.url.data.filename != "":
            file_url = secure_filename(form.url.data.filename)
            movie.url = change_filename(file_url)
            form.url.data.save(app.config["UP_DIR"] + movie.url)

        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)
        movie.star = data["star"]
        movie.tag_id = data["tag"]
        movie.info = data["info"]
        movie.title = data["title"]
        movie.area = data["area"]
        movie.length = data["length"]
        movie.release_time = data["release_time"]
        db.session.add(movie)
        db.session.commit()
        flash("修改成功","success")
        return redirect(url_for("admin.movie_edit",id=movie.id))
    return render_template('admin/movie_edit.html',form=form,movie=movie)


@admin.route("/preview/add/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.mkdir(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        logo = change_filename(file_logo)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        preview = Preview(
            title=data["title"],
            logo=logo,
        )
        db.session.add(preview)
        db.session.commit()
        flash("添加成功！", "success")
        return redirect(url_for("admin.preview_add"))
    return render_template('admin/preview_add.html',form=form)

@admin.route("/preview/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def preview_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(Preview.add_time.desc()).paginate(page=page, per_page=10)
    return render_template('admin/preview_list.html',page_data=page_data)


@admin.route("/preview/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def preview_del(id=None):
     preview = Preview.query.filter_by(id=id).first_or_404()
     db.session.delete(preview)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.preview_list",page=1))


@admin.route("/preview/edit/<int:id>/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.filter_by(id=id).first_or_404()
    if form.validate_on_submit():
        data = form.data
        existed_preview = Preview.query.filter_by(title=data["title"]).first()
        if existed_preview and existed_preview.title != preview.title:
            flash("预告已经存在","error")
            return redirect(url_for("admin.preview_edit", id=preview.id))
        if not os.path.exists(app.config["UP_DIR"]):
            os.mkdir(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)
        preview.title = data["title"]
        db.session.add(preview)
        db.session.commit()
        flash("修改成功","success")
        return redirect(url_for("admin.preview_edit",id=preview.id))
    return render_template('admin/preview_edit.html',form=form,preview=preview)



@admin.route("/user/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def user_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(Preview.add_time.desc()).paginate(page=page, per_page=10)
    return render_template('admin/user_list.html',page_data=page_data)

@admin.route("/user/info/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def user_info(id=None):
    user = User.query.get_or_404(id=id)
    return render_template('admin/user_info.html',user=user)


@admin.route("/user/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def user_del(id=None):
     user = User.query.filter_by(id=id).first_or_404()
     db.session.delete(user)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.user_list",page=1))


@admin.route("/comment/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def comment_list(page=None):
    if page is None:
        page=1
    page_data = Comment.query.join(Movie).join(User).filter(
        Movie.id==Comment.movie_id,
        User.id==Comment.user_id
    ).order_by(Comment.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/comment_list.html',page_data=page_data)

@admin.route("/comment/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def comment_del(id=None):
     comment = Comment.query.filter_by(id=id).first_or_404()
     db.session.delete(comment)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.comment_list",page=1))


@admin.route("/movie_col/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def movie_col_list(page=None):
    if page is None:
        page=1
    page_data = MovieCol.query.join(Movie).join(User).filter(
        Movie.id==MovieCol.movie_id,
        User.id==MovieCol.user_id
    ).order_by(MovieCol.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/movie_col_list.html',page_data=page_data)


@admin.route("/movie_col/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def movie_col_del(id=None):
     movie_col = MovieCol.query.filter_by(id=id).first_or_404()
     db.session.delete(movie_col)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.movie_col_list",page=1))


@admin.route("/operation_log/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def operation_log_list(page=None):
    if page is None:
        page = 1
    page_data = OperationLog.query.join(Admin).filter(
        Admin.id==OperationLog.admin_id,
    ).order_by(OperationLog.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/operation_log_list.html',page_data=page_data)

@admin.route("/admin_loginlog/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def admin_loginlog_list(page=None):
    if page is None:
        page = 1
    page_data = AdminLog.query.join(Admin).filter(
        Admin.id==AdminLog.admin_id,
    ).order_by(AdminLog.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/admin_loginlog_list.html',page_data=page_data)

@admin.route("/user_loginlog/list/<int:page>/")
@admin_login_req
@admin_auth
def user_loginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.join(User).filter(
        User.id==Userlog.user_id,
    ).order_by(Userlog.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/user_loginlog_list.html',page_data=page_data)

@admin.route("/role/add/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role = Role(
            name=data["name"],
            auths = ",".join(map(lambda v:str(v),data["auths"])
        ))
        db.session.add(role)
        db.session.commit()
        flash("添加成功","success")
    return render_template('admin/role_add.html',form=form)

@admin.route("/role/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def role_list(page=None):
    if page is None:
        page = 1
    page_data = Role.query.order_by(Role.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/role_list.html',page_data=page_data)

@admin.route("/role/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def role_del(id=None):
     role = Role.query.filter_by(id=id).first_or_404()
     db.session.delete(role)
     db.session.commit()
     flash("删除成功！","sucess")
     return redirect(url_for("admin.role_list",page=1))


@admin.route("/role/edit/<int:id>/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.filter_by(id=id).first()
    if request.method == "GET":
        form.auths.data = list(map(lambda v:int(v),role.auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        role.name = data["name"]
        role.auths = ",".join(map(lambda v:str(v),data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash("修改成功","success")
        return redirect(url_for("admin.role_edit",id=role.id))
    return render_template('admin/role_edit.html',form=form,role=role)

@admin.route("/auth/add/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name = data["name"],
            url = data["url"]
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加成功","success")
    return render_template('admin/auth_add.html',form=form)

@admin.route("/auth/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def auth_list(page=None):
    if page is None:
        page = 1
    page_data = Auth.query.order_by(Auth.add_time.desc()).paginate(page=page,per_page=10)
    return render_template('admin/auth_list.html',page_data=page_data)

admin.route("/auth/del/<int:id>/",methods=["GET"])
@admin_login_req
@admin_auth
def auth_del(id=None):
    auth = Auth.query.filter_by(id=id).first()
    db.session.delete(auth)
    db.session.commit()
    flash("删除成功","success")
    return redirect(url_for("admin.auth_list",page=1))

@admin.route("/auth/edit/<int:id>/",methods=["GET","POST"])
@admin_login_req
@admin_auth
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.filter_by(id=id).first()
    if form.validate_on_submit():
        data = form.data
        auth.name = data["name"]
        auth.url = data["url"]
        db.session.add(auth)
        db.session.commit()
        flash("修改成功","success")
        return redirect(url_for("admin.auth_edit",id=auth.id))
    return render_template('admin/auth_edit.html',form=form,auth=auth)

@admin.route("/admin/add/")
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data["name"],
            pwd = generate_password_hash(data["pwd"]),
            role_id = data["role_id"],
            is_super = 1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加成功","success")
    return render_template('admin/admin_add.html',form=form)

@admin.route("/admin/list/<int:page>/",methods=["GET"])
@admin_login_req
@admin_auth
def admin_list(page=None):
    if page is None:
        page = 1
    page_data = Admin.query.join(Role).filter(Admin.role_id==Role.id).order_by(Admin.add_time.desc()).paginate(page=page, per_page=10)
    return render_template('admin/admin_list.html',page_data=page_data)