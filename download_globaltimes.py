# -*- coding: utf-8 -*-
import datetime
import os
import re
import requests

host_link = "https://www.hqck.net"
base_location = "/home/vitoyang/test/global_times/"


def download_and_save(link, suffix_num):
    print("downloading from " + link)
    image_response = requests.get(link)
    file_name_suffix = ""
    if suffix_num < 10:
        file_name_suffix = "0" + str(suffix_num) + ".jpg"
    else:
        file_name_suffix = str(suffix_num) + ".jpg"
    file_name = str(datetime.date.today()) + "-" + file_name_suffix
    sz = open(base_location + file_name, "wb").write(image_response.content)
    print("saving " + file_name)


def main():
    response = requests.get(host_link + "/hqsb.html")

    # 这神奇的编码格式，折腾了半天，开始还以为是gb2312呢……
    # print(response.content.decode('GB18030'))

    # newest_paper_date = re.search(r"\d{4}-\d{1,2}-\d{1,2}", response.text)
    # print("最新的报纸日期是: " + newest_paper_date.group())
    # print("今天的日期是: " + str(datetime.date.today()))
    # print('是否继续 \033[4m%s\033[0mes Or \033[4m%s\033[0mo' % ('Y', 'N'))
    # ctrl_code = input()
    # if ctrl_code == 'n' or ctrl_code == 'N':
    #     return
    # elif ctrl_code != 'y' and ctrl_code != 'Y':
    #     print("error input")
    #     return

    # 获取今日环球时报地址
    link = re.search(
        "/arc/jwbt/hqsb/\d{4}/\d{4}/\d*.html", response.text).group()
    big_link = host_link + link

    tmp_response = requests.get(big_link)
    # 获取今日环球时报第一张图片的地址
    download_link = re.search(
        "环球时报电子版在线阅读 .*\" src=\"http://.*.jpg\"", tmp_response.content.decode("GB18030"))
    download_link = re.search("http://.*.jpg", download_link.group()).group()
    download_and_save(download_link, 1)

    for i in range(2, 17):
        suffix = "_" + str(i) + ".html"
        tmp_link = re.sub("\.html", suffix, big_link)
        # print(tmp_link)
        tmp_response = requests.get(tmp_link)
        # 获取今日环球时报图片的地址
        download_link = re.search(
        "环球时报电子版在线阅读 .*\" src=\"http://.*.jpg\"", tmp_response.content.decode("GB18030"))
        download_link = re.search("http://.*.jpg", download_link.group()).group()
        download_and_save(download_link, i)

    # 将所有图片转为pdf
    convert_cmd = "convert " + base_location + \
        "*.jpg " + base_location + "`date +%Y-%m-%d`.pdf"
    os.system(convert_cmd)
    # 删除图片缓存
    del_cmd = "rm " + base_location + "*.jpg"
    os.system(del_cmd)


if __name__ == "__main__":
    main()
