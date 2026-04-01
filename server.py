#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订货程序本地服务器
- 提供 index.html 及项目文件
- 将图片文件夹映射到 /images/ 路径
- 多线程 + 禁用 keep-alive + SO_LINGER，彻底防止 CLOSE_WAIT 堆积
"""

import http.server
import socketserver
import socket
import os
import json
import urllib.parse
from pathlib import Path

PORT = 8888
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = r"C:\Users\ASUS\Pictures\foto detersivi"

# 支持的图片格式
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


# ──────────────────────────────────────────────────────────────
# HTTP Handler
# ──────────────────────────────────────────────────────────────
class ImageHandler(http.server.SimpleHTTPRequestHandler):
    timeout = 15
    protocol_version = "HTTP/1.0"   # 禁用 keep-alive，防止 CLOSE_WAIT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_DIR, **kwargs)

    # ---------- GET ----------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/images/'):
            filename = urllib.parse.unquote(path[len('/images/'):])
            filepath = os.path.join(IMAGE_DIR, filename)
            if os.path.isfile(filepath):
                self.send_response(200)
                ext = os.path.splitext(filename)[1].lower()
                ctype = 'image/jpeg' if ext in ('.jpg', '.jpeg') else \
                        'image/png' if ext == '.png' else \
                        'image/gif' if ext == '.gif' else \
                        'image/webp' if ext == '.webp' else 'image/jpeg'
                self.send_header('Content-Type', ctype)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.send_header('Connection', 'close')
                fsize = os.path.getsize(filepath)
                self.send_header('Content-Length', str(fsize))
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Connection', 'close')
                self.end_headers()
            return

        if path == '/api/images':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            self.end_headers()
            files = []
            if os.path.isdir(IMAGE_DIR):
                for f in sorted(os.listdir(IMAGE_DIR)):
                    if Path(f).suffix.lower() in IMG_EXTS:
                        stem = Path(f).stem
                        files.append({'filename': f, 'id': stem,
                                      'url': f'/images/{urllib.parse.quote(f)}'})
            self.wfile.write(json.dumps({'total': len(files), 'files': files},
                                        ensure_ascii=False).encode('utf-8'))
            return

        super().do_GET()

    def log_message(self, format, *args):
        if args and '/images/' in str(args[0]):
            return
        super().log_message(format, *args)

    def handle_error(self, request, client_address):
        pass


# ──────────────────────────────────────────────────────────────
# 多线程服务器
# ──────────────────────────────────────────────────────────────
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def get_request(self):
        sock, addr = super().get_request()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                        b'\x01\x00\x00\x00\x00\x00\x00\x00')
        return sock, addr


def scan_images():
    if not os.path.isdir(IMAGE_DIR):
        print(f"⚠️  图片目录不存在: {IMAGE_DIR}")
        return 0
    count = sum(1 for f in os.listdir(IMAGE_DIR)
                if Path(f).suffix.lower() in IMG_EXTS)
    return count


if __name__ == '__main__':
    img_count = scan_images()
    print("=" * 55)
    print("  [Server] 百货订货程序 - 本地服务器")
    print("=" * 55)
    print(f"  项目目录: {PROJECT_DIR}")
    print(f"  图片目录: {IMAGE_DIR}")
    print(f"  图片数量: {img_count} 张")
    print(f"")
    print(f"  ✅ 订货程序地址:  http://localhost:{PORT}")
    print("=" * 55)
    print("  按 Ctrl+C 停止服务器")
    print("")

    with ThreadedTCPServer(("", PORT), ImageHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")
