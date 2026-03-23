"""测试通知发送模块。"""

import json
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pr_queue.notifier import send_webhook, send_slack_notification, send_feishu_notification


def _start_test_server(port=19876, received=None):
    """启动一个简单的测试 HTTP 服务器来接收 webhook。"""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            if received is not None:
                received.append(json.loads(body.decode("utf-8")))
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    thread = Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    return server


class TestSendWebhook(unittest.TestCase):
    """Webhook 发送测试。"""

    def test_dry_run_returns_true(self):
        result = send_webhook("http://invalid-url.example.com", "test", dry_run=True)
        self.assertTrue(result)

    def test_slack_notification_dry_run(self):
        result = send_slack_notification("http://example.com", "test", dry_run=True)
        self.assertTrue(result)

    def test_feishu_notification_dry_run(self):
        result = send_feishu_notification("http://example.com", "test", dry_run=True)
        self.assertTrue(result)

    def test_sends_to_real_server(self):
        received = []
        server = _start_test_server(port=19877, received=received)
        try:
            result = send_webhook(
                "http://127.0.0.1:19877", "Hello Webhook!"
            )
            self.assertTrue(result)
            self.assertEqual(len(received), 1)
            self.assertEqual(received[0]["text"], "Hello Webhook!")
        finally:
            server.server_close()

    def test_invalid_url_returns_false(self):
        result = send_webhook("http://127.0.0.1:19999", "test")
        self.assertFalse(result)

    def test_message_encoding(self):
        received = []
        server = _start_test_server(port=19878, received=received)
        try:
            send_webhook("http://127.0.0.1:19878", "中文消息测试 🦞")
            self.assertEqual(received[0]["text"], "中文消息测试 🦞")
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
