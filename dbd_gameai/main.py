import os

import cv2 as cv
import numpy as np
import win32api
import win32con
import win32gui
import win32ui

import util


class Main:
    # Config
    GAME_TITLE = "DeadByDaylight"
    FLAGS = {"DEBUG": True, "SAVE_IMG": False}
    RES = [(1920, 1080)]
    SIZE = [[(200, 200), (860, 425)]]
    PATH = {
        "IMG_DIR": "../img",
        "IMG_FORMAT": "../img/{}.bmp",
        "TEMP_SPACE": "../asset/temp_space.bmp",
        "MASK_SKILL": "../asset/mask_skill.bmp",
    }
    THRESH = {"TEMP_SKILL": 0.8, "WHITE": 175, "NOFILL": 150, "WIGGLE": 500}

    err = [15.8, 15.8, 1, 1]
    wait, pix_count = False, 0
    ang_white, ang_red, ang_space, pix_count = None, None, None, None

    # Constructor
    def __init__(self):
        os.chdir(os.path.dirname(__file__))
        self.hwnd = util.get_hwnd(self.GAME_TITLE)
        if self.hwnd is None:
            print("{} not found. Please start the game first.".format(self.GAME_TITLE))
            exit()
        win_rect = win32gui.GetWindowRect(self.hwnd)
        self.res_i = util.check_res(self.RES, win_rect)
        if not isinstance(self.res_i, int):
            print("Screen resolution {} not yet supported.".format(self.res_i))
            print("Supported screen resolution(s) {}".format(self.RES))
            exit()

        for key in self.PATH.keys():
            self.PATH[key] = os.path.join(*self.PATH[key].split("/"))
        self.temp_space = cv.imread(self.PATH["TEMP_SPACE"], cv.IMREAD_COLOR)
        self.mask_skill = cv.imread(self.PATH["MASK_SKILL"], cv.IMREAD_COLOR)
        self.mask_skill = np.round(np.sum(self.mask_skill, axis=-1) / (255 * 3))
        self.mask_skill = self.mask_skill.astype("uint8")
        if self.FLAGS["SAVE_IMG"]:
            self.img_i = 0
            if not os.path.exists(self.PATH["IMG_DIR"]):
                os.makedirs(self.PATH["IMG_DIR"])

        self.wDC = win32gui.GetWindowDC(self.hwnd)
        self.dcObj = win32ui.CreateDCFromHandle(self.wDC)
        self.cDC = self.dcObj.CreateCompatibleDC()
        self.dataBitMap = win32ui.CreateBitmap()
        self.dataBitMap.CreateCompatibleBitmap(self.dcObj, *self.SIZE[self.res_i][0])
        self.cDC.SelectObject(self.dataBitMap)

        self.pen = win32gui.CreatePen(0, 3, win32api.RGB(0, 255, 0))
        win32gui.SelectObject(self.wDC, self.pen)

    # Destructor
    def __del__(self):
        if self.hwnd is not None:
            win32gui.DeleteObject(self.pen)
            self.dcObj.DeleteDC()
            self.cDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, self.wDC)
            win32gui.DeleteObject(self.dataBitMap.GetHandle())

    def skill_check(self):
        self.cDC.BitBlt(
            (0, 0),
            self.SIZE[self.res_i][0],
            self.dcObj,
            self.SIZE[self.res_i][1],
            win32con.SRCCOPY,
        )
        signedIntsArray = self.dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype="uint8")
        img.shape = (self.SIZE[self.res_i][0][1], self.SIZE[self.res_i][0][0], 4)
        img = img[..., :3]
        img = np.ascontiguousarray(img)
        result = cv.matchTemplate(img, self.temp_space, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

        if max_val > self.THRESH["TEMP_SKILL"]:
            img = util.extract("img", img, self.mask_skill)
            if self.pix_count is None:
                white = util.extract("white", img, self.THRESH["WHITE"])
                self.ang_white = util.get_angle(white)
                self.pix_count = np.count_nonzero(white)
                if self.THRESH["NOFILL"] < self.pix_count < self.THRESH["WIGGLE"]:
                    contr, _ = cv.findContours(
                        white, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
                    )
                    solid = np.zeros_like(white)
                    cv.drawContours(solid, contr, -1, 255, 2)
                    solid = cv.subtract(white, solid)
                    self.ang_white = util.get_angle(solid)
                elif util.is_wiggle(white, self.err, self.THRESH["WIGGLE"]):
                    white = None
                    self.ang_white = None

            red = util.extract("red", img)
            self.ang_red = util.get_angle(red)
            if self.wait:
                if self.ang_white is None:
                    self.wait = util.rw_overlap(self.ang_white, self.ang_red, self.err)
                elif self.pix_count < self.THRESH["NOFILL"]:
                    w2 = util.extract("white", img, self.THRESH["WHITE"])
                    ang_w2 = util.get_angle(white)
                    if abs(util.ang_diff(self.ang_white - ang_w2)) > self.err[0]:
                        white, self.ang_white, self.wait = w2, ang_w2, False
            elif util.rw_overlap(self.ang_white, self.ang_red, self.err):
                util.press_space()
                self.wait = True
                if self.pix_count > self.THRESH["NOFILL"]:
                    self.ang_space = self.ang_red
            if self.FLAGS["SAVE_IMG"]:
                self.dataBitMap.SaveBitmapFile(
                    self.cDC, self.PATH["IMG_FORMAT"].format(self.img_i)
                )
                self.img_i += 1
        else:
            if not (self.ang_space is None or self.ang_white is None):
                diff_key = util.ang_diff(self.ang_red - self.ang_space)
                diff_red = util.ang_diff(self.ang_white - self.ang_red)
                if diff_key * diff_red < 0:
                    util.mov_avg(self.err, self.err[0] + abs(diff_red))
                elif diff_key * diff_red > 0:
                    util.mov_avg(self.err, self.err[0] - abs(diff_red))

            self.pix_count, self.wait = None, False
            self.ang_white, self.ang_red, self.ang_space = None, None, None

    def draw_skill_check(self):
        cx, cy, r1, r2 = 960, 525, 53, 58
        if self.ang_white is not None:
            util.draw_line(self.wDC, cx, cy, r1, r2, self.ang_white)
        if self.ang_space is not None:
            util.draw_line(self.wDC, cx, cy, r1, r2, self.ang_space)
        if self.ang_red is not None:
            util.draw_line(self.wDC, cx, cy, r1, r2, self.ang_red)
            if self.ang_white is None:
                util.draw_line(self.wDC, cx, cy, r1, r2, 0)
                util.draw_line(self.wDC, cx, cy, r1, r2, 180)

    def loop(self):
        try:
            while True:
                self.skill_check()
                self.draw_skill_check()
        except KeyboardInterrupt:
            print("Terminating Loop")


if __name__ == "__main__":
    bot = Main()
    bot.loop()
