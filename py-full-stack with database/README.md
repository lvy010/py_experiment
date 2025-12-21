# 毕业论文选题系统（Flask + SQLite）

## 功能
- 学生：登录记忆学号，按教师/类别/难度筛选，提交 3 个内志愿；查看分配与通知（被取消志愿会提醒）。
- 教师：登录记忆工号，发布/改/删课题；查看志愿并确认分配，超额与已分配自动阻止，确认后自动取消其他学生志愿并发通知。
- 教研室：按名称快速登录；审核课题（通过/驳回）；查看教师/学生统计、完成率、分配映射；无一键自动分配。

## 快速开始
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python - <<'PY'
from app import init_db
init_db()
PY
flask --app app run --debug 
```
访问 http://127.0.0.1:5000/

## 示例
- 教师：T001 张老师（max 3），T002 李老师（max 2）
- 学生：S001/S002/S003
- 课题：P001 “基于 Flask 的选题系统设计与实现”，P002 “机器学习在文本分类中的应用”
默认课题状态“待审核”，教研室通过后“未分配”，教师确认后“已分配”。

## 约束
- 志愿唯一：同一学生同一课题或同一序号不可重复；最多 3 个志愿。
- 分配唯一：课题只分给一名学生；教师受 `max_projects` 限制。
- 通知：分配后自动取消其他学生该课题志愿并生成通知。

## 重置/测试数据
- 重置：删除 `thesis_selection.db` 后再次运行 `init_db()` 或执行 `schema.sql`。
- 额外测试：`python load_test_data.py`

## 部署提示
- 更换 `secret_key`，生产关闭 `debug`。
- SQLite 适合单机，生产可换 MySQL/PostgreSQL 并调整连接。

