import webview
import os
import sys

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

html_path = os.path.join(base_dir, 'editor.html')
webview.create_window("AF·SIM", html_path, width=1280, height=800)
webview.start()