# app.py
import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Activity, Registration, Evaluation
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, os.getenv("DATABASE_FILE", "drl.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# flask-login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# make now() available in templates
app.jinja_env.globals['now'] = lambda: datetime.now()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------ Routes ------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Đăng nhập thành công", "success")
            return redirect(url_for("index"))
        flash("Tên đăng nhập hoặc mật khẩu không đúng", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Đã đăng xuất", "info")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    activities = Activity.query.order_by(Activity.date.desc()).all()
    return render_template("index.html", activities=activities)

@app.route("/activity/<int:aid>", methods=["GET","POST"])
@login_required
def activity_detail(aid):
    act = Activity.query.get_or_404(aid)
    message = None
    if request.method == "POST":
        if current_user.role != "student":
            flash("Chỉ sinh viên mới được đăng ký.", "warning")
            return redirect(url_for("activity_detail", aid=aid))
        existing = Registration.query.filter_by(user_id=current_user.id, activity_id=aid).first()
        if existing and not existing.cancelled:
            message = "Bạn đã đăng ký hoạt động này."
        else:
            if existing and existing.cancelled:
                existing.cancelled = False
                existing.registered_at = datetime.utcnow()
            else:
                reg = Registration(user_id=current_user.id, activity_id=aid)
                db.session.add(reg)
            db.session.commit()
            message = "Đăng ký thành công!"
    user_reg = None
    if current_user.role == "student":
        user_reg = Registration.query.filter_by(user_id=current_user.id, activity_id=aid, cancelled=False).first()
    regs = []
    if current_user.role in ("teacher","admin"):
        regs = Registration.query.filter_by(activity_id=aid, cancelled=False).join(User).all()
    return render_template("activity.html", activity=act, message=message, user_reg=user_reg, regs=regs)

@app.route("/activity/<int:aid>/cancel", methods=["POST"])
@login_required
def activity_cancel(aid):
    if current_user.role != "student":
        abort(403)
    reg = Registration.query.filter_by(user_id=current_user.id, activity_id=aid, cancelled=False).first()
    if reg:
        reg.cancelled = True
        db.session.commit()
        flash("Bạn đã hủy đăng ký.", "info")
    return redirect(url_for("activity_detail", aid=aid))

# Admin routes
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        abort(403)
    activities = Activity.query.order_by(Activity.created_at.desc()).all()
    return render_template("admin_dashboard.html", activities=activities)

@app.route("/admin/activity/new", methods=["GET","POST"])
@login_required
def admin_activity_new():
    if current_user.role != "admin":
        abort(403)
    if request.method == "POST":
        name = request.form.get("name","").strip()
        date = request.form.get("date","")
        max_score = int(request.form.get("max_score") or 10)
        desc = request.form.get("description","")
        a = Activity(name=name, date=date, max_score=max_score, description=desc)
        db.session.add(a); db.session.commit()
        flash("Thêm hoạt động thành công", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("activity_form.html", activity=None)

@app.route("/admin/activity/edit/<int:aid>", methods=["GET","POST"])
@login_required
def admin_activity_edit(aid):
    if current_user.role != "admin":
        abort(403)
    act = Activity.query.get_or_404(aid)
    if request.method == "POST":
        act.name = request.form.get("name") or act.name
        act.date = request.form.get("date") or act.date
        act.max_score = int(request.form.get("max_score") or act.max_score)
        act.description = request.form.get("description") or act.description
        db.session.commit()
        flash("Cập nhật hoạt động", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("activity_form.html", activity=act)

@app.route("/admin/activity/delete/<int:aid>", methods=["POST"])
@login_required
def admin_activity_delete(aid):
    if current_user.role != "admin":
        abort(403)
    act = Activity.query.get_or_404(aid)
    db.session.delete(act); db.session.commit()
    flash("Xóa hoạt động thành công", "success")
    return redirect(url_for("admin_dashboard"))

# Users management
@app.route("/admin/users", methods=["GET","POST"])
@login_required
def admin_users():
    if current_user.role != "admin":
        abort(403)
    if request.method == "POST":
        username = request.form.get("username","").strip()
        fullname = request.form.get("fullname","").strip()
        role = request.form.get("role")
        pwd = request.form.get("password") or "123456"
        student_id = request.form.get("student_id") or None
        class_name = request.form.get("class_name") or None
        if User.query.filter_by(username=username).first():
            flash("Tên đăng nhập đã tồn tại", "warning")
        else:
            u = User(username=username, fullname=fullname, role=role, student_id=student_id, class_name=class_name)
            u.set_password(pwd)
            db.session.add(u); db.session.commit()
            flash(f"Tạo tài khoản {username} thành công (pwd: {pwd})", "success")
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users_manage.html", users=users)

@app.route("/admin/users/edit/<int:user_id>", methods=["GET","POST"])
@login_required
def edit_user(user_id):
    if current_user.role != "admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.username = request.form.get("username") or user.username
        user.fullname = request.form.get("fullname") or user.fullname
        user.role = request.form.get("role") or user.role
        user.student_id = request.form.get("student_id") or user.student_id
        user.class_name = request.form.get("class_name") or user.class_name
        newpwd = request.form.get("password")
        if newpwd:
            user.set_password(newpwd)
        db.session.commit()
        flash("Cập nhật tài khoản", "success")
        return redirect(url_for("admin_users"))
    return render_template("edit_user.html", user=user)

@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user); db.session.commit()
    flash("Đã xóa tài khoản", "info")
    return redirect(url_for("admin_users"))

# Teacher routes
@app.route("/teacher")
@login_required
def teacher_panel():
    if current_user.role != "teacher":
        abort(403)
    activities = Activity.query.order_by(Activity.date.desc()).all()
    return render_template("teacher_panel.html", activities=activities)

@app.route("/teacher/activity/<int:aid>", methods=["GET"])
@login_required
def teacher_activity(aid):
    if current_user.role != "teacher":
        abort(403)
    act = Activity.query.get_or_404(aid)
    regs = Registration.query.filter_by(activity_id=aid, cancelled=False).join(User).all()
    students = []
    for r in regs:
        ev = Evaluation.query.filter_by(registration_id=r.id).first()
        students.append({"reg": r, "student": r.user, "rating": ev.percent if ev else 0, "evaluation": ev})
    return render_template("teacher_panel.html", activity=act, students=students, activities=[act])

@app.route("/teacher/rate/<int:reg_id>", methods=["POST"])
@login_required
def teacher_rate(reg_id):
    if current_user.role != "teacher":
        abort(403)
    level = request.form.get("level")  # 'none','attend','active'
    note = request.form.get("note","")
    mapping = {"none":0.0,"attend":80.0,"active":100.0}
    percent = mapping.get(level, 0.0)
    reg = Registration.query.get_or_404(reg_id)
    ev = Evaluation.query.filter_by(registration_id=reg.id).first()
    if ev:
        ev.level = level; ev.percent = percent; ev.note = note; ev.teacher_id = current_user.id; ev.evaluated_at = datetime.utcnow()
    else:
        ev = Evaluation(registration_id=reg.id, teacher_id=current_user.id, level=level, percent=percent, note=note)
        db.session.add(ev)
    db.session.commit()
    flash("Đã lưu đánh giá", "success")
    return redirect(url_for("teacher_activity", aid=reg.activity_id))

# Reports
@app.route("/admin/report")
@login_required
def admin_report():
    if current_user.role != "admin":
        abort(403)
    sel_class = request.args.get("class")
    sel_student = request.args.get("student_id")
    classes = db.session.query(User.class_name).filter(User.role=="student").distinct().all()
    classes = [c[0] for c in classes if c[0]]
    students = []
    if sel_class:
        students = User.query.filter_by(role="student", class_name=sel_class).all()
    elif sel_student:
        students = User.query.filter_by(role="student", student_id=sel_student).all()
    else:
        students = []
    results = []
    for s in students:
        total = 0.0
        details = []
        for r in s.registrations:
            if r.cancelled:
                continue
            act = r.activity
            ev = Evaluation.query.filter_by(registration_id=r.id).first()
            percent = ev.percent if ev else 0.0
            point = act.max_score * percent / 100.0
            total += point
            details.append({"activity": act.name, "max": act.max_score, "percent": percent, "point": point})
        results.append({"student": s, "total": total, "details": details})
    return render_template("report.html", classes=classes, selected_class=sel_class, students=results)

# ------------- Run -------------
if __name__ == "__main__":
    # ensure DB created (if user prefers manual init, you can remove this)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
