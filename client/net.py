"""Kết nối tới server: thread đọc, hàng đợi cho giao diện, callback theo id."""
import queue
import socket
import ssl
import threading

from protocol.messages import MessageStream


class Connection:
    def __init__(self, host, port, use_ssl=False):
        self.host, self.port, self.use_ssl = host, port, use_ssl
        self.inbox = queue.Queue()      # giao diện lấy từ đây: ("resp"|"push"|"closed", msg)
        self.stream = None
        self.sock = None
        self._next = 1
        self._callbacks = {}
        self._lock = threading.Lock()
        self.connected = False

    def connect(self):
        sock = socket.create_connection((self.host, self.port), timeout=5)
        if self.use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False          # chứng chỉ tự ký dùng cho đồ án
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=self.host)
        sock.settimeout(None)
        self.sock = sock
        self.stream = MessageStream(sock)
        self.connected = True
        threading.Thread(target=self._reader, daemon=True).start()

    def send(self, msg_type, payload=None, cb=None):
        """Gửi yêu cầu. cb(msg) chạy trên luồng giao diện khi có ACK/ERROR."""
        with self._lock:
            rid = self._next
            self._next += 1
            if cb:
                self._callbacks[rid] = cb
        try:
            self.stream.send(msg_type, payload or {}, rid)
        except OSError:
            self.connected = False
            self.inbox.put(("closed", None))

    def take_callback(self, rid):
        with self._lock:
            return self._callbacks.pop(rid, None)

    def _reader(self):
        try:
            while True:
                msg = self.stream.recv()
                if msg is None:
                    break
                t = msg["type"]
                if t == "PING":
                    self.stream.send("PONG", {})
                elif t in ("ACK", "ERROR"):
                    self.inbox.put(("resp", msg))
                else:
                    self.inbox.put(("push", msg))
        except (OSError, ValueError):
            pass
        self.connected = False
        self.inbox.put(("closed", None))

    def close(self):
        self.connected = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)   # bắt buộc, nếu không thread đọc giữ socket mở
        except (OSError, AttributeError):
            pass
        try:
            self.sock.close()
        except (OSError, AttributeError):
            pass
