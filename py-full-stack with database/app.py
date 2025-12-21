import os
import sqlite3
import uuid
from datetime import datetime

from flask import Flask, g, redirect, render_template, request, url_for, flash, session


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "thesis_selection.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = get_db()
    with open(os.path.join(BASE_DIR, "schema.sql"), "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


def ensure_db():
    # 如果数据库文件不存在，则初始化
    if not os.path.exists(DB_PATH):
        init_db()
    # 保证通知表存在（用于向学生发送被取消志愿的提醒）
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notification (
            notif_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            message TEXT NOT NULL,
            created_time TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES student(student_id)
        )
        """
    )
    db.commit()


app = Flask(__name__)
app.secret_key = "dev-secret-key"  # 实验课程可使用简单明文


@app.before_request
def before_request():
    ensure_db()


@app.teardown_appcontext
def close_connection(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    return render_template("index.html")


# ===================== 学生端 =====================

@app.route("/student", methods=["GET", "POST"])
def student_portal():
    db = get_db()
    # 学生登录状态保存在 session 中，避免每次操作都重新输入编号
    student_id = None
    teacher_name = ""
    category = ""
    difficulty = ""

    if request.method == "POST":
        # 如果表单里带了 student_id，说明是登录/查询动作，更新 session
        form_sid = request.form.get("student_id", "").strip()
        if form_sid:
            session["student_id"] = form_sid
        student_id = session.get("student_id", "").strip()

        # 查询课题筛选条件
        teacher_name = request.form.get("teacher_name", "").strip()
        category = request.form.get("category", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
    else:
        # GET 请求时直接从 session 读取当前登录学生
        student_id = session.get("student_id", "").strip()

    if not student_id:
        return render_template("student_login.html")

    stu = db.execute(
        "SELECT * FROM student WHERE student_id=?", (student_id,)
    ).fetchone()
    if not stu:
        # 学号无效时清理 session 并回到登录页
        session.pop("student_id", None)
        flash("学生编号不存在", "error")
        return render_template("student_login.html")

    query = """
    SELECT p.*, t.teacher_name
    FROM project p
    JOIN teacher t ON p.teacher_id = t.teacher_id
    WHERE p.status IN ('已审核','未分配')
    """
    params = []
    if teacher_name:
        query += " AND t.teacher_name LIKE ?"
        params.append(f"%{teacher_name}%")
    if category:
        query += " AND p.category LIKE ?"
        params.append(f"%{category}%")
    if difficulty:
        query += " AND p.difficulty = ?"
        params.append(difficulty)

    projects = db.execute(query, params).fetchall()

    # 当前学生志愿情况
    volunteers = db.execute(
        """
        SELECT v.*, p.project_name, p.category, p.difficulty, t.teacher_name
        FROM volunteer v
        JOIN project p ON v.project_id = p.project_id
        JOIN teacher t ON p.teacher_id = t.teacher_id
        WHERE v.student_id=?
        ORDER BY v.sequence
        """,
        (student_id,),
    ).fetchall()

    # 分配结果
    allocation = db.execute(
        """
        SELECT a.*, p.project_name, t.teacher_name, t.phone AS teacher_phone
        FROM allocation a
        JOIN project p ON a.project_id = p.project_id
        JOIN teacher t ON p.teacher_id = t.teacher_id
        WHERE a.student_id=?
        """,
        (student_id,),
    ).fetchone()

    # 读取学生通知（最新在前）
    notifications = db.execute(
        "SELECT notif_id, message, created_time, is_read FROM notification WHERE student_id=? ORDER BY created_time DESC",
        (student_id,),
    ).fetchall()

    # 标记为已读
    db.execute("UPDATE notification SET is_read=1 WHERE student_id=? AND is_read=0", (student_id,))
    db.commit()

    return render_template(
        "student.html",
        student=stu,
        projects=projects,
        volunteers=volunteers,
        allocation=allocation,
        notifications=notifications,
    )


@app.route("/student/submit_volunteer", methods=["POST"])
def submit_volunteer():
    db = get_db()
    student_id = session.get("student_id", "").strip() or request.form.get(
        "student_id", ""
    ).strip()
    if not student_id:
        flash("学生编号缺失", "error")
        return redirect(url_for("student_portal"))

    # 读取最多 3 个志愿
    selected = []
    for seq in (1, 2, 3):
        pid = request.form.get(f"project_{seq}", "").strip()
        if pid:
            selected.append((seq, pid))

    if not selected:
        flash("请至少选择一个课题作为志愿", "error")
        return redirect(url_for("student_portal"))

    # 不能出现重复课题
    project_ids = [p for _, p in selected]
    if len(project_ids) != len(set(project_ids)):
        flash("同一课题不能在多个志愿顺序中重复出现", "error")
        return redirect(url_for("student_portal"))

    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    try:
        # 先删除该学生的原有志愿
        # 在插入前确认所选课题均未被已分配（加锁）
        for _, pid in selected:
            p = db.execute("SELECT status FROM project WHERE project_id=?", (pid,)).fetchone()
            if p and p["status"] == "已分配":
                flash(f'课题 {pid} 已被分配，不能作为志愿提交', 'error')
                return redirect(url_for("student_portal"))

        db.execute("DELETE FROM volunteer WHERE student_id=?", (student_id,))
        # 重新插入
        for seq, pid in selected:
            db.execute(
                """
                INSERT INTO volunteer (volunteer_id, student_id, project_id, sequence, submit_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), student_id, pid, seq, now),
            )
        db.commit()
        flash("志愿提交成功", "success")
    except sqlite3.IntegrityError as e:
        db.rollback()
        flash(f"提交失败，违反唯一性约束：{e}", "error")

    return redirect(url_for("student_portal"))


# ===================== 教师端 =====================

@app.route("/teacher", methods=["GET", "POST"])
def teacher_portal():
    db = get_db()
    teacher_id = None

    if request.method == "POST":
        form_tid = request.form.get("teacher_id", "").strip()
        if form_tid:
            session["teacher_id"] = form_tid
        teacher_id = session.get("teacher_id", "").strip()
    else:
        teacher_id = session.get("teacher_id", "").strip()

    if not teacher_id:
        return render_template("teacher_login.html")

    teacher = db.execute(
        "SELECT * FROM teacher WHERE teacher_id=?", (teacher_id,)
    ).fetchone()
    if not teacher:
        session.pop("teacher_id", None)
        flash("教师编号不存在", "error")
        return render_template("teacher_login.html")

    # 自己发布的课题
    projects = db.execute(
        "SELECT * FROM project WHERE teacher_id=? ORDER BY project_id",
        (teacher_id,),
    ).fetchall()

    # 当前已分配/可用名额（通过 allocation + teacher.max_projects 估算）
    used_slots = db.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM allocation a
        JOIN project p ON a.project_id = p.project_id
        WHERE p.teacher_id=?
        """,
        (teacher_id,),
    ).fetchone()["cnt"]
    remaining = teacher["max_projects"] - used_slots

    # 与该教师课题相关的志愿
    volunteers = db.execute(
        """
        SELECT v.*, s.student_name, s.class, s.major, s.comprehensive_score, p.project_name
        FROM volunteer v
        JOIN project p ON v.project_id = p.project_id
        JOIN student s ON v.student_id = s.student_id
        WHERE p.teacher_id=?
        ORDER BY p.project_id, v.sequence, s.comprehensive_score DESC
        """,
        (teacher_id,),
    ).fetchall()

    # 当前教师已有被分配的课题（用于前端禁用已分配课题的确认按钮）
    allocated_rows = db.execute(
        "SELECT a.project_id FROM allocation a JOIN project p ON a.project_id=p.project_id WHERE p.teacher_id=?",
        (teacher_id,),
    ).fetchall()
    allocated_projects = [r["project_id"] for r in allocated_rows]

    return render_template(
        "teacher.html",
        teacher=teacher,
        projects=projects,
        volunteers=volunteers,
        remaining=remaining,
        allocated_projects=allocated_projects,
    )


@app.route("/teacher/select_student", methods=["POST"])
def teacher_select_student():
    db = get_db()
    teacher_id = session.get("teacher_id", "").strip() or request.form.get("teacher_id", "").strip()
    project_id = request.form.get("project_id", "").strip()
    student_id = request.form.get("student_id", "").strip()

    if not (teacher_id and project_id and student_id):
        flash("参数缺失", "error")
        return redirect(url_for("teacher_portal"))

    # 验证课题归属
    proj = db.execute("SELECT * FROM project WHERE project_id=? AND teacher_id=?", (project_id, teacher_id)).fetchone()
    if not proj:
        flash("课题不存在或不属于当前教师", "error")
        return redirect(url_for("teacher_portal"))

    # 如果已被分配，拒绝
    exists = db.execute("SELECT COUNT(*) AS c FROM allocation WHERE project_id=?", (project_id,)).fetchone()["c"]
    if exists > 0 or proj["status"] == "已分配":
        flash("该课题已被分配，无法再确认其他学生", "error")
        return redirect(url_for("teacher_portal"))

    # 检查教师名额
    used = db.execute(
        "SELECT COUNT(*) AS c FROM allocation a JOIN project p ON a.project_id=p.project_id WHERE p.teacher_id=?",
        (teacher_id,),
    ).fetchone()["c"]
    teacher = db.execute("SELECT max_projects, teacher_name FROM teacher WHERE teacher_id=?", (teacher_id,)).fetchone()
    maxp = teacher["max_projects"] if teacher else 9999
    if used >= maxp:
        flash("教师已超出可带课题限额，无法再分配", "error")
        return redirect(url_for("teacher_portal"))

    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    try:
        db.execute(
            "INSERT INTO allocation (allocation_id, student_id, project_id, status, allocation_time, coordinator) VALUES (?, ?, ?, '已确认', ?, ?)",
            (str(uuid.uuid4()), student_id, project_id, now, teacher["teacher_name"] if teacher else "教师"),
        )
        # 查出将被取消志愿的学生 id（不包含被确认的 student_id）
        rows = db.execute("SELECT student_id FROM volunteer WHERE project_id=? AND student_id<>?", (project_id, student_id)).fetchall()
        affected_ids = [r["student_id"] for r in rows]

        # 删除他们对该课题的志愿
        db.execute("DELETE FROM volunteer WHERE project_id=? AND student_id<>?", (project_id, student_id))

        # 为每个被取消的学生插入通知
        for sid in affected_ids:
            msg = f'您申请的课题 {project_id} 已被教师确认分配给其他学生，您的该项志愿已被取消。'
            db.execute(
                "INSERT INTO notification (notif_id, student_id, message, created_time, is_read) VALUES (?, ?, ?, ?, 0)",
                (str(uuid.uuid4()), sid, msg, now),
            )

        db.execute("UPDATE project SET status='已分配' WHERE project_id=?", (project_id,))
        db.commit()

        msg = "已成功确认学生并分配课题"
        if affected_ids:
            msg += f"；已自动取消 {len(affected_ids)} 位其他学生对此课题的志愿"
        flash(msg, "success")
    except sqlite3.IntegrityError as e:
        db.rollback()
        flash(f"分配失败：{e}", "error")

    return redirect(url_for("teacher_portal"))


@app.route("/teacher/project/create", methods=["POST"])
def create_project():
    db = get_db()
    teacher_id = request.form.get("teacher_id", "").strip()
    if not teacher_id:
        flash("教师编号缺失", "error")
        return redirect(url_for("teacher_portal"))

    name = request.form.get("project_name", "").strip()
    category = request.form.get("category", "").strip()
    requirements = request.form.get("requirements", "").strip()
    difficulty = request.form.get("difficulty", "").strip()
    if not (name and category and difficulty):
        flash("课题名称、类别和难度为必填项", "error")
        return redirect(url_for("teacher_portal"))

    pid = "P" + uuid.uuid4().hex[:7].upper()
    db.execute(
        """
        INSERT INTO project (project_id, project_name, category, requirements, difficulty, teacher_id, status)
        VALUES (?, ?, ?, ?, ?, ?, '待审核')
        """,
        (pid, name, category, requirements, difficulty, teacher_id),
    )
    db.commit()
    flash("课题发布成功，等待教研室审核", "success")
    return redirect(url_for("teacher_portal"))


@app.route("/teacher/project/delete", methods=["POST"])
def delete_project():
    db = get_db()
    teacher_id = session.get("teacher_id", "").strip() or request.form.get(
        "teacher_id", ""
    ).strip()
    project_id = request.form.get("project_id", "").strip()
    # 仅能删除未被志愿和未被分配的课题
    count_v = db.execute(
        "SELECT COUNT(*) AS c FROM volunteer WHERE project_id=?", (project_id,)
    ).fetchone()["c"]
    count_a = db.execute(
        "SELECT COUNT(*) AS c FROM allocation WHERE project_id=?", (project_id,)
    ).fetchone()["c"]
    if count_v > 0 or count_a > 0:
        flash("该课题已被学生选择或已分配，不能删除", "error")
    else:
        db.execute(
            "DELETE FROM project WHERE project_id=? AND teacher_id=?",
            (project_id, teacher_id),
        )
        db.commit()
        flash("课题已删除", "success")
    return redirect(url_for("teacher_portal"))


@app.route("/teacher/project/update", methods=["POST"])
def update_project():
    db = get_db()
    teacher_id = session.get("teacher_id", "").strip() or request.form.get(
        "teacher_id", ""
    ).strip()
    project_id = request.form.get("project_id", "").strip()
    name = request.form.get("project_name", "").strip()
    category = request.form.get("category", "").strip()
    requirements = request.form.get("requirements", "").strip()
    difficulty = request.form.get("difficulty", "").strip()

    db.execute(
        """
        UPDATE project
        SET project_name=?, category=?, requirements=?, difficulty=?
        WHERE project_id=? AND teacher_id=?
        """,
        (name, category, requirements, difficulty, project_id, teacher_id),
    )
    db.commit()
    flash("课题信息已更新", "success")
    return redirect(url_for("teacher_portal"))


# ===================== 教研室端 =====================

@app.route("/office", methods=["GET", "POST"])
def office_portal():
    db = get_db()
    office_name = None

    if request.method == "POST":
        form_office = request.form.get("office_name", "").strip()
        if form_office:
            session["office_name"] = form_office
        office_name = session.get("office_name", "").strip()
    else:
        office_name = session.get("office_name", "").strip()

    if not office_name:
        return render_template("office_login.html")

    # 为简单起见，只通过教研室名称“登录”，后续不再重复输入
    projects = db.execute(
        """
        SELECT p.*, t.teacher_name
        FROM project p
        JOIN teacher t ON p.teacher_id = t.teacher_id
        ORDER BY p.status, p.project_id
        """
    ).fetchall()

    # 统计数据
    teacher_stats = db.execute(
        """
        SELECT t.teacher_name,
               COUNT(DISTINCT p.project_id) AS project_count,
               COUNT(DISTINCT a.allocation_id) AS allocated_count
        FROM teacher t
        LEFT JOIN project p ON t.teacher_id = p.teacher_id
        LEFT JOIN allocation a ON p.project_id = a.project_id
        GROUP BY t.teacher_id
        """
    ).fetchall()

    student_stats = db.execute(
        """
        SELECT s.student_name,
               COUNT(DISTINCT v.volunteer_id) AS volunteer_count,
               CASE WHEN EXISTS (
                   SELECT 1 FROM allocation a WHERE a.student_id = s.student_id
               ) THEN 1 ELSE 0 END AS has_allocation
        FROM student s
        LEFT JOIN volunteer v ON s.student_id = v.student_id
        GROUP BY s.student_id
        """
    ).fetchall()

    total_students = db.execute("SELECT COUNT(*) AS c FROM student").fetchone()["c"]
    allocated_students = db.execute(
        "SELECT COUNT(DISTINCT student_id) AS c FROM allocation"
    ).fetchone()["c"]
    completion_rate = (
        f"{allocated_students / total_students * 100:.1f}%"
        if total_students
        else "0%"
    )

    # 当前分配映射（用于教研室查看学生-课题-教师对应关系）
    allocation_map = db.execute(
        """
        SELECT a.*, p.project_name, p.teacher_id, t.teacher_name, s.student_name
        FROM allocation a
        JOIN project p ON a.project_id = p.project_id
        JOIN teacher t ON p.teacher_id = t.teacher_id
        JOIN student s ON a.student_id = s.student_id
        ORDER BY a.allocation_time
        """,
    ).fetchall()

    return render_template(
        "office.html",
        office_name=office_name or "教研室",
        projects=projects,
        teacher_stats=teacher_stats,
        student_stats=student_stats,
        completion_rate=completion_rate,
        allocation_map=allocation_map,
    )


@app.route("/office/project/audit", methods=["POST"])
def audit_project():
    db = get_db()
    project_id = request.form.get("project_id", "").strip()
    action = request.form.get("action", "").strip()
    if action == "approve":
        status = "未分配"
    elif action == "reject":
        status = "已驳回"
    else:
        flash("未知操作", "error")
        return redirect(url_for("office_portal"))

    db.execute("UPDATE project SET status=? WHERE project_id=?", (status, project_id))
    db.commit()
    flash("课题审核状态已更新", "success")
    return redirect(url_for("office_portal"))


# 已移除自动分配逻辑：按用户要求删除一键自动分配模块，改为人工审核与教师确认分配。


# /office/auto_allocate 路由已移除（前端按钮也已禁用）


# ===================== 登出功能 =====================


@app.route("/student/logout")
def student_logout():
    session.pop("student_id", None)
    flash("已退出当前学生登录", "success")
    return redirect(url_for("student_portal"))


@app.route("/teacher/logout")
def teacher_logout():
    session.pop("teacher_id", None)
    flash("已退出当前教师登录", "success")
    return redirect(url_for("teacher_portal"))


@app.route("/office/logout")
def office_logout():
    session.pop("office_name", None)
    flash("已退出当前教研室登录", "success")
    return redirect(url_for("office_portal"))


if __name__ == "__main__":
    # 开发调试模式
    app.run(debug=True)


