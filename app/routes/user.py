from flask import request
from app.utils.sanitizer import sanitize_input
from flask_restx import fields, Namespace
from app.utils import get_logger
from app.utils.rate_limiter import rate_limit_by_name
from app import utils
from . import  ARLResource
from app import modules

ns = Namespace('user', description="管理员登录认证")

logger = get_logger()



login_fields = ns.model('LoginARL', {
    'username': fields.String(required=True, description="用户名"),
    'password': fields.String(required=True, description="密码"),
})


@ns.route('/login')
class LoginARL(ARLResource):

    @ns.expect(login_fields)
    @rate_limit_by_name("login")
    def post(self):
        """
        用户登录
        """
        args = self.parse_args(login_fields)


        return build_data(utils.user_login(**args))




@ns.route('/logout')
class LogoutARL(ARLResource):

    def get(self):
        """
        用户退出
        """
        token = request.headers.get("Token")
        utils.user_logout(token)

        return build_data({})


change_pass_fields = ns.model('ChangePassARL', {
    'old_password': fields.String(required=True, description="旧密码"),
    'new_password': fields.String(required=True, description="新密码"),
    'check_password': fields.String(required=True, description="确认密码"),
})


@ns.route('/change_pass')
class ChangePassARL(ARLResource):
    @ns.expect(change_pass_fields)
    def post(self):
        """
        密码修改
        """
        args = self.parse_args(change_pass_fields)
        ret = {
            "message": "success",
            "code": 200,
            "data": {}
        }
        token = request.headers.get("Token")

        if args["new_password"] != args["check_password"]:
            ret["code"] = 301
            ret["message"] = "新密码和确定密码不一致"
            return ret

        if not args["new_password"]:
            ret["code"] = 302
            ret["message"] = "新密码不能为空"
            return ret

        if utils.change_pass(token, args["old_password"], args["new_password"]):
            utils.user_logout(token)
        else:
            ret["message"] = "旧密码错误"
            ret["code"] = 303

        return ret


reset_pass_fields = ns.model('ResetPassARL', {
    'username': fields.String(required=True, description="用户名"),
    'new_password': fields.String(required=True, description="新密码"),
    'check_password': fields.String(required=True, description="确认密码"),
})


@ns.route('/reset_pass')
class ResetPassARL(ARLResource):
    @ns.expect(reset_pass_fields)
    def post(self):
        """
        密码重置（用于 MD5 迁移）
        """
        args = self.parse_args(reset_pass_fields)
        ret = {
            "message": "success",
            "code": 200,
            "data": {}
        }

        # 验证两次密码是否一致
        if args["new_password"] != args["check_password"]:
            ret["code"] = 301
            ret["message"] = "新密码和确认密码不一致"
            return ret

        if not args["new_password"]:
            ret["code"] = 302
            ret["message"] = "新密码不能为空"
            return ret

        # 重置密码
        if utils.reset_password(args["username"], args["new_password"]):
            ret["message"] = "密码重置成功"
        else:
            ret["code"] = 303
            ret["message"] = "密码重置失败（用户不存在或密码强度不足）"

        return ret


def build_data(data):
    ret = {
        "message": "success",
        "code": 200,
        "data": {}
    }

    # 检测是否需要密码重置
    if isinstance(data, dict) and data.get("password_reset_required"):
        ret["code"] = 403
        ret["message"] = "密码需要重置，请使用 /api/user/reset_pass 接口"
        ret["data"] = {"username": data.get("username")}
        return ret

    if data:
        ret["data"] = data
    else:
        ret["code"] = 401

    return ret


