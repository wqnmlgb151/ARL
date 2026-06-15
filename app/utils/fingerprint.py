import json
from app.config import Config

# 延迟导入，避免循环依赖
_logger = None
_conn_db = None
_load_file = None


def _get_logger():
    global _logger
    if _logger is None:
        from app.utils import get_logger as _get_logger_func
        _logger = _get_logger_func()
    return _logger


def _get_conn_db():
    global _conn_db
    if _conn_db is None:
        from app.utils import conn_db
        _conn_db = conn_db
    return _conn_db


def _get_load_file():
    global _load_file
    if _load_file is None:
        from app.utils.file_utils import load_file
        _load_file = load_file
    return _load_file

# 解析规则，只有或，且条件不能出现=

'''
html
title
headers
favicon_hash
'''

# 这个函数已经不用了


def parse_human_rule(rule):
    rule_map = {
        "html": [],
        "title": [],
        "headers": [],
        "favicon_hash": []
    }
    key_map = {
        "body": "html",
        "title": "title",
        "header": "headers",
        "icon_hash": "favicon_hash"
    }
    split_result = rule.split("||")
    empty_flag = True

    for item in split_result:
        key_value = item.split("=")
        key = key_value[0]
        key = key.strip()
        if len(key_value) == 2:
            if key not in key_map:
                _get_logger().info("{} 不在指定关键字中".format(key))
                continue

            value = key_value[1]
            value = value.strip()
            if len(value) <= 6:
                _get_logger().info("{} 长度少于7".format(value))
                continue

            if value[0] != '"' or value[-1] != '"':
                _get_logger().info("{} 没有在双引号内".format(value))
                continue

            empty_flag = False

            # 防御性转换成gbk
            value.encode("gbk")

            value = value[1:-1]
            if key == "icon_hash":
                value = int(value)

            rule_map[key_map[key]].append(value)

    if empty_flag:
        return None

    return rule_map


def transform_rule_map(rule):
    key_map = {
        "html": "body",
        "title": "title",
        "headers": "header",
        "favicon_hash": "icon_hash"
    }
    human_rule_list = []
    for key in rule:
        if key not in key_map:
            _get_logger().info("{} 不在指定关键字中".format(key))
            continue

        for rule_item in rule[key]:
            human_rule_list.append('{}="{}"'.format(key_map[key], rule_item))

    return " || ".join(human_rule_list)


web_app_rules = json.loads("\n".join(_get_load_file()(Config.web_app_rule)))


# 这里只是加载本地指纹规则
def load_fingerprint():
    items = []
    for rule in web_app_rules:
        new_rule = dict()
        new_rule["name"] = rule
        new_rule["rule"] = web_app_rules[rule]
        items.append(new_rule)
    return items


# 根据规则列表来获取应用名，单个规则字段是或的关系
def fetch_fingerprint(content, headers, title, favicon_hash, finger_list):
    finger_name_list = []

    for finger in finger_list:
        rule = finger["rule"]
        rule_name = finger["name"]
        match_flag = False
        for html in rule["html"]:
            if html.encode("utf-8") in content:
                finger_name_list.append(rule_name)
                match_flag = True
                break

            try:
                if html.encode("gbk") in content:
                    finger_name_list.append(rule_name)
                    match_flag = True
                    break
            except Exception as e:
                _get_logger().debug("error on fetch_fingerprint {} to gbk: {}".format(html, e))

        if match_flag:
            continue
        for header in rule["headers"]:
            if header in headers:
                finger_name_list.append(rule_name)
                match_flag = True
                break

        if match_flag:
            continue
        for rule_title in rule["title"]:
            if rule_title in title:
                finger_name_list.append(rule_name)
                match_flag = True
                break

        if match_flag:
            continue
        if isinstance(rule.get("favicon_hash"), list):
            for rule_hash in rule["favicon_hash"]:
                if rule_hash == favicon_hash:
                    finger_name_list.append(rule_name)
                    break

    return finger_name_list
