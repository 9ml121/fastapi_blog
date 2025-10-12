"""
User 模型测试

测试 User 模型的字段定义、约束、方法等功能
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.user import User, UserRole


class TestUserModel:
    """User 模型测试类"""

    @pytest.fixture(scope="class")
    def engine(self):
        """创建测试数据库引擎"""
        # 使用内存数据库进行测试
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)

        yield engine

        # 清理资源
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    @pytest.fixture
    def session(self, engine):
        """创建测试数据库会话"""
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据 - 每次生成唯一数据"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "password_hash": "hashed_password_123",
            "nickname": f"测试用户_{unique_id}",
        }

    def test_user_creation(self, session, sample_user_data):
        """测试用户创建"""
        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 验证基本字段
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.nickname == sample_user_data["nickname"]
        assert user.password_hash == "hashed_password_123"

        # 验证默认值
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.avatar is None
        assert user.last_login is None

        # 验证时间戳
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_role_enum(self, session, sample_user_data):
        """测试用户角色枚举"""
        # 创建普通用户
        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        assert user.role == UserRole.USER
        assert user.is_regular_user is True
        assert user.is_admin is False

        # 提升为管理员
        user.promote_to_admin()
        assert user.role == UserRole.ADMIN
        assert user.is_admin is True
        assert user.is_regular_user is False

        # 降级为普通用户
        user.demote_to_user()
        assert user.role == UserRole.USER

    def test_username_unique_constraint(self, session, sample_user_data):
        """测试用户名唯一约束"""
        # 创建第一个用户
        user1 = User(**sample_user_data)
        session.add(user1)
        session.commit()

        # 尝试创建相同用户名的用户
        user_data_2 = sample_user_data.copy()
        user_data_2["email"] = "different@example.com"
        user2 = User(**user_data_2)
        session.add(user2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_email_unique_constraint(self, session, sample_user_data):
        """测试邮箱唯一约束"""
        # 创建第一个用户
        user1 = User(**sample_user_data)
        session.add(user1)
        session.commit()

        # 尝试创建相同邮箱的用户
        user_data_2 = sample_user_data.copy()
        user_data_2["username"] = "different_user"
        user2 = User(**user_data_2)
        session.add(user2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_user_methods(self, session, sample_user_data):
        """测试用户方法"""
        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 测试激活/停用
        assert user.is_active is True
        user.deactivate()
        assert user.is_active is False
        user.activate()
        assert user.is_active is True

        # 测试邮箱验证
        assert user.is_verified is False
        user.verify_email()
        assert user.is_verified is True

    def test_user_string_representations(self, session, sample_user_data):
        """测试用户字符串表示"""
        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 测试 __str__ 方法
        str_repr = str(user)
        assert sample_user_data["nickname"] in str_repr
        assert f"@{sample_user_data['username']}" in str_repr

        # 测试 __repr__ 方法
        repr_str = repr(user)
        assert "User(" in repr_str
        assert f"username='{sample_user_data['username']}'" in repr_str
        assert "role='UserRole.USER'" in repr_str or "role='user'" in repr_str

    def test_admin_user_creation(self, session, sample_user_data):
        """测试管理员用户创建"""
        sample_user_data["role"] = UserRole.ADMIN
        admin_user = User(**sample_user_data)
        session.add(admin_user)
        session.commit()

        assert admin_user.role == UserRole.ADMIN
        assert admin_user.is_admin is True
        assert admin_user.is_regular_user is False

    def test_deleted_at_default_value(self, session, sample_user_data):
        """测试 deleted_at 字段默认值"""
        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 新创建的用户 deleted_at 应该为 None
        assert user.deleted_at is None

    def test_soft_delete_with_deleted_at(self, session, sample_user_data):
        """测试使用 deleted_at 实现软删除"""
        from datetime import datetime

        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 模拟软删除：设置 deleted_at
        deletion_time = datetime.now()
        user.deleted_at = deletion_time
        session.commit()

        # 验证软删除时间已记录
        assert user.deleted_at is not None
        assert user.deleted_at == deletion_time

    def test_deleted_at_vs_is_active_semantics(self, session, sample_user_data):
        """测试 deleted_at 和 is_active 的语义区分"""
        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 场景1：管理员禁用用户（is_active=False，deleted_at=None）
        user.deactivate()
        assert user.is_active is False
        assert user.deleted_at is None  # 未删除，只是禁用

        # 场景2：用户删除账号（deleted_at 有值）
        from datetime import datetime

        user.deleted_at = datetime.now()
        assert user.deleted_at is not None
        # is_active 可以是 True 或 False，由业务决定

    def test_account_recovery_from_soft_delete(self, session, sample_user_data):
        """测试从软删除恢复账号"""
        from datetime import datetime

        user = User(**sample_user_data)
        session.add(user)
        session.commit()

        # 软删除
        user.deleted_at = datetime.now()
        session.commit()
        assert user.deleted_at is not None

        # 恢复账号：重置 deleted_at 为 None
        user.deleted_at = None
        session.commit()
        assert user.deleted_at is None


if __name__ == "__main__":
    # 简单的手动测试运行器
    import sys
    import traceback

    print("🧪 运行 User 模型测试...")

    # 这里我们需要手动设置一些测试
    try:
        # 基础的模型创建测试
        from app.models.user import User, UserRole

        # 测试枚举
        assert UserRole.USER == "user"
        assert UserRole.ADMIN == "admin"
        print("✅ 枚举类型测试通过")

        # 测试模型创建（不涉及数据库）
        user = User(
            username="test",
            email="test@example.com",
            password_hash="hash",
            nickname="测试",
        )

        assert user.username == "test"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        print("✅ 模型实例化测试通过")

        # 测试方法
        user.promote_to_admin()
        assert user.is_admin is True
        user.demote_to_user()
        assert user.is_regular_user is True
        print("✅ 模型方法测试通过")

        print("\n🎉 User 模型基础测试全部通过！")
        print("💡 要运行完整的数据库测试，请使用: pytest tests/test_models_user.py")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
        sys.exit(1)
