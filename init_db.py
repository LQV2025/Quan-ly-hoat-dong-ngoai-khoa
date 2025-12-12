# init_db.py
from app import app
from models import db, User, Activity
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", fullname="Quản trị", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
    if not User.query.filter_by(username="teacher1").first():
        t = User(username="teacher1", fullname="Giáo viên 1", role="teacher")
        t.set_password("teach123")
        db.session.add(t)
    if not User.query.filter_by(username="sv01").first():
        s = User(username="sv01", fullname="Nguyễn Văn A", role="student", student_id="SV001", class_name="CNTT1")
        s.set_password("sv123")
        db.session.add(s)
    if not Activity.query.first():
        a1 = Activity(name="Tình nguyện dọn rác", description="Hoạt động dọn rác khuôn viên", date="2025-10-20", max_score=10)
        a2 = Activity(name="Workshop kỹ năng", description="Kỹ năng mềm cho SV", date="2025-11-05", max_score=8)
        db.session.add_all([a1,a2])
    db.session.commit()
    print("DB initialized. Accounts: admin/admin123, teacher1/teach123, sv01/sv123")
