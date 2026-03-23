"""
test_user_auth.py - UserAuth 模块测试套件
测试工程师: Leike 🔍
日期: 2026-03-22
任务: mission-1 - 找出所有 bug、安全隐患、设计缺陷并写出对应测试
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from user_auth import UserAuth


class TestUserAuthRegister(unittest.TestCase):
    """注册功能测试"""

    def setUp(self):
        self.auth = UserAuth()

    def test_register_normal(self):
        """正常注册：用户名和密码正确，应返回 True"""
        result = self.auth.register("alice", "P@ssw0rd")
        self.assertTrue(result)
        self.assertIn("alice", self.auth.users)

    def test_register_duplicate_username(self):
        """重复注册：相同用户名应返回 False"""
        self.auth.register("alice", "P@ssw0rd")
        result = self.auth.register("alice", "newpass")
        self.assertFalse(result)
        # 原密码不应被覆盖
        self.assertEqual(self.auth.users["alice"], "P@ssw0rd")

    def test_register_empty_username(self):
        """[BUG] 空用户名：系统允许注册空字符串用户名——无输入校验"""
        result = self.auth.register("", "password")
        self.assertTrue(result)  # 这是一个问题！空用户名不应该被允许
        self.assertIn("", self.auth.users)

    def test_register_empty_password(self):
        """[BUG] 空密码：系统允许注册空密码——无密码强度校验"""
        result = self.auth.register("alice", "")
        self.assertTrue(result)  # 这是一个问题！空密码不应该被允许
        self.assertEqual(self.auth.users["alice"], "")

    def test_register_none_username(self):
        """[BUG] None 用户名：系统允许 None 作为用户名"""
        result = self.auth.register(None, "password")
        self.assertTrue(result)  # 这是一个问题！
        self.assertIn(None, self.auth.users)

    def test_register_none_password(self):
        """[BUG] None 密码：系统允许 None 作为密码"""
        result = self.auth.register("alice", None)
        self.assertTrue(result)  # 这是一个问题！

    def test_register_sql_injection_username(self):
        """[安全] 用户名中的特殊字符：系统没有做输入清洗"""
        result = self.auth.register("'; DROP TABLE users;--", "password")
        self.assertTrue(result)  # 特殊字符被原样存入
        self.assertIn("'; DROP TABLE users;--", self.auth.users)

    def test_register_special_characters_password(self):
        """正常注册：特殊字符密码应该被允许"""
        result = self.auth.register("alice", "P@$$w0rd!#%^&*()")
        self.assertTrue(result)

    def test_register_very_long_username(self):
        """[边界] 超长用户名：系统没有长度限制"""
        long_name = "a" * 10000
        result = self.auth.register(long_name, "password")
        self.assertTrue(result)  # 没有长度校验

    def test_register_case_sensitivity(self):
        """[设计缺陷] 用户名大小写敏感：'Alice' 和 'alice' 是两个不同用户"""
        self.auth.register("Alice", "pass1")
        result = self.auth.register("alice", "pass2")
        self.assertTrue(result)  # 两个 'alice' 共存
        self.assertEqual(len(self.auth.users), 2)


class TestUserAuthLogin(unittest.TestCase):
    """登录功能测试"""

    def setUp(self):
        self.auth = UserAuth()
        self.auth.register("alice", "P@ssw0rd")

    def test_login_normal(self):
        """正常登录：正确的用户名和密码应返回用户信息"""
        result = self.auth.login("alice", "P@ssw0rd")
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "alice")
        self.assertTrue(result["logged_in"])

    def test_login_wrong_password(self):
        """错误密码：应返回 None"""
        result = self.auth.login("alice", "wrongpass")
        self.assertIsNone(result)

    def test_login_nonexistent_user(self):
        """不存在的用户：应返回 None"""
        result = self.auth.login("bob", "password")
        self.assertIsNone(result)

    def test_login_empty_password(self):
        """[安全] 空密码尝试：如果用户密码为空，可以登录"""
        self.auth.register("bob", "")
        result = self.auth.login("bob", "")
        self.assertIsNotNone(result)  # 空密码居然能登录

    def test_login_case_sensitivity(self):
        """[设计缺陷] 密码大小写敏感但用户可能不知道"""
        result = self.auth.login("alice", "p@ssw0rd")
        self.assertIsNone(result)  # 大小写不一致

    def test_login_timing_attack(self):
        """[安全] 明文比较密码：可能存在时序攻击风险
        当前的 == 比较在 Python 中对字符串会逐字符比较，
        理论上攻击者可以通过响应时间推断密码前缀"""
        import time
        # 这个测试是说明性的，验证当前代码使用 == 比较而非恒定时间比较
        stored = self.auth.users["alice"]
        # 如果密码被哈希，这里应该看不到明文
        self.assertEqual(stored, "P@ssw0rd")  # 明文存储！重大安全问题

    def test_login_returns_mutable_dict(self):
        """[设计缺陷] login 返回可变字典，调用者可修改"""
        result = self.auth.login("alice", "P@ssw0rd")
        result["username"] = "hacked"
        result["admin"] = True
        # 返回的字典被外部修改了
        self.assertEqual(result["username"], "hacked")


class TestUserAuthChangePassword(unittest.TestCase):
    """修改密码功能测试"""

    def setUp(self):
        self.auth = UserAuth()
        self.auth.register("alice", "oldpass")

    def test_change_password_normal(self):
        """正常修改密码：旧密码正确时应成功"""
        result = self.auth.change_password("alice", "oldpass", "newpass")
        self.assertTrue(result)
        self.assertEqual(self.auth.users["alice"], "newpass")

    def test_change_password_wrong_old(self):
        """旧密码错误：应返回 False"""
        result = self.auth.change_password("alice", "wrongold", "newpass")
        self.assertFalse(result)
        self.assertEqual(self.auth.users["alice"], "oldpass")  # 密码不变

    def test_change_password_nonexistent_user(self):
        """不存在的用户：应返回 False"""
        result = self.auth.change_password("bob", "old", "new")
        self.assertFalse(result)

    def test_change_password_to_empty(self):
        """[BUG] 修改密码为空：系统允许将密码设为空字符串"""
        result = self.auth.change_password("alice", "oldpass", "")
        self.assertTrue(result)  # 这是一个问题！
        self.assertEqual(self.auth.users["alice"], "")

    def test_change_password_to_none(self):
        """[BUG] 修改密码为 None：系统允许将密码设为 None"""
        result = self.auth.change_password("alice", "oldpass", None)
        self.assertTrue(result)  # 这是一个问题！
        self.assertIsNone(self.auth.users["alice"])

    def test_change_password_same_as_old(self):
        """[设计缺陷] 新旧密码相同：系统没有阻止重复使用旧密码"""
        result = self.auth.change_password("alice", "oldpass", "oldpass")
        self.assertTrue(result)  # 应该拒绝，但没有

    def test_change_password_no_old_password_check_for_nonexistent(self):
        """[BUG] 不存在的用户用 None 旧密码可能绕过检查
        users.get(username) 对不存在的用户返回 None，
        如果 old_password 也是 None，则条件成立！"""
        # 先确认 bob 不存在
        self.assertNotIn("bob", self.auth.users)
        result = self.auth.change_password("bob", None, "hacked")
        self.assertTrue(result)  # 严重 bug！不存在的用户 + None 旧密码 = 修改成功
        self.assertIn("bob", self.auth.users)
        self.assertEqual(self.auth.users["bob"], "hacked")

    def test_change_password_new_password_shorter(self):
        """[设计缺陷] 没有密码复杂度校验"""
        result = self.auth.change_password("alice", "oldpass", "a")
        self.assertTrue(result)  # 单字符密码就被接受了


class TestUserAuthDeleteUser(unittest.TestCase):
    """删除用户功能测试"""

    def setUp(self):
        self.auth = UserAuth()
        self.auth.register("alice", "P@ssw0rd")
        self.auth.register("bob", "password")

    def test_delete_user_normal(self):
        """正常删除：存在的用户应被成功删除"""
        result = self.auth.delete_user("alice")
        self.assertTrue(result)
        self.assertNotIn("alice", self.auth.users)

    def test_delete_nonexistent_user(self):
        """删除不存在的用户：应返回 False"""
        result = self.auth.delete_user("charlie")
        self.assertFalse(result)

    def test_delete_user_then_login(self):
        """删除后登录：应返回 None"""
        self.auth.delete_user("alice")
        result = self.auth.login("alice", "P@ssw0rd")
        self.assertIsNone(result)

    def test_delete_all_users(self):
        """删除所有用户：系统应有某种保护或状态"""
        self.auth.delete_user("alice")
        self.auth.delete_user("bob")
        self.assertEqual(len(self.auth.users), 0)
        # 空系统没有任何状态指示

    def test_delete_empty_string_username(self):
        """[BUG] 空字符串用户名：如果有人注册了空用户名，可以删除"""
        self.auth.register("", "pass")
        result = self.auth.delete_user("")
        self.assertTrue(result)

    def test_delete_none_username(self):
        """[BUG] None 用户名：如果有人注册了 None，可以删除"""
        self.auth.register(None, "pass")
        result = self.auth.delete_user(None)
        self.assertTrue(result)


class TestUserAuthSecurity(unittest.TestCase):
    """安全场景综合测试"""

    def setUp(self):
        self.auth = UserAuth()

    def test_plaintext_password_storage(self):
        """[严重安全] 密码明文存储：可以直接读取所有密码"""
        self.auth.register("alice", "MySecret123")
        self.auth.register("bob", "Hunter2")
        # 密码以明文存储在内存中
        self.assertEqual(self.auth.users["alice"], "MySecret123")
        self.assertEqual(self.auth.users["bob"], "Hunter2")
        # 如果这个字典被序列化或日志记录，密码直接泄露

    def test_no_rate_limiting(self):
        """[安全] 无暴力破解防护：可以无限次尝试登录"""
        self.auth.register("alice", "correct")
        for i in range(10000):
            self.auth.login("alice", f"attempt_{i}")
        # 没有任何限制或锁定机制

    def test_no_session_management(self):
        """[设计缺陷] 无会话管理：登录返回的是静态字典，没有 token 或 session"""
        result = self.auth.login("alice", "P@ssw0rd")
        # 没有返回 session token、过期时间等
        # 无法追踪用户登录状态、无法做 session 管理

    def test_no_logging_or_audit(self):
        """[设计缺陷] 无审计日志：注册、登录、修改密码等操作没有日志"""
        self.auth.register("alice", "pass")
        self.auth.login("alice", "pass")
        self.auth.delete_user("alice")
        # 没有任何日志记录这些操作

    def test_concurrent_access_unsafe(self):
        """[设计缺陷] 非线程安全：多线程并发操作可能导致数据竞争"""
        import threading

        def register_n(n):
            for i in range(n):
                self.auth.register(f"user_{threading.get_ident()}_{i}", "pass")

        threads = [threading.Thread(target=register_n, args=(100,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # 如果有问题，某些用户可能丢失
        # 由于 GIL，dict 操作在 CPython 中基本安全，但不保证语义正确

    def test_no_input_sanitization(self):
        """[安全] 无输入清洗：任何 Python 对象都可作为用户名"""
        # 试试用数字、元组等作为用户名
        self.auth.register(12345, "pass")
        self.auth.register(("tuple", "key"), "pass")
        self.assertIn(12345, self.auth.users)
        self.assertIn(("tuple", "key"), self.auth.users)


class TestUserAuthEdgeCases(unittest.TestCase):
    """边界条件测试"""

    def setUp(self):
        self.auth = UserAuth()

    def test_register_after_delete_same_username(self):
        """删除后重新注册同名用户：应该成功"""
        self.auth.register("alice", "pass1")
        self.auth.delete_user("alice")
        result = self.auth.register("alice", "pass2")
        self.assertTrue(result)
        self.assertEqual(self.auth.users["alice"], "pass2")

    def test_login_returns_new_dict_each_time(self):
        """每次登录返回新字典：验证不是共享同一引用"""
        self.auth.register("alice", "pass")
        r1 = self.auth.login("alice", "pass")
        r2 = self.auth.login("alice", "pass")
        # 两个不同的字典对象
        self.assertIsNot(r1, r2)
        # 修改一个不影响另一个
        r1["logged_in"] = False
        self.assertTrue(r2["logged_in"])

    def test_register_whitespace_username(self):
        """[设计缺陷] 纯空格用户名被允许"""
        result = self.auth.register("   ", "password")
        self.assertTrue(result)  # 空格用户名被接受

    def test_register_unicode_username(self):
        """正常注册：Unicode 用户名应该被允许"""
        result = self.auth.register("用户名", "密码")
        self.assertTrue(result)

    def test_change_password_nonexistent_with_none_old_creates_user(self):
        """[严重 BUG] change_password 中 users.get(username) != old_password 的漏洞
        当 username 不存在时，get 返回 None。
        如果 old_password 也是 None，条件不成立（None != None 为 False），
        所以代码会执行 self.users[username] = new_password，直接创建新用户！
        
        这等于任何人都可以用 change_password(username, None, any_password) 来创建用户。"""
        # 确保用户不存在
        self.assertNotIn("ghost_user", self.auth.users)
        # 用 None 旧密码"修改"一个不存在的用户
        result = self.auth.change_password("ghost_user", None, "pwned")
        self.assertTrue(result)
        self.assertEqual(self.auth.users["ghost_user"], "pwned")
        # 新用户被凭空创建了！这是一个后门级的 bug


if __name__ == "__main__":
    unittest.main(verbosity=2)
