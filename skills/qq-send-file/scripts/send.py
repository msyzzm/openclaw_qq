#!/usr/bin/env python3
"""qq-send-file — 把文件通过 openclaw_qq 发送 API 推到指定 QQ 群。

用法:
    python3 send.py <群号> <文件路径> [--type auto|image|video|record|file] [--text "说明文字"]
                    [--host 127.0.0.1] [--port 7600] [--token <TOKEN>] [--timeout 180]

token 解析顺序: --token > 环境变量 QQ_SEND_TOKEN > ~/.openclaw/.qq-send-token
成功时打印服务端 JSON 并返回 0；失败时打印错误到 stderr 并返回非 0。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_HOST = os.environ.get("QQ_SEND_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("QQ_SEND_PORT", "7600"))


def load_token(cli_token: str | None) -> str | None:
    if cli_token:
        return cli_token
    env = os.environ.get("QQ_SEND_TOKEN")
    if env:
        return env
    for candidate in (
        Path.home() / ".openclaw" / ".qq-send-token",
        Path.home() / ".qq-send-token",
    ):
        if candidate.is_file():
            value = candidate.read_text(encoding="utf-8").strip()
            if value:
                return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a file to a QQ group via the openclaw_qq send-API.")
    parser.add_argument("group", help="target QQ group id (digits)")
    parser.add_argument("file", help="path to the file to send")
    parser.add_argument("--type", default="auto",
                        choices=["auto", "image", "video", "record", "file"],
                        help="send type; auto = detect from file extension (default: auto)")
    parser.add_argument("--text", default="", help="caption text sent before image/video")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"API host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"API port (default: {DEFAULT_PORT})")
    parser.add_argument("--token", default=None, help="API token (else QQ_SEND_TOKEN env or token file)")
    parser.add_argument("--timeout", type=float, default=180.0, help="request timeout seconds (default: 180)")
    args = parser.parse_args()

    file_path = Path(args.file).expanduser()
    if not file_path.is_file():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 2

    token = load_token(args.token)
    if not token:
        print("error: no API token. Pass --token, set QQ_SEND_TOKEN, "
              "or write it to ~/.openclaw/.qq-send-token", file=sys.stderr)
        return 2

    data = file_path.read_bytes()
    query = {"group": args.group, "filename": file_path.name}
    if args.type != "auto":
        query["type"] = args.type
    if args.text:
        query["text"] = args.text
    url = f"http://{args.host}:{args.port}/send?" + urllib.parse.urlencode(query)

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8")
            print(body)
            try:
                return 0 if json.loads(body).get("ok") else 1
            except json.JSONDecodeError:
                return 1
    except urllib.error.HTTPError as err:
        detail = ""
        try:
            detail = err.read().decode("utf-8")
        except Exception:
            pass
        print(f"HTTP {err.code}: {detail}", file=sys.stderr)
        return 1
    except Exception as err:  # noqa: BLE001
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
