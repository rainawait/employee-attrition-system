"""
操作日志工具函数 —— 一行代码记录日志
用法: from utils.logger import log_action
      log_action('删除员工', '员工编号1001', '姓名：张三，部门：研发部')
"""
from flask import session, request, has_request_context
from db_model import db, OperationLog


def log_action(action, target='', detail=''):
    """
    记录操作日志。
    自动从 session 获取 user_id/username，从 request 获取 IP。
    若不在请求上下文中则静默跳过。
    """
    if not has_request_context():
        return  # 非请求环境（如命令行、定时任务）静默跳过

    try:
        user_id = session.get('user_id')
        username = session.get('username', '')
        ip = request.remote_addr or ''

        log_entry = OperationLog(
            user_id=user_id,
            username=username,
            action=action,
            target=str(target),
            detail=str(detail),
            ip=ip,
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception:
        # 日志记录失败不应影响主业务流程
        pass
