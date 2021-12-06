from fish import Monitor, Hotkey, Detector
from ctypes import windll
import yaml
from loguru import logger
from time import sleep


def main():
    windll.shcore.SetProcessDpiAwareness(1)
    # load config
    init_mode = False
    configs = None
    try:
        with open('cfg.yml') as cfg:
            configs = yaml.safe_load(cfg)
    except FileNotFoundError:
        init_mode = True
        logger.info("""
            首次使用需要执行程序初始化:
                进入钓鱼界面抛竿前按下Alt+1;
                鱼上钩出现进度条后(游标在最左边时)按下Alt+2
            程序初始化之后会自动结束
            如判断有问题, 钓鱼过程中按下Alt+3, 然后检查images目录下的screen_[timestamp].bmp文件标记的位置是否正确.
            如位置有偏差可修改cfg.yml
        """)

    monitor = Monitor()
    hotkey = Hotkey()
    detector = Detector(configs)

    # 当前鼠标状态
    mouse_is_pressed = None
    logger.info("开始摸鱼")
    while True:
        screen = monitor.screencap()
        marks = None
        # 是否正在钓鱼
        is_fishing = False

        if not init_mode:
            is_wait, is_rise, mark_arr1 = detector.match_icon(screen)
            if is_wait:
                if mouse_is_pressed:
                    # 上钩后 释放鼠标
                    monitor.mouse(False)
                    mouse_is_pressed = None
                continue

            is_progress, mark_arr2 = detector.match_progress(screen)
            if is_progress is not None:
                is_fishing = True
                mouse_is_pressed = is_progress
                monitor.mouse(is_progress)
                sleep(0.04)

            if is_rise and not is_fishing:
                # 点击提钩
                sleep(0.1)
                monitor.mouse(True)
                sleep(0.1)
                monitor.mouse(False)
                
            marks = [mark_arr1] + mark_arr2

        if key := hotkey.get():
            if key[0] == 'NUMPAD':
                if key[1] == 1:
                    detector.init_pos_icon(screen)
                elif key[1] == 2:
                    detector.init_pos_icon(screen, mode='rise')
                    detector.init_pos_process(screen)
                elif key[1] == 3:
                    detector.save_screen(screen, None)
                elif key[1] == 4:
                    detector.save_screen(screen, marks)


if __name__ == '__main__':
    main()
