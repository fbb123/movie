from datetime import datetime

from flask import Flask

from app import db




#会员
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer,primary_key=True) #编号
    name = db.Column(db.String(100),unique=True) #昵称
    pwd = db.Column(db.String(100)) #密码
    email = db.Column(db.String(100),unique=True) #邮箱
    phone = db.Column(db.String(11),unique=True) #电话
    info = db.Column(db.Text) #个性简介
    face = db.Column(db.String(255),unique=True) #头像
    add_time = db.Column(db.DateTime,index=True,default=datetime.now) #注册时间
    uuid = db.Column(db.String(255),unique=True) #唯一标识符
    user_logs = db.relationship("Userlog",backref="user") #外键关联会员日志
    comments = db.relationship("Comment",backref="user")
    movie_cols = db.relationship("MovieCol",backref="user")



    def __repr__(self):
        return "<User %r>" % self.name

    def check_pwd(self,pwd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd,pwd)

#会员登录日志
class Userlog(db.Model):
    __tablename__ = "userlog"
    id = db.Column(db.Integer,primary_key=True) #编号
    user_id = db.Column(db.Integer,db.ForeignKey("user.id")) #所属会员
    ip = db.Column(db.String(100)) #登录ip
    add_time = db.Column(db.DateTime,index=True,default=datetime.now) #登录时间

    def __repr__(self):
        return "<Userlog %r>" % self.id

 #标签
class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer,primary_key=True)#编号
    name = db.Column(db.String(100),unique=True) #标签名
    movies = db.relationship("Movie",backref="tag")
    add_time = db.Column(db.DateTime,index=True,default=datetime.now)#添加时间

    def __repr__(self):
        return "<Tag %r>" % self.name

#电影
class Movie(db.Model):
    __tablename__ = "movie"
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255),unique=True)
    url = db.Column(db.String(255),unique=True)
    info = db.Column(db.Text) #简介
    logo = db.Column(db.String(255),unique=True)#封面
    star = db.Column(db.SmallInteger)#星级
    play_num = db.Column(db.BigInteger)
    comment_num = db.Column(db.BigInteger)
    tag_id = db.Column(db.Integer,db.ForeignKey("tag.id"))
    area = db.Column(db.String(255)) #地区
    release_time = db.Column(db.Date)#上映时间
    length = db.Column(db.String(100)) #时长
    comments = db.relationship("Comment",backref="movie")
    movie_cols = db.relationship("MovieCol",backref="movie")

    add_time = db.Column(db.DateTime,index=True,default=datetime.now)

    def __repr__(self):
        return "<Movie %r>" % self.title

#预告
class Preview(db.Model):
    __tablename__ = "preview"
    id = db.Column(db.Integer,primary_key=True) #编号
    title = db.Column(db.String(255),unique=True) #标题
    logo = db.Column(db.String(255),unique=True) #封面
    add_time = db.Column(db.DateTime,index=True,default=datetime.now)

    def __repr__(self):
        return "<Preview %r>" % self.title

#评论
class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer,primary_key=True)
    content = db.Column(db.Text)
    movie_id = db.Column(db.Integer,db.ForeignKey("movie.id"))
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"))
    add_time = db.Column(db.DateTime,index=True,default=datetime.now)

    def __repr__(self):
        return "<Comment %r>" % self.id

#收藏
class MovieCol(db.Model):
    __tablename__ = "movie_col"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movie.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<MovieCol %r>" % self.id

#权限
class Auth(db.Model):
    __tablename__ = "auth"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),unique=True)
    url = db.Column(db.String(255),unique=True)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<Auth %r>" % self.name


# 角色
class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    auths = db.Column(db.String(600))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<Role %r>" % self.name

#管理员
class Admin(db.Model):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 昵称
    pwd = db.Column(db.String(100))  # 密码
    is_super = db.Column(db.SmallInteger)#0为超级管理员
    role_id = db.Column(db.Integer,db.ForeignKey("role.id"))
    admin_logs = db.relationship("AdminLog",backref="admin")
    operation_logs = db.relationship("OperationLog",backref="admin")
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<Admin %r>" % self.name

    def check_pwd(self,pwd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd,pwd)

#管理员登录日志
class AdminLog(db.Model):
    __tablename__ = "admin_log"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    admin_id = db.Column(db.Integer,db.ForeignKey("admin.id"))
    ip = db.Column(db.String(100))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<AdminLog %r>" % self.id

#管理员操作日志
class OperationLog(db.Model):
    __tablename__ = "Operation_log"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"))
    ip = db.Column(db.String(100))
    reason = db.Column(db.String(600))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<OperationLog %r>" % self.id


# if __name__ == "__main__":
    # db.create_all()
    # role = Role(
    #     name = "超级管理员",
    #     auths = ""
    # )
    # db.session.add(role)
    # db.session.commit()
    # from werkzeug.security import generate_password_hash
    # admin = Admin(
    #     name = "admin",
    #     pwd = generate_password_hash("admin123"),
    #     is_super = 0,
    #     role_id = 1
    # )
    # db.session.add(admin)
    # db.session.commit()
