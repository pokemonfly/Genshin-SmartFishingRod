import win32gui
import win32ui
import win32api
import win32con
from multiprocessing import Process, Pipe
from loguru import logger
from time import sleep
import ctypes.wintypes as wintypes
import ctypes
import numpy as np


class Monitor (Process):
    def __init__(self):
        super().__init__(daemon=True)
        while True:
            if hwnd := win32gui.FindWindow('UnityWndClass', '原神'):
                self.hwnd = hwnd
                break
            else:
                logger.info('游戏未启动... ')
                sleep(5)
        self.receiver, self.sender = Pipe(False)
        self.w, self.h = 0, 0
        self.rect = -1, -1, 0, 0
        self.is_stop = False
        
        self.start()

    def syncWindow(self):
        rect = wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(self.hwnd),
            ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )
        self.rect = rect.left, rect.top, rect.right, rect.bottom
        self.w, self.h = rect.right - rect.left, rect.bottom - rect.top

    def screencap(self):
        return self.receiver.recv()

    def run(self):
        while self.rect[0] < 0:
            # 全屏游戏 最小化时 拿不到窗口大小
            sleep(1)
            self.syncWindow()

        left, top, w, h = 0, 0, self.w, self.h
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
        cDC.SelectObject(dataBitMap)

        while True:
            if self.is_stop:
                dcObj.DeleteDC()
                cDC.DeleteDC()
                win32gui.DeleteObject(dataBitMap.GetHandle())
                win32gui.ReleaseDC(self.hwnd, wDC)

            cDC.BitBlt((0, 0), (w, h), dcObj, (left, top), win32con.SRCCOPY)
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            img = np.frombuffer(signedIntsArray, dtype=np.uint8)
            img.shape = (h, w, 4)
            self.sender.send(img)

    def mouse(self, isKeyUp):
        x, y = win32api.GetCursorPos()
        message = win32con.WM_LBUTTONDOWN if isKeyUp else win32con.WM_LBUTTONUP
        win32gui.PostMessage(self.hwnd, message, win32con.MK_LBUTTON,
                             ((y << 16) | x))


