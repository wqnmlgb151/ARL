import os
import yaml
import sys

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    CELERY_BROKER_URL = "amqp://arl:arlpassword@localhost:5672/arlv2host"

    MONGO_DB = 'ARLV2'
    MONGO_URL = 'mongodb://127.0.0.1:27017/'

    TMP_PATH = os.path.join(basedir, 'tmp')
    if not os.path.exists(TMP_PATH):
        os.mkdir(TMP_PATH)
    MASSDNS_BIN = os.path.join(basedir, 'tools/massdns')
    SCREENSHOT_JS = os.path.join(basedir, 'tools/screenshot.js')
    SCREENSHOT_DIR = os.path.join(basedir, 'tmp_screenshot')
    SCREENSHOT_FAIL_IMG = os.path.join(basedir, 'dicts/noscreenshot.jpg')
    DRIVER_JS = os.path.join(basedir, 'tools/driver.js')

    DOMAIN_DICT_TEST = os.path.join(basedir, 'dicts/domain_dict_test.txt')
    DOMAIN_DICT_2W = os.path.join(basedir, 'dicts/domain_2w.txt')
    DNS_SERVER = os.path.join(basedir, 'dicts/dnsserver.txt')

    CDN_JSON_PATH = os.path.join(basedir, 'dicts/cdn_info.json')

    # WebInfoHunter 规则文件
    WIH_RULE_PATH = os.path.join(basedir, "dicts/wih_rules.yml")

    black_domain_path = os.path.join(basedir, 'dicts/blackdomain.txt')
    black_hexie_path = os.path.join(basedir, 'dicts/blackhexie.txt')
    black_asset_site = os.path.join(basedir, 'dicts/black_asset_site.txt')
    altdns_dict_path = os.path.join(basedir, 'dicts/altdnsdict.txt')

    web_app_rule = os.path.join(basedir, 'dicts/webapp.json')
    dns_query_plugin_path = os.path.join(basedir, 'services/dns_query_plugin')

    # 端口列表（数据文件位于 app/dicts/ports/，惰性加载）
    PORTS_DIR = os.path.join(basedir, 'dicts', 'ports')
    TOP_1000_PATH = os.path.join(PORTS_DIR, 'top_1000.txt')
    TOP_100_PATH = os.path.join(PORTS_DIR, 'top_100.txt')
    TOP_10_PATH = os.path.join(PORTS_DIR, 'top_10.txt')

    # 以下默认值在模块级别通过 _load_port_defaults() 从文件加载
    TOP_1000 = ""
    TOP_100 = ""
    TOP_10 = ""

    FOFA_KEY = ""
    FOFA_URL = "https://fofa.info"
    FOFA_MAX_PAGE = 5      # 最大查询页数
    FOFA_PAGE_SIZE = 2000  # 每页2000条

    AUTH = False
    API_KEY = ""

    # SSRF 防护：禁止的 IP 范围（内网和保留地址）
    BLACK_IPS = [
        "127.0.0.0/8",      # Loopback
        "10.0.0.0/8",       # Private Class A
        "172.16.0.0/12",    # Private Class B
        "192.168.0.0/16",   # Private Class C
        "169.254.0.0/16",   # Link-local
        "0.0.0.0/8",        # Invalid/broadcast
        "224.0.0.0/4",      # Multicast
        "240.0.0.0/4",      # Reserved
    ]

    GEOIP_ASN = ""
    GEOIP_CITY = ""

    FILE_LEAK_TOP_2k = os.path.join(basedir, 'dicts/file_top_2000.txt')
    FILE_LEAK_TOP_200 = os.path.join(basedir, 'dicts/file_top_200.txt')

    DOMAIN_MAX_LEN = 25  # 不包括下发的目标域名长度，

    DINGDING_SECRET = ""
    DINGDING_ACCESS_TOKEN = ""

    FEISHU_WEBHOOK = ""
    FEISHU_SECRET = ""

    WX_WORK_WEBHOOK = ""

    EMAIL_HOST = ""
    EMAIL_PORT = ""
    EMAIL_USERNAME = ""
    EMAIL_PASSWORD = ""
    EMAIL_TO = ""
    # FORBIDDEN_DOMAINS = ["gov.cn", "edu.cn", "org.cn"]
    FORBIDDEN_DOMAINS = []

    GITHUB_TOKEN = ""
    GITHUB_HASH_FILE = os.path.join(TMP_PATH, 'github.hash')

    # 域名爆破并发数
    DOMAIN_BRUTE_CONCURRENT = 300
    # 组合生成的域名爆破并发数
    ALT_DNS_CONCURRENT = 1500

    # 代理地址
    PROXY_URL = ""

    QUERY_PLUGIN_CONFIG = dict()

    WEB_HOOK_URL = ""
    WEB_HOOK_TOKEN = ""

    # Redis 缓存配置（可选）
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = ""

    AUTH_WARNING = "API authentication is disabled. This is a security risk in production."
    _initialized = False

    @classmethod
    def init_app(cls, config_path: str = None) -> None:
        """
        初始化应用配置（幂等调用）

        由于配置在模块导入时已从 config.yaml 加载，
        此处仅标记已初始化防止重复初始化。

        Args:
            config_path: 配置文件路径（已不再需要，保留用于 API 兼容）
        """
        if cls._initialized:
            return
        cls._initialized = True


def _load_port_file(path):
    """从数据文件加载端口列表"""
    with open(path, 'r') as f:
        return f.read().strip()


# 从数据文件加载默认端口列表
try:
    Config.TOP_1000 = _load_port_file(Config.TOP_1000_PATH)
    Config.TOP_100 = _load_port_file(Config.TOP_100_PATH)
    Config.TOP_10 = _load_port_file(Config.TOP_10_PATH)
except FileNotFoundError as e:
    import logging
    logging.getLogger(__name__).error(f"Port data file not found: {e}")
    sys.exit(1)


try:
    with open(os.path.join(basedir, 'config.yaml'), encoding='utf-8') as f:
        y = yaml.load(f, Loader=yaml.SafeLoader)

    Config.MONGO_URL = y["MONGO"]["URI"]
    Config.MONGO_DB = y["MONGO"]["DB"]

    Config.CELERY_BROKER_URL = y["CELERY"]["BROKER_URL"]

    # *** Fofa 配置 ***
    Config.FOFA_KEY = y["FOFA"]["KEY"]
    if y["FOFA"].get("URL"):
        Config.FOFA_URL = y["FOFA"]["URL"]

    if y["FOFA"].get("MAX_PAGE"):
        Config.FOFA_MAX_PAGE = y["FOFA"]["MAX_PAGE"]

    if y["FOFA"].get("PAGE_SIZE"):
        Config.FOFA_PAGE_SIZE = y["FOFA"]["PAGE_SIZE"]

    # *** GEOIP 配置 ***
    Config.GEOIP_CITY = y["GEOIP"]["CITY"]
    Config.GEOIP_ASN = y["GEOIP"]["ASN"]

    Config.AUTH = y["ARL"]["AUTH"]
    Config.API_KEY = y["ARL"]["API_KEY"]
    Config.BLACK_IPS = y["ARL"]["BLACK_IPS"]

    # *** TOP 10 端口设置 ***
    if y["ARL"].get("PORT_TOP_10"):
        Config.TOP_10 = y["ARL"]["PORT_TOP_10"]

    # *** 文件泄漏字典 ***
    if y["ARL"].get("FILE_LEAK_DICT"):
        file_leak_dict = y["ARL"]["FILE_LEAK_DICT"]
        if os.path.isfile(file_leak_dict):
            Config.FILE_LEAK_TOP_2k = file_leak_dict
        else:
            print("Warning {} is not file".format(file_leak_dict))

    # *** 域名爆破字典 ***
    if y["ARL"].get("DOMAIN_DICT"):
        domain_dict = y["ARL"]["DOMAIN_DICT"]
        if os.path.isfile(domain_dict):
            Config.DOMAIN_DICT_2W = domain_dict
        else:
            print("Warning {} is not file".format(domain_dict))

    # *** 禁止域名配置 ***
    forbidden_domains = y["ARL"].get("FORBIDDEN_DOMAINS")
    if forbidden_domains is None:
        pass
    else:
        Config.FORBIDDEN_DOMAINS = []
        if not isinstance(forbidden_domains, list):
            print("arl.forbidden_domains is not list")
            sys.exit(-1)
        elif forbidden_domains:
            Config.FORBIDDEN_DOMAINS = forbidden_domains

    # *** 钉钉配置 ***
    if y.get("DINGDING"):
        if y["DINGDING"].get("SECRET"):
            Config.DINGDING_SECRET = y["DINGDING"]["SECRET"]

        if y["DINGDING"].get("ACCESS_TOKEN"):
            Config.DINGDING_ACCESS_TOKEN = y["DINGDING"]["ACCESS_TOKEN"]

    # *** 邮箱配置 ***
    if y.get("EMAIL"):
        if y["EMAIL"].get("HOST"):
            Config.EMAIL_HOST = y["EMAIL"]["HOST"]

        if y["EMAIL"].get("PORT"):
            Config.EMAIL_PORT = int(y["EMAIL"]["PORT"])

        if y["EMAIL"].get("USERNAME"):
            Config.EMAIL_USERNAME = y["EMAIL"]["USERNAME"]

        if y["EMAIL"].get("PASSWORD"):
            Config.EMAIL_PASSWORD = y["EMAIL"]["PASSWORD"]

        if y["EMAIL"].get("TO"):
            Config.EMAIL_TO = y["EMAIL"]["TO"]

    # *** GITHUB TOKEN 配置 ***
    if y.get("GITHUB"):
        if y["GITHUB"].get("TOKEN"):
            Config.GITHUB_TOKEN = y["GITHUB"]["TOKEN"]

    # *** 域名爆破并发数 ***
    domain_concurrent = y["ARL"].get("DOMAIN_BRUTE_CONCURRENT")
    if domain_concurrent:
        Config.DOMAIN_BRUTE_CONCURRENT = int(domain_concurrent)

    # *** 组合生成的域名爆破并发数 ***
    alt_dns_concurrent = y["ARL"].get("ALT_DNS_CONCURRENT")
    if alt_dns_concurrent:
        Config.ALT_DNS_CONCURRENT = int(alt_dns_concurrent)

    # *** 代理配置 ***
    if y.get("PROXY"):
        if y["PROXY"].get("HTTP_URL"):
            Config.PROXY_URL = y["PROXY"]["HTTP_URL"]

    # *** 域名查询插件配置 ***
    if y.get("QUERY_PLUGIN"):
        query_plugin_conf = y["QUERY_PLUGIN"]
        if isinstance(query_plugin_conf, dict):
            Config.QUERY_PLUGIN_CONFIG = query_plugin_conf

    # *** WEBHOOK 配置文件 ***
    if y.get("WEBHOOK"):
        if y["WEBHOOK"].get("URL"):
            Config.WEB_HOOK_URL = y["WEBHOOK"]["URL"]
        if y["WEBHOOK"].get("TOKEN"):
            Config.WEB_HOOK_TOKEN = y["WEBHOOK"]["TOKEN"]

    # *** 飞书消息推送配置 ***
    if y.get("FEISHU"):
        if y["FEISHU"].get("WEBHOOK_URL"):
            Config.FEISHU_WEBHOOK = y["FEISHU"]["WEBHOOK_URL"]
        if y["FEISHU"].get("SECRET"):
            Config.FEISHU_SECRET = y["FEISHU"]["SECRET"]

    # *** 企业微信推送配置 ***
    if y.get("WXWORK"):
        if y["WXWORK"].get("WEBHOOK_URL"):
            Config.WX_WORK_WEBHOOK = y["WXWORK"]["WEBHOOK_URL"]

    # *** Redis 缓存配置 ***
    if y.get("REDIS"):
        Config.REDIS_HOST = y["REDIS"].get("HOST", Config.REDIS_HOST)
        Config.REDIS_PORT = y["REDIS"].get("PORT", Config.REDIS_PORT)
        Config.REDIS_DB = y["REDIS"].get("DB", Config.REDIS_DB)
        Config.REDIS_PASSWORD = y["REDIS"].get("PASSWORD", Config.REDIS_PASSWORD)

    # 环境变量覆盖（Docker 兼容）
    Config.REDIS_HOST = os.getenv("REDIS_HOST", Config.REDIS_HOST)
    Config.REDIS_PORT = int(os.getenv("REDIS_PORT", Config.REDIS_PORT))
    Config.REDIS_DB = int(os.getenv("REDIS_DB", Config.REDIS_DB))
    Config.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", Config.REDIS_PASSWORD)

except FileNotFoundError:
    # Config file not found is a fatal error - fail fast
    print(f"Configuration file not found: {os.path.join(basedir, 'config.yaml')}")
    sys.exit(1)
except yaml.YAMLError as e:
    # YAML parsing error - fail fast with clear message
    print(f"Invalid YAML in config.yaml: {e}")
    sys.exit(1)
except KeyError as e:
    # Missing required config key
    print(f"Missing required configuration key: {e}")
    sys.exit(1)
except Exception as e:
    # Unexpected error - log full traceback before exiting
    import logging
    logging.getLogger(__name__).exception(f"Unexpected error loading config.yaml: {e}")
    sys.exit(1)
