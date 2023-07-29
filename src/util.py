import math

import cv2 as cv
import win32api
import win32con
import win32gui


def get_hwnd(window_name):
    def winEnumHandler(hwnd, hwnds):
        if (
            win32gui.IsWindowVisible(hwnd)
            and win32gui.GetWindowText(hwnd).strip() == window_name
        ):
            hwnds.append(hwnd)
            return True

    hwnds = []
    win32gui.EnumWindows(winEnumHandler, hwnds)
    return None if len(hwnds) == 0 else hwnds[0]


def check_res(res, win_rect):
    w = win_rect[2] - win_rect[0]
    h = win_rect[3] - win_rect[1]
    for i in range(len(res)):
        if res[i][0] == w and res[i][1] == h:
            return i
    return w, h


def press_space():
    # Ref for keyboard events - https://gist.github.com/chriskiehl/2906125
    # https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    win32api.keybd_event(0x20, 0, 0, 0)
    win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)


def get_angle(img):
    try:
        m = cv.moments(img.T, True)
        x = int(m["m10"] / m["m00"])
        y = int(m["m01"] / m["m00"])
        return math.atan2(y - 100, x - 100) / math.pi * 180
    except ZeroDivisionError as e:
        print(e)
        return None


def ang_diff(ang):
    return (ang + 180) % 360 - 180


def mov_avg(err, n):
    err[1] += n
    err[2] += 1
    err[0] = err[1] / err[2]


def draw_line(wDC, cx, cy, r1, r2, th):
    th = th / 180 * math.pi
    win32gui.MoveToEx(wDC, cx + int(r1 * math.cos(th)), cy + int(r1 * math.sin(th)))
    win32gui.LineTo(wDC, cx + int(r2 * math.cos(th)), cy + int(r2 * math.sin(th)))
