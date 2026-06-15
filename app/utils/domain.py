import tld
from app.config import Config

blackdomain_list = None
blackhexie_list = None


def check_domain_black(domain):
    """检查域名是否在黑名单中（已禁用，返回False允许扫描所有域名）"""
    # 黑名单功能已禁用，允许扫描所有域名
    return False


def is_forbidden_domain(domain):
    """检查域名是否在禁止列表中（已禁用，返回False允许扫描所有域名）"""
    # 禁止域名功能已禁用，允许扫描所有域名
    return False


def is_valid_domain(domain):
    from app.utils import domain_parsed
    if "." not in domain:
        return False

    invalid_chars = "!@#$%&*():_\\"
    for c in invalid_chars:
        if c in domain:
            return False

    # 不允许下发特殊二级域名
    if domain in ["com.cn", "gov.cn", "edu.cn"]:
        return False

    if domain_parsed(domain):
        return True

    return False


def is_valid_fuzz_domain(domain):
    from app.utils import domain_parsed
    if "{fuzz}" not in domain:
        return False

    domain = domain.replace("{fuzz}", "12fuzz12")
    parsed = domain_parsed(domain)
    if not parsed:
        return False

    if "12fuzz12" in parsed['fld']:
        return False

    return True


def is_in_scope(src_domain, target_domain):
    from app.utils import get_fld

    fld1 = get_fld(src_domain)
    fld2 = get_fld(target_domain)

    if not fld1 or not fld2:
        return False

    if fld1 != fld2:
        return False

    if src_domain == target_domain:
        return True

    return src_domain.endswith("."+target_domain)


def is_in_scopes(domain, scopes):
    for target_scope in scopes:
        if is_in_scope(domain, target_scope):
            return True

    return False


def cut_first_name(domain):
    """将子域名剔除前面一节名称"""
    domain_parts, non_zero_i, _ = tld.utils.process_url(domain, fix_protocol=True, fail_silently=True)
    if not domain_parts:
        return

    if non_zero_i == 1:
        return

    item = ".".join(domain_parts[1:])
    return item
