import datetime
import os
import pytz
import requests
import subprocess
import sys
import time
import traceback

import lovely_logger as log

from PIL import Image, ImageDraw, ImageFont

DEBUG = False
LOG_INFO = False
LOG_ERROR = False

BEFORE_THIS_HOUR = 1
EVERY_X_MINS = 5

if DEBUG or os.name == 'nt':
    DEBUG = True
    import cv2
    import numpy as np
else:
    from waveshare_epd import epd2in13_V2


def get_current_directory():
    return os.path.dirname(os.path.realpath(__file__))


log.init(os.path.join(get_current_directory(), 'log.txt'), max_files=10)
TURN_ON_GHOST_FIX_LOOP = False


def black_white_loop_to_fix_ghosting(epd,
                                     monitor_height,
                                     monitor_width,
                                     loop_num_limit=1440):
    if not DEBUG:
        loop_num = 0
        while loop_num < loop_num_limit:
            epd.init(epd.FULL_UPDATE)
            clear_image = Image.new('1', (monitor_height, monitor_width), 0)
            epd.display(epd.getbuffer(clear_image))
            time.sleep(30)

            epd.init(epd.FULL_UPDATE)
            clear_image = Image.new('1', (monitor_height, monitor_width), 255)
            epd.display(epd.getbuffer(clear_image))
            time.sleep(30)

            loop_num += 1


def get_coinbase_ethereum_sell_price():
    response = requests.get('https://api.pro.coinbase.com/products/eth-gbp/ticker')
    if response.status_code != 200:
        raise ApiError('GET /products/eth-gbp/ticker : {}'.format(response.status_code))

    return float(response.json()['price'])


def loop():
    try:
        log.info("Running...")

        if not DEBUG:
            epd = epd2in13_V2.EPD()

            monitor_height = epd.width
            monitor_width = epd.height

            log.info("Initialising and clearing...")
            epd.init(epd.FULL_UPDATE)
            epd.Clear(0xFF)
        else:
            monitor_height = 122
            monitor_width = 250

        # Init font
        font_path = os.path.join(get_current_directory(), 'ComicNeue-Bold.ttf')
        font16 = ImageFont.truetype(font_path, 16)
        font18 = ImageFont.truetype(font_path, 18)
        font48 = ImageFont.truetype(font_path, 48)

        log.info("Showing time...")

        while True:
            display_image = Image.new('1', (monitor_width, monitor_height), 255)
            display_draw = ImageDraw.Draw(display_image)

            display_draw.text((180, 20), time.strftime('%H:%M:%S'), font=font18, fill=0)

            try:
                price = get_coinbase_ethereum_sell_price()
                price_str = "£{:.2f}".format(price)
                display_draw.text((36, 40), price_str, font=font48, fill=0)
                display_draw.text((8, 20), "ETH/GBP", font=font18, fill=0)

                if LOG_INFO:
                    log.info(str(price_str))
            except Exception:
                if LOG_ERROR:
                    log.error(traceback.format_exc())

            if not DEBUG:
                epd.display(epd.getbuffer(display_image.rotate(180)))
                time.sleep(50)
            else:
                display_image.save(os.path.join(get_current_directory(), 'out.png'))
                subprocess.call(os.path.join(get_current_directory(), 'out.png'), shell=True)
                exit()

    except (Exception, KeyboardInterrupt):
        if LOG_ERROR:
            log.error(traceback.format_exc())
        if not DEBUG:
            log.info("Clearing...")
            epd.init(epd.FULL_UPDATE)
            epd.Clear(0xFF)

            if TURN_ON_GHOST_FIX_LOOP:
                log.info("Running ghost fix loop...")
                black_white_loop_to_fix_ghosting(
                    epd=epd,
                    monitor_height=monitor_height,
                    monitor_width=monitor_width,
                    loop_num_limit=1440
                )

            log.info("Displaying blank image...")
            epd.init(epd.FULL_UPDATE)
            blank_image = Image.new('1', (monitor_height, monitor_width), 255)
            epd.display(epd.getbuffer(blank_image))

            log.info("Going to sleep...")
            epd.sleep()
        exit()


def main():
    loop()


if __name__ == '__main__':
    main()
