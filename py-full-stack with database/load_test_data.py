import os
import sqlite3


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "thesis_selection.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        # 1）先确保表结构存在：执行 schema.sql（重复执行是安全的）
        schema_path = os.path.join(BASE_DIR, "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)

        # 2）再导入测试数据：执行 test_data.sql
        test_data_path = os.path.join(BASE_DIR, "test_data.sql")
        with open(test_data_path, "r", encoding="utf-8") as f:
            test_sql = f.read()
        conn.executescript(test_sql)

        conn.commit()
        print("表结构已创建/更新，测试数据已导入完成。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()



