"""Giao thức message: mỗi message là 1 dòng JSON UTF-8 kết thúc bằng '\\n'.

Yêu cầu : {"type": "...", "payload": {...}, "id": 12}
ACK     : {"type": "ACK",   "id": 12, "payload": {...}}
ERROR   : {"type": "ERROR", "id": 12, "payload": {"code": "...", "message": "..."}}
Push    : {"type": "...", "payload": {...}}            (server chủ động, không có id)
"""
import json
import threading

MAX_LINE = 1_000_000


def encode(msg: dict) -> bytes:
    return json.dumps(msg, ensure_ascii=False).encode("utf-8") + b"\n"


class MessageStream:
    """Gói socket thành luồng message theo dòng (framing)."""

    def __init__(self, sock):
        self.sock = sock
        self._buf = b""
        self._send_lock = threading.Lock()

    def send(self, msg_type, payload=None, req_id=None):
        msg = {"type": msg_type, "payload": payload if payload is not None else {}}
        if req_id is not None:
            msg["id"] = req_id
        data = encode(msg)
        with self._send_lock:
            self.sock.sendall(data)

    def recv(self):
        """Đọc 1 message. Trả None nếu đối phương đóng kết nối."""
        while b"\n" not in self._buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                return None
            self._buf += chunk
            if len(self._buf) > MAX_LINE:
                raise ValueError("Message quá lớn")
        line, self._buf = self._buf.split(b"\n", 1)
        msg = json.loads(line.decode("utf-8"))
        if not isinstance(msg, dict) or "type" not in msg:
            raise ValueError("Message sai cấu trúc")
        msg.setdefault("payload", {})
        return msg
