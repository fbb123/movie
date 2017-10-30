from flask import render_template,redirect,url_for
from . import admin

@admin.route("/")
def index():
    return render_template('admin/index.html')

@admin.route("/login/")
def login():
    return render_template('admin/login.html')

@admin.route("/logout/")
def logout():
    return redirect(url_for('admin.login'))

@admin.route("/change_pwd/")
def change_pwd():
    return render_template('admin/change_pwd.html')

@admin.route("/tag/add/")
def tag_add():
    return render_template('admin/tag_add.html')

@admin.route("/tag/list/")
def tag_list():
    return render_template('admin/tag_list.html')

@admin.route("/movie/add/")
def movie_add():
    return render_template('admin/movie_add.html')

@admin.route("/movie/list/")
def movie_list():
    return render_template('admin/movie_list.html')

@admin.route("/preview/add/")
def preview_add():
    return render_template('admin/preview_add.html')

@admin.route("/preview/list/")
def preview_list():
    return render_template('admin/preview_list.html')

@admin.route("/user/list/")
def user_list():
    return render_template('admin/user_list.html')

@admin.route("/user/info/")
def user_info():
    return render_template('admin/user_info.html')

@admin.route("/comment/list/")
def comment_list():
    return render_template('admin/comment_list.html')

@admin.route("/movie_col/list/")
def movie_col_list():
    return render_template('admin/movie_col_list.html')

@admin.route("/operation_log/list/")
def operation_log_list():
    return render_template('admin/operation_log_list.html')

@admin.route("/admin_loginlog/list/")
def admin_loginlog_list():
    return render_template('admin/admin_loginlog_list.html')

@admin.route("/user_loginlog/list/")
def user_loginlog_list():
    return render_template('admin/user_loginlog_list.html')

@admin.route("/role/add/")
def role_add():
    return render_template('admin/role_add.html')

@admin.route("/role/list/")
def role_list():
    return render_template('admin/role_list.html')

@admin.route("/auth/add/")
def auth_add():
    return render_template('admin/auth_add.html')

@admin.route("/auth/list/")
def auth_list():
    return render_template('admin/auth_list.html')

@admin.route("/admin/add/")
def admin_add():
    return render_template('admin/admin_add.html')

@admin.route("/admin/list/")
def admin_list():
    return render_template('admin/admin_list.html')