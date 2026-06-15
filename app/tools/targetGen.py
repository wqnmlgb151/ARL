#!/usr/bin/python3.6

from urllib.parse import urlparse
import sys
import os

# 导入统一的工具函数
try:
    from app.utils.file_utils import load_file
    from app.utils.url import normal_url
except ImportError:
    # 如果无法导入app模块，提供本地实现
    def normal_url(url):
        scheme_map = {
            'http': 80,
            "https": 443
        }
        o = urlparse(url)

        scheme = o.scheme
        hostname = o.hostname
        path = o.path
        port = o.port
        if scheme not in scheme_map:
            return

        if o.path == "":
            path = "/"

        if port == scheme_map[o.scheme] or port is None:
            ret_url = "{}://{}{}".format(scheme, hostname, path)
        else:
            ret_url = "{}://{}:{}{}".format(scheme, hostname, port, path)

        if o.query:
            ret_url = ret_url + "?" + o.query

        return ret_url


    def load_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()



def base_url(url):
    url = normal_url(url.strip())
    print(url)
    if not url:
        return

    if len(url) > 140:
        return
    o = urlparse(url)

    base = os.path.dirname(o.path)
    base = base.rstrip("/") + "/"

    ret = "{}://{}{}".format(o.scheme, o.netloc, base)

    return ret


def save_file(targets, output_path=None):
    """
    保存结果到文件

    Args:
        targets: 要保存的 URL 列表
        output_path: 输出文件路径，默认使用 sys.argv[3]
    """
    if output_path is None:
        output_path = sys.argv[3]

    # 确保输出目录存在
    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "a", encoding="utf-8") as f:
        for url in targets:
            f.write(url + "\n")



def main():
    targets = list(set(load_file(sys.argv[1])))
    dicts = list(set(load_file(sys.argv[2])))

    results = []
    for target in targets:
        target = target.strip()
        for dict in dicts:
            dict = dict.strip()
            url = "{}/{}".format(target, dict)
            results.append(url)


    print("gen target {}".format(len(results)))

    save_file(results)

if __name__ == '__main__':
    main()

