"""Chạy client:  python run_client.py"""
import json
import os

from client.app import run


def load_config():
    for p in ("config/config.json", "config/config.example.json"):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Không tìm thấy file cấu hình trong thư mục config/")


if __name__ == "__main__":
    run(load_config())
