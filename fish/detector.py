import cv2
import numpy as np
import yaml
import time
from loguru import logger
from ctypes import windll


def alpha_mask(bgra):
    alpha = bgra[..., 3]
    image = bgra[..., :3].astype(np.uint16)
    for ch in range(3):
        image[..., ch] *= alpha
    image = (image // 255).astype(np.uint8)
    return image

FRAME_COLOR = [192, 255, 255]
class Detector(object):
    def __init__(self, cfg):
        if cfg:
            self.process_rect = cfg['process_rect']
            self.process_cursor_height = int(cfg['process_cursor_height'])
            self.process_frame_height = int(cfg['process_frame_height'])
            self.fish_btn_wait_rect = cfg['fish_btn_wait_rect']
            self.fish_btn_wait_img = cv2.imread(cfg['fish_btn_wait_img'])
            self.fish_btn_rise_rect = cfg['fish_btn_rise_rect']
            self.fish_btn_rise_img = cv2.imread(cfg['fish_btn_rise_img'])

    def init_pos_icon(self, image, mode="wait"):
        if image is None:
            return 0, 0, 0, 0
        height, width = image.shape[:2]
        base_x, base_y = int(width*0.8), int(height * 0.8)
        image = alpha_mask(image[base_y:, base_x:])
        mask = np.all(image != (0, 0, 0), axis=2)
        # 裁剪
        x_sum = np.sum(mask, axis=0)
        y_sum = np.sum(mask, axis=1)
        x1, x2, y1, y2 = 0, 0, 0, 0
        for i, val in enumerate(x_sum):
            if x1 == 0 and val > 0:
                x1 = i
            elif x1 > 0 and val == 0 and i > x1 + 10:
                x2 = i
                break
        for i, val in enumerate(y_sum):
            if y1 == 0 and val > 0:
                y1 = i
            elif y1 > 0 and val == 0 and i > y1 + 10:
                y2 = i
                break
        path = f'images/clip_{int(time.time())}.png'
        cv2.imwrite(path, image[y1:y2, x1:x2])

        rect = x1 + base_x, y1 + base_y, x2 + base_x, y2 + base_y
        with open('cfg.yml', 'a') as file:
            yaml.safe_dump({
                f'fish_btn_{mode}_rect': rect,
                f'fish_btn_{mode}_img': path
            }, file)
        return rect

    def init_pos_process(self, image):
        height, width = image.shape[:2]
        base_x, base_y = int(width*0.3), 0
        image = alpha_mask(
            image[base_y:int(height * 0.2), base_x:int(width*0.7)])
        mask = np.all(image == FRAME_COLOR, axis=2)
        x_sum = np.sum(mask, axis=0)
        y_sum = np.sum(mask, axis=1)
        x1, y1, y2 = 0, 0, 0  # x2对称
        for i, val in enumerate(x_sum):
            if x1 == 0 and val > 5:  # 排除意外像素影响
                x1 = i
                break
        for i, val in enumerate(y_sum):
            if y1 == 0 and val > 4:
                y1 = i
            elif y1 > 0 and val == 0:
                y2 = i
                break

        process_rect = x1 + base_x, y1 + base_y,  width - x1 - base_x,  y2 + base_y
        with open('cfg.yml', 'a') as file:
            yaml.safe_dump({
                'process_rect': process_rect,
                # 最高的
                'process_cursor_height': str(max(x_sum)),
                # 出现次数最多
                'process_frame_height': str(np.argmax(np.bincount(x_sum[x_sum > 0])))
            }, file)
        logger.info('请重启脚本')
        return process_rect

    def save_screen(self, image, marks, debug=None):
        # 原图截图
        filepath = f'images/screen_{int(time.time())}.bmp'
        if marks is not None:
            for i in marks:
                cv2.rectangle(image, i[:2],
                              i[2:4], (255, 255, 255), 1)

        if debug:
            cv2.imshow('preview', image)
            cv2.waitKey(0)
            return

        cv2.imwrite(filepath, image)
        logger.info(f'Screenshot saved to {filepath}')

    def match_icon(self, image):
        # 检查图标
        x1, y1, x2, y2 = self.fish_btn_wait_rect
        wait_mask = alpha_mask(image[y1:y2, x1:x2])
        wait_res = cv2.matchTemplate(
            wait_mask, self.fish_btn_wait_img, cv2.TM_SQDIFF_NORMED)
        loc = cv2.minMaxLoc(wait_res)
        wait_sim = 1 - loc[0]

        if wait_sim > 0.8:
            # 等待抛竿
            return True, False, self.fish_btn_wait_rect

        x1, y1, x2, y2 = self.fish_btn_rise_rect
        rise_mask = alpha_mask(image[y1:y2, x1:x2])
        rise_res = cv2.matchTemplate(
            rise_mask, self.fish_btn_rise_img, cv2.TM_SQDIFF_NORMED)
        loc = cv2.minMaxLoc(rise_res)
        rise_sim = 1 - loc[0]

        return False, rise_sim > 0.5, self.fish_btn_wait_rect

    def match_progress(self, image):  # 进度条匹配
        x1, y1, x2, y2 = self.process_rect
        progress = alpha_mask(image[y1:y2, x1:x2])
        mask = np.all(progress == FRAME_COLOR, axis=2)
        rect_arr = []
        if np.sum(mask) > 30:
            sample = np.sum(mask, axis=0)
            frame_pos, cursor_pos = [], []
            for i, val in enumerate(sample):
                # 超过后变成红色 导致像素高度变化
                if abs(val - self.process_frame_height) <= 2 and val > 0:
                    frame_pos.append(i)
                elif abs(val - self.process_cursor_height) < 4:
                    cursor_pos.append(i)

            if frame_pos and cursor_pos:
                frame_pos, cursor_pos = [min(frame_pos), max(frame_pos)], [
                    min(cursor_pos), max(cursor_pos)]
                rect_arr.append((x1 + frame_pos[0], y1, x1 +
                                 frame_pos[1], y2))
                cursor_x = sum(cursor_pos) // 2
                rect_arr.append(
                    (x1 + cursor_pos[0], y1-5, x1 + cursor_pos[1], y2+5))

                # 如果未达到位置则需要点击
                return cursor_x < frame_pos[0] + (frame_pos[1] - frame_pos[0]) * 0.4, rect_arr
        return None, rect_arr


def testProgress():
    windll.shcore.SetProcessDpiAwareness(1)
    with open('cfg.yml') as cfg:
        configs = yaml.safe_load(cfg)
    detector = Detector(configs)
    img = cv2.imread('images/screen_1638718862.bmp', cv2.IMREAD_UNCHANGED)
    is_progress, mark_arr = detector.match_progress(img)
    print(is_progress, mark_arr)
    detector.save_screen(img, mark_arr, debug=True)


def testInit():
    windll.shcore.SetProcessDpiAwareness(1)
    d = Detector(None)
    img = cv2.imread('images/screen_1638622718.bmp', cv2.IMREAD_UNCHANGED)
    # x1, y1, x2, y2 = d.init_pos_icon(img, mode='rise')
    x1, y1, x2, y2 = d.init_pos_process(img)
    d.save_screen(img, None, debug=True)


if __name__ == '__main__':
    testProgress()
