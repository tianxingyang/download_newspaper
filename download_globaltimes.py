# -*- coding: utf-8 -*-
import datetime
import os
import re
import requests

host_link = "http://www.ht5.com"
base_location = "/home/vitoyang/test/global_times/"


def main():
    response = requests.get(host_link + "/hqsb.html")

    # 这神奇的编码格式，折腾了半天，开始还以为是gb2312呢……
    # print(response.content.decode('GB18030'))

    newest_paper_date = re.search(r"\d{4}-\d{1,2}-\d{1,2}", response.text)
    print("最新的报纸日期是: " + newest_paper_date.group())
    print("今天的日期是: " + str(datetime.date.today()))
    print('是否继续 \033[4m%s\033[0mes Or \033[4m%s\033[0mo' % ('Y', 'N'))
    ctrl_code = input()
    if ctrl_code == 'n' or ctrl_code == 'N':
        return
    elif ctrl_code != 'y' and ctrl_code != 'Y':
        print("error input")
        return

    if re.search(r"readbk-\d*.html", response.text) != None:
        print("今天的报纸还在发布中")
        return

    # 获取今日环球时报地址
    link = re.search(r"/html/html/.*.html", response.text).group()
    big_link = host_link + link

    for i in range(1, 17):
        suffix = "-" + str(i) + ".html"
        tmp_link = re.sub(r"\.html", suffix, big_link)
        # print(tmp_link)
        tmp_response = requests.get(tmp_link)
        # 获取今日环球时报图片的地址
        download_link = re.search(
            r"http://images.jdqu.com/upload/hqck.*.jpg", tmp_response.text).group()
        print("downloading from " + download_link)
        image_response = requests.get(download_link)
        file_name_suffix = ""
        if i < 10:
            file_name_suffix = "0" + str(i) + ".jpg"
        else:
            file_name_suffix = str(i) + ".jpg"
        file_name = str(datetime.date.today()) + "-" + file_name_suffix
        # 将获取到的图片缓存到本地
        sz = open(base_location + file_name,
                  "wb").write(image_response.content)
        print("saving " + file_name)

    # 将所有图片转为pdf
    convert_cmd = "convert " + base_location + "*.jpg `date +%Y%m%d`.pdf"
    os.system(convert_cmd)
    # 删除图片缓存
    del_cmd = "rm " + base_location + "*.jpg"
    os.system(del_cmd)


if __name__ == "__main__":
    main()
