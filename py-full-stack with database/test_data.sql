-- 额外测试数据脚本（在 thesis_selection.db 初始化后导入）
-- 注意：schema.sql 中已插入 T001/T002、S001~S003、P001/P002

PRAGMA foreign_keys = ON;

-- 更多教师
INSERT INTO teacher (teacher_id, teacher_name, research_office, title, phone, max_projects) VALUES
('T003', '王老师', '软件工程教研室', '教授', '13800000003', 4),
('T004', '赵老师', '人工智能教研室', '副教授', '13800000004', 3)
ON CONFLICT DO NOTHING;

-- 更多学生
INSERT INTO student (student_id, student_name, class, major, comprehensive_score, phone) VALUES
('S004', '小张', '软工2101', '软件工程', 95.0, '13900000004'),
('S005', '小赵', '软工2102', '软件工程', 89.0, '13900000005'),
('S006', '小王', '计科2101', '计算机科学与技术', 91.5, '13900000006'),
('S007', '小孙', '计科2101', '计算机科学与技术', 83.0, '13900000007'),
('S008', '小周', '信安2101', '信息安全', 87.0, '13900000008'),
('S009', '小吴', '信安2102', '信息安全', 90.0, '13900000009'),
('S010', '小郑', '软工2103', '软件工程', 78.0, '13900000010')
ON CONFLICT DO NOTHING;

-- 更多课题
INSERT INTO project (project_id, project_name, category, requirements, difficulty, teacher_id, status) VALUES
('P003', '基于微服务的选题系统设计', '计算机应用', '了解微服务架构，完成系统拆分与接口设计。', '高', 'T003', '待审核'),
('P004', '毕业论文选题数据可视化分析', '计算机应用', '掌握数据可视化工具，对选题数据进行可视化展示。', '中', 'T003', '待审核'),
('P005', '深度学习在图像识别中的应用', '人工智能', '熟悉卷积神经网络，完成图像分类实验。', '高', 'T004', '待审核'),
('P006', '基于爬虫的毕业论文题目采集系统', '计算机应用', '掌握 Python 爬虫框架，能够采集并清洗网页数据。', '中', 'T002', '待审核'),
('P007', '校园选题系统安全性分析', '信息安全', '掌握基本安全攻防知识，对选题系统进行安全性评估。', '中', 'T001', '待审核'),
('P008', '智能推荐在选题系统中的应用', '人工智能', '了解推荐系统基础算法，尝试实现简单选题推荐。', '高', 'T004', '待审核')
ON CONFLICT DO NOTHING;

-- 模拟多学生选择同一课题的志愿（用于冲突测试）
-- 假设教研室已审核通过 P003, P004, P005, P006, P007, P008，并将状态修改为“未分配”后执行以下志愿插入

INSERT INTO volunteer (volunteer_id, student_id, project_id, sequence, submit_time) VALUES
-- 多人第一志愿选择 P003
(hex(randomblob(16)), 'S001', 'P003', 1, datetime('now', '-60 minutes')),
(hex(randomblob(16)), 'S002', 'P003', 1, datetime('now', '-50 minutes')),
(hex(randomblob(16)), 'S003', 'P003', 1, datetime('now', '-40 minutes')),
(hex(randomblob(16)), 'S004', 'P003', 1, datetime('now', '-30 minutes')),
-- 部分学生把 P004/P005 作为第二、三志愿
(hex(randomblob(16)), 'S005', 'P004', 1, datetime('now', '-20 minutes')),
(hex(randomblob(16)), 'S006', 'P005', 1, datetime('now', '-10 minutes')),
(hex(randomblob(16)), 'S007', 'P003', 2, datetime('now', '-5 minutes')),
(hex(randomblob(16)), 'S008', 'P004', 2, datetime('now', '-3 minutes')),
(hex(randomblob(16)), 'S009', 'P005', 2, datetime('now', '-2 minutes')),
(hex(randomblob(16)), 'S010', 'P006', 1, datetime('now', '-1 minutes'))
ON CONFLICT DO NOTHING;


