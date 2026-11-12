#!/usr/bin/env python3
"""Bark 推送（仅标准库）。

用法：
    python bark.py "标题" "正文"
    BARK_TITLE=.. BARK_BODY=.. python bark.py

环境变量：
    BARK_KEY     必填，Bark key（未设置则跳过，不报错）
    BARK_SERVER  可选，默认 https://api.day.app
    BARK_GROUP   可选，分组名，默认 Hermes
    BARK_URL     可选，完整跳转链接
"""
import json
import os
import sys
import urllib.request


def send_bark(title, body, group=None, url=None):
    key = os.getenv("BARK_KEY", "").strip()
    if not key:
        print("❌ BARK_KEY 未设置，跳过 Bark 推送")
        return False

    server = os.getenv("BARK_SERVER", "https://api.day.app").strip().rstrip("/")
    payload = {
        "title": title,
        "body": body,
        "group": group or os.getenv("BARK_GROUP", "Hermes"),
    }
    if url:
        payload["url"] = url

    req = urllib.request.Request(
        f"{server}/{key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "curl/8.5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"❌ Bark 推送异常: {exc}")
        return False

    if result.get("code") == 200:
        print(f"✅ Bark 推送成功: {title}")
        return True
    print(f"❌ Bark 推送失败: {result}")
    return False


if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else os.getenv("BARK_TITLE", "Hermes 通知")
    body = sys.argv[2] if len(sys.argv) > 2 else os.getenv("BARK_BODY", "")
    sys.exit(0 if send_bark(title, body, url=os.getenv("BARK_URL")) else 1)
