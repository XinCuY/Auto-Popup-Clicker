import cv2
import numpy as np
import time
import keyboard
import win32gui
import win32con
import win32api
from wgc_python import WindowCapture

# ===== 配置 =====
PARTIAL_TITLE = "浙江统计教育培训在线学习中心"
TEMPLATE_PATH = "popup.png"
MATCH_THRESHOLD = 0.8
CLICK_COOLDOWN = 2.0

# 点击偏移（请根据模板测量）
CLICK_OFFSET_X = 380
CLICK_OFFSET_Y = 492

# ===== 获取窗口句柄、标题和类名 =====
def find_window_info_by_partial_title(partial_title):
    hwnds = []
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        if partial_title.lower() in title.lower():
            hwnds.append((hwnd, title))
    win32gui.EnumWindows(callback, None)
    if not hwnds:
        return None, None, None
    hwnd, title = hwnds[0]
    # 获取窗口类名
    class_name = win32gui.GetClassName(hwnd)
    return hwnd, title, class_name

hwnd, title, class_name = find_window_info_by_partial_title(PARTIAL_TITLE)
if hwnd is None:
    print("未找到窗口")
    exit()
print(f"✅ 找到窗口: 句柄={hwnd}, 标题='{title}', 类名='{class_name}'")

# ===== 加载模板 =====
template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_GRAYSCALE)
if template is None:
    print("模板文件未找到")
    exit()
tw, th = template.shape[::-1]

# ===== 后台点击（PostMessage） =====
def click_background(hwnd, x, y):
    lparam = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)

# ===== 主程序 =====
print("开始监控（WGC 后台截图 + PostMessage 后台点击）... 按 ESC 退出")
last_click_time = 0

# 正确传入标题和类名
with WindowCapture(title, class_name, client_area_only=True) as cap:
    while True:
        if keyboard.is_pressed('esc'):
            break

        frame = cap.capture_one()
        img_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)


        if max_val >= MATCH_THRESHOLD:
            now = time.time()
            if now - last_click_time < CLICK_COOLDOWN:
                continue
            click_x = max_loc[0] + CLICK_OFFSET_X
            click_y = max_loc[1] + CLICK_OFFSET_Y
            print(f"✅ 检测到弹窗！匹配度 {max_val:.3f}，后台点击 ({click_x}, {click_y})")
            click_background(hwnd, click_x, click_y)
            last_click_time = now
            time.sleep(1)

        time.sleep(0.05)
