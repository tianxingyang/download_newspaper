# -*- coding: utf-8 -*-
import datetime
import os
import re
import requests
import shutil

host_link = "https://www.hqck.net"
base_location = "/home/vitoyang/test/global_times/"
my_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36 Edg/80.0.361.50"
}


def download_and_save(link, suffix_num):
    # 生成缓存文件后缀名
    file_name_suffix = ""
    if suffix_num < 10:
        file_name_suffix = "0" + str(suffix_num) + ".jpg"
    else:
        file_name_suffix = str(suffix_num) + ".jpg"
    file_name = str(datetime.date.today()) + "-" + file_name_suffix
    if os.path.exists(base_location + "tmp/" + file_name):
        print(file_name + "已下载，跳过")
        return
    download_link = search_download_link(link)
    if download_link == None:
        return
    print("downloading from " + download_link)
    image_response = requests.get(download_link, headers=my_headers)
    sz = open(base_location + "tmp/" + file_name, "wb").write(image_response.content)
    print("saving " + file_name)


def search_download_link(link):
    tmp_response = requests.get(link, headers=my_headers)
    download_link = re.search(
        "环球时报电子版在线阅读 .*\" src=\"http://.*.jpg\"", tmp_response.content.decode("GB18030"))
    if download_link is None:
        print("查找图片下载地址失败")
        return None
    download_link = re.search("http://.*.jpg", download_link.group())
    if download_link is None:
        print("查找图片下载地址失败")
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


def main():
    response = requests.get(host_link + "/hqsb.html", headers=my_headers)

    # 这神奇的编码格式，折腾了半天，开始还以为是gb2312呢……
    # print(response.content.decode('GB18030'))

    newest_paper_date = re.search(r"\d{4}-\d{1,2}-\d{1,2}", response.text)
    print("最新的报纸日期是: " + newest_paper_date.group())
    print("今天的日期是: " + str(datetime.date.today()))
    print('是否继续 \033[4m%s\033[0mes Or \033[4m%s\033[0mo' % ('Y', 'N'))
    if control() is False:
        return

    if os.path.exists(base_location + str(datetime.date.today()) + ".pdf"):
        print("今日报纸已经下载")
        print('是否重新下载 \033[4m%s\033[0mes Or \033[4m%s\033[0mo' % ('Y', 'N'))
        if not control():
            return
        else:
            os.remove(base_location + str(datetime.date.today()) + ".pdf")

    if not os.path.exists(base_location + "tmp"):
        os.mkdir(base_location + "tmp")

    link = re.search(
        "/arc/jwbt/hqsb/\d{4}/\d{4}/\d*.html", response.text).group()
    big_link = host_link + link
    download_and_save(big_link, 1)

    for i in range(2, 17):
        suffix = "_" + str(i) + ".html"
        tmp_link = re.sub("\.html", suffix, big_link)
        # print(tmp_link)
        download_and_save(tmp_link, i)

    # # 将所有图片转为pdf
    convert_cmd = "convert " + base_location + "tmp/" + \
        "*.jpg " + base_location + "`date +%Y-%m-%d`.pdf"
    # print(convert_cmd)
    print("converting jpeg to pdf")
    os.system(convert_cmd)
    # 删除图片缓存
    shutil.rmtree(base_location + "tmp")
    print("tmp files has been deleted")


if __name__ == "__main__":
    main()
