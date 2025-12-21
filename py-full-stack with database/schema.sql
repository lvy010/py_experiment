-- 数据库：毕业论文选题系统
-- 使用 SQLite 语法，字段设计尽量贴合作业要求

PRAGMA foreign_keys = ON;

-- 教师表
CREATE TABLE IF NOT EXISTS teacher (
    teacher_id      TEXT PRIMARY KEY,
    teacher_name    TEXT NOT NULL,
    research_office TEXT NOT NULL,
    title           TEXT NOT NULL,
    phone           TEXT,
    max_projects    INTEGER NOT NULL DEFAULT 5
);

-- 学生表
CREATE TABLE IF NOT EXISTS student (
    student_id          TEXT PRIMARY KEY,
    student_name        TEXT NOT NULL,
    class               TEXT NOT NULL,
    major               TEXT NOT NULL,
    comprehensive_score REAL DEFAULT 0.0,
    phone               TEXT
);

-- 教研室表
CREATE TABLE IF NOT EXISTS research_office (
    office_id      TEXT PRIMARY KEY,
    office_name    TEXT NOT NULL,
    college        TEXT NOT NULL,
    director       TEXT NOT NULL,
    director_phone TEXT
);

-- 课题表
CREATE TABLE IF NOT EXISTS project (
    project_id   TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    requirements TEXT,
    difficulty   TEXT NOT NULL, -- 低/中/高
    teacher_id   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT '待审核', -- 待审核/已审核/已分配/未分配/已驳回
    FOREIGN KEY (teacher_id) REFERENCES teacher(teacher_id)
);

-- 志愿表
CREATE TABLE IF NOT EXISTS volunteer (
    volunteer_id TEXT PRIMARY KEY,
    student_id   TEXT NOT NULL,
    project_id   TEXT NOT NULL,
    sequence     INTEGER NOT NULL, -- 1/2/3
    submit_time  TEXT NOT NULL,    -- ISO 字符串
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (project_id) REFERENCES project(project_id),
    UNIQUE (student_id, project_id),    -- 同一学生不能对同一课题提交多个志愿
    UNIQUE (student_id, sequence)       -- 同一学生同一志愿顺序只能选一个课题
);

-- 分配表
CREATE TABLE IF NOT EXISTS allocation (
    allocation_id   TEXT PRIMARY KEY,
    student_id      TEXT NOT NULL,
    project_id      TEXT NOT NULL UNIQUE, -- 同一课题只分配给一个学生
    status          TEXT NOT NULL DEFAULT '待确认', -- 待确认/已确认/已驳回
    allocation_time TEXT NOT NULL,
    coordinator     TEXT,
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (project_id) REFERENCES project(project_id)
);

-- 一些示例数据，方便本地测试
INSERT INTO teacher (teacher_id, teacher_name, research_office, title, phone, max_projects) VALUES
('T001', '张老师', '软件工程教研室', '副教授', '13800000001', 3),
('T002', '李老师', '人工智能教研室', '讲师', '13800000002', 2)
ON CONFLICT DO NOTHING;

INSERT INTO student (student_id, student_name, class, major, comprehensive_score, phone) VALUES
('S001', '小明', '软工2101', '软件工程', 88.5, '13900000001'),
('S002', '小红', '软工2102', '软件工程', 92.0, '13900000002'),
('S003', '小李', '信安2101', '信息安全', 85.0, '13900000003')
ON CONFLICT DO NOTHING;

INSERT INTO project (project_id, project_name, category, requirements, difficulty, teacher_id, status) VALUES
('P001', '基于 Flask 的选题系统设计与实现', '计算机应用', '熟悉 Python 与 Web 开发，完成系统设计与实现。', '中', 'T001', '待审核'),
('P002', '机器学习在文本分类中的应用', '人工智能', '掌握基本机器学习算法，能够实现文本分类实验。', '高', 'T002', '待审核')
ON CONFLICT DO NOTHING;


