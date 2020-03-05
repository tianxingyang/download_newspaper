#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import json
import os
import random
import re
import requests
import shutil
import subprocess
import sys
import time

my_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36 Edg/80.0.361.50"
}

config = {}
serverchan = {}
has_serverchan = False
date_of_today = str(datetime.datetime.today().date())
last_download_date = datetime.date.fromtimestamp(0)


def serverchan_send(text="", desp=""):
    global has_serverchan
    if not has_serverchan:
        return
    d = {
        "text": text,
        "desp": desp
    }
    rsp = requests.post(serverchan["addr"], d)


def read_config():
    if not os.path.exists("config.json"):
        print("config.json not exist")
        return False
    else:
        with open("config.json") as f:
            global config
            config = json.load(f)

    if os.path.exists("serverchan.json"):
        with open("serverchan.json") as f:
            global serverchan
            global has_serverchan
            serverchan = json.load(f)
            has_serverchan = True
    return True


def download_and_save(link, suffix_num):
    # 生成缓存文件后缀名
    file_name_suffix = ""
    if suffix_num < 10:
        file_name_suffix = "0" + str(suffix_num) + ".jpg"
    else:
        file_name_suffix = str(suffix_num) + ".jpg"
    file_name = date_of_today + "-" + file_name_suffix
    if os.path.exists(config['base_location'] + "tmp/" + file_name):
        print(file_name + "已下载，跳过")
        return
    download_link = search_download_link(link)
    if download_link is None:
        return
    print("downloading from " + download_link)
    image_response = requests.get(download_link, headers=my_headers)
    sz = open(config['base_location'] + "tmp/" + file_name,
              "wb").write(image_response.content)
    print("saving " + file_name)


def search_download_link(link):
    tmp_response = requests.get(link, headers=my_headers)
    download_link = re.search(
        "环球时报电子版在线阅读 .*\" src=\"http://.*.jpg\"", tmp_response.content.decode("GB18030"))
    if download_link is None:
        serverchan_send("查找图片下载地址失败", "脚本退出")
        sys.exit(0)
        return None
    download_link = re.search("http://.*.jpg", download_link.group())
    if download_link is None:
        serverchan_send("查找图片下载地址失败", "脚本退出")
        sys.exit(0)
        return None
    return download_link.group()


# true 就是用户输入确定，false 就是用户输入取消
def control():
    ctrl_code = input()
    if ctrl_code == 'n' or ctrl_code == 'N':
        return False
    elif ctrl_code != 'y' and ctrl_code != 'Y':
        print("error input")
        return False
    else:
        return True


def do_download():
    response = requests.get(
        config['host_link'] + "/hqsb.html", headers=my_headers)
    global date_of_today
    # 这神奇的编码格式，折腾了半天，开始还以为是gb2312呢……
    # print(response.content.decode('GB18030'))

    newest_paper_date = re.search(r"\d{4}-\d{1,2}-\d{1,2}", response.text)
    if newest_paper_date is None:
        serverchan_send("报纸日期无法获取", "报纸供应商出现问题，脚本退出")
        sys.exit(0)
        return
    if newest_paper_date.group() != date_of_today:
        return

    if not os.path.exists(config['base_location'] + "tmp"):
        os.mkdir(config['base_location'] + "tmp")

    global debug
    if debug:
        print("最新的报纸日期是: " + newest_paper_date.group())
        print("今天的日期是: " + date_of_today)
        date_of_today = newest_paper_date.group()
        print('是否继续 \033[4m%s\033[0mes Or \033[4m%s\033[0mo' % ('Y', 'N'))
        if not control():
            return

        if os.path.exists(config['target_location'] + "环球时报-" + date_of_today + ".pdf"):
            print("今日报纸已经下载")
            print(
                '是否重新下载 \033[4m%s\033[0mes Or \033[4m%s\033[0mo' % ('Y', 'N'))
            if not control():
                return
            else:
                os.remove(config['target_location'] + date_of_today + ".pdf")
    else:
        # release 模式默认覆盖已下载的当日报纸
        if os.path.exists(config['target_location'] + "环球时报-" + date_of_today + ".pdf"):
            os.remove(config['target_location'] +
                      "环球时报-" + date_of_today + ".pdf")

    link = re.search(
        "/arc/jwbt/hqsb/\d{4}/\d{4}/\d*.html", response.text)
    if link is None:
        serverchan_send("首版查找失败", "脚本退出")
        sys.exit(0)
        return
    big_link = config['host_link'] + link.group()
    download_and_save(big_link, 1)

    pages = 8 if datetime.datetime.today().weekday() == 5 else 16
    for i in range(2, pages + 1):
        time.sleep(random.random())
        suffix = "_" + str(i) + ".html"
        tmp_link = re.sub("\.html", suffix, big_link)
        # print(tmp_link)
        download_and_save(tmp_link, i)

    # 将所有图片转为 pdf
    convert_cmd = "sudo -u www-data convert " + config['base_location'] + "tmp/" + \
        "*.jpg " + config['target_location'] + \
        "环球时报-" + date_of_today + ".pdf"
    # print(convert_cmd)
    print("converting jpeg to pdf")
    # p = subprocess.run(convert_cmd)
    os.system(convert_cmd)
    # 删除图片缓存
    shutil.rmtree(config['base_location'] + "tmp")
    print("tmp files has been deleted")
    # 刷新 nextcloud 缓存
    # refresh_cmd = "sudo -u www-data php " + config['occ_path'] + \
    #     " files:scan --path=" + config['refresh_target']
    # print(refresh_cmd)
    refresh_cmd = ['sudo', '-u', 'www-data', 'php', config['occ_path'],
                   'files:scan', '--path=%s' % config['refresh_target']]
    p = subprocess.run(refresh_cmd, stdout=open("out", "a"))
    # os.system(refresh_cmd)
    global last_download_date
    last_download_date = datetime.datetime.today().date()
    serverchan_send("报纸下载成功，请查收")


def main():
    global last_download_date
    while True:
        if datetime.datetime.today().weekday() == 6:
            time.sleep(24*60*60)

        if time.localtime()[3] >= config['start_time'] and last_download_date != datetime.datetime.today().date():
            print(last_download_date)
            print(datetime.datetime.today())
            do_download()

        time.sleep(5*60)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:\t%s\t[-r release, run in background]\n\t\t\t\t[-d debug mode]" %
              os.path.basename(__file__))
        sys.exit(0)

    if os.getuid() != 0:
        print("请用root用户启动")
        sys.exit(0)

    debug = False
    if sys.argv[1] == '-d':
        debug = True
    elif sys.argv[1] != '-r':
        print("Usage:\t%s\t[-r release, run in background]\n\t\t\t\t[-d debug mode]" %
              os.path.basename(__file__))
        sys.exit(0)

    if not read_config():
        sys.exit(0)

    if not debug:
        try:
            pid = os.fork()
            if pid != 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" %
                             (e.errno, e.strerror))
            sys.exit(1)

        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid != 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" %
                             (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout = open("out", "w")
        sys.stderr = open("err", "w")

    main()
