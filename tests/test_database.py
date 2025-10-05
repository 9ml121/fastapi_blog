"""
数据库连接模块测试
测试 app/db/database.py 模块的功能
"""

from contextlib import suppress

from sqlalchemy import text

from app.db.database import SessionLocal, engine, get_db


class TestDatabaseConnection:
    """数据库连接测试类"""

    def test_engine_connection(self):
        """测试数据库引擎连接"""
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()
            assert version is not None
            assert "PostgreSQL" in version[0]

    def test_session_creation(self):
        """测试数据库会话创建"""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT current_database()"))
            db_name = result.fetchone()
            assert db_name is not None
            assert db_name[0] == "blogdb"
        finally:
            db.close()

    def test_get_db_dependency(self):
        """测试依赖注入函数"""
        db_generator = get_db()
        db = next(db_generator)
        try:
            # 验证会话可用
            result = db.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1
        finally:
            # 确保会话正确关闭
            with suppress(StopIteration):
                next(db_generator)

    def test_database_name(self):
        """测试连接到正确的数据库"""
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()
            assert db_name is not None
            assert db_name[0] == "blogdb"


if __name__ == "__main__":
    # 直接运行测试的简单方式
    import sys
    import traceback

    print("🧪 运行数据库连接测试...")

    test_class = TestDatabaseConnection()
    tests = [
        test_class.test_engine_connection,
        test_class.test_session_creation,
        test_class.test_get_db_dependency,
        test_class.test_database_name,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n📊 测试结果: {passed}个通过, {failed}个失败")

    if failed > 0:
        sys.exit(1)
