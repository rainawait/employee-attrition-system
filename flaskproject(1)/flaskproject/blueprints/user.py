from flask import Blueprint, render_template, request, jsonify, session, send_file
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from db_model import db, User
import os
import uuid
from PIL import Image
import pandas as pd
from io import BytesIO

user_bp = Blueprint('user', __name__, url_prefix='/user')


# ===================== 权限装饰器 =====================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"code": 401, "msg": "请先登录"}), 401
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"code": 401, "msg": "请先登录"}), 401
        if session.get('role') != 'admin':
            return jsonify({"code": 403, "msg": "权限不足，仅管理员可操作"}), 403
        return f(*args, **kwargs)

    return wrapper


# ===================== 页面路由 =====================
@user_bp.route('/list')
@login_required
def user_list():
    if session.get('role') != 'admin':
        return render_template("home.html")
    return render_template("user/list.html")


@user_bp.route('/profile')
@login_required
def profile_page():
    return render_template("user/profile.html")


# ===================== API接口 =====================

# 1. 用户分页列表
@user_bp.route('/api/users')
@admin_required
def api_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()

    query = User.query
    if keyword:
        query = query.filter(User.username.like(f'%{keyword}%') | User.real_name.like(f'%{keyword}%'))
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=limit, error_out=False)
    user_list = []
    for u in pagination.items:
        avatar = u.avatar or ''
        if avatar and not avatar.startswith('/'):
            avatar = '/' + avatar
        user_list.append({
            'id': u.id,
            'username': u.username,
            'real_name': u.real_name or '',
            'email': u.email or '',
            'phone': u.phone or '',
            'department': u.department or '',
            'avatar': avatar,
            'role': u.role,
            'status': u.status,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else '',
            'updated_at': u.updated_at.strftime('%Y-%m-%d %H:%M') if u.updated_at else ''
        })
    return jsonify({"code": 0, "count": pagination.total, "data": user_list})


# 2. 新增用户
@user_bp.route('/api/add', methods=['POST'])
@admin_required
def add_user():
    try:
        data = request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        real_name = data.get('real_name', '').strip()

        if not username or not password or not real_name:
            return jsonify({"code": 400, "msg": "用户名、密码、真实姓名不能为空"}), 400
        if len(password) < 6:
            return jsonify({"code": 400, "msg": "密码长度不能少于6位"}), 400

        email = data.get('email', '').strip()
        if email and '@' not in email:
            return jsonify({"code": 400, "msg": "邮箱格式不正确"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"code": 400, "msg": "用户名已存在"}), 400

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            real_name=real_name,
            email=email,
            phone=data.get('phone', ''),
            department=data.get('department', ''),
            avatar='',
            role='user',
            status='active'
        )
        db.session.add(new_user)
        db.session.commit()
        from utils.logger import log_action
        log_action('创建用户', username, f'姓名：{real_name}, 角色：user')
        return jsonify({"code": 0, "msg": "用户添加成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"添加失败：{str(e)}"}), 500


# 3. 编辑用户
@user_bp.route('/api/edit', methods=['POST'])
@login_required
def edit_user():
    try:
        data = request.form
        target_id = data.get('user_id', type=int)
        if not target_id:
            return jsonify({"code": 400, "msg": "参数缺失"}), 400

        current_id = session['user_id']
        is_admin = session.get('role') == 'admin'
        if not is_admin and target_id != current_id:
            return jsonify({"code": 403, "msg": "只能编辑自己的信息"}), 403

        user = User.query.get(target_id)
        if not user:
            return jsonify({"code": 404, "msg": "用户不存在"}), 404

        if is_admin:
            user.real_name = data.get('real_name', user.real_name)
            user.email = data.get('email', user.email)
            user.phone = data.get('phone', user.phone)
            user.department = data.get('department', user.department)
            user.role = data.get('role', user.role)
            user.status = data.get('status', user.status)
        else:
            user.real_name = data.get('real_name', user.real_name)
            user.email = data.get('email', user.email)
            user.phone = data.get('phone', user.phone)

        db.session.commit()
        return jsonify({"code": 0, "msg": "信息修改成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"修改失败：{str(e)}"}), 500


# 4. 删除用户
@user_bp.route('/api/delete', methods=['POST'])
@admin_required
def delete_user():
    try:
        target_id = request.form.get('user_id', type=int)
        if not target_id:
            return jsonify({"code": 400, "msg": "参数缺失"}), 400
        if target_id == session['user_id']:
            return jsonify({"code": 400, "msg": "不能删除自己的账户"}), 400

        user = User.query.get(target_id)
        if not user:
            return jsonify({"code": 404, "msg": "用户不存在"}), 404

        # 删除头像文件
        if user.avatar:
            file_path = user.avatar.lstrip('/')
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(user)
        db.session.commit()
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500


# 5. 用户详情
@user_bp.route('/api/detail/<int:user_id>')
@login_required
def user_detail(user_id):
    is_admin = session.get('role') == 'admin'
    if not is_admin and user_id != session['user_id']:
        return jsonify({"code": 403, "msg": "仅可查看自己的信息"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    avatar = user.avatar or ''
    if avatar and not avatar.startswith('/'):
        avatar = '/' + avatar

    return jsonify({
        "code": 0,
        "data": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name or '',
            "email": user.email or '',
            "phone": user.phone or '',
            "department": user.department or '',
            "avatar": avatar,
            "role": user.role,
            "status": user.status,
            "created_at": user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else '',
            "updated_at": user.updated_at.strftime('%Y-%m-%d %H:%M') if user.updated_at else ''
        }
    })


# 6. 重置密码
@user_bp.route('/api/reset-password', methods=['POST'])
@admin_required
def reset_password():
    try:
        target_id = request.form.get('user_id', type=int)
        new_pwd = request.form.get('new_password', '').strip()
        if not target_id or not new_pwd:
            return jsonify({"code": 400, "msg": "参数缺失"}), 400
        if len(new_pwd) < 6:
            return jsonify({"code": 400, "msg": "新密码长度不能少于6位"}), 400

        user = User.query.get(target_id)
        if not user:
            return jsonify({"code": 404, "msg": "目标用户不存在"}), 404

        user.password = generate_password_hash(new_pwd)
        db.session.commit()
        return jsonify({"code": 0, "msg": "密码重置成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"重置失败：{str(e)}"}), 500


# 7. 批量启用/禁用
@user_bp.route('/api/batch-status', methods=['POST'])
@admin_required
def batch_status():
    try:
        ids_str = request.form.get('user_ids', '').strip()
        status = request.form.get('status', '').strip()
        if not ids_str or status not in ['active', 'disabled']:
            return jsonify({"code": 400, "msg": "参数错误"}), 400

        id_list = [int(x) for x in ids_str.split(',') if x.strip()]
        current_id = session['user_id']
        if current_id in id_list:
            return jsonify({"code": 400, "msg": "不能修改自己的状态"}), 400

        count = 0
        for uid in id_list:
            user = User.query.get(uid)
            if user:
                user.status = status
                count += 1
        db.session.commit()
        return jsonify({"code": 0, "msg": f"成功更新{count}个用户", "count": count})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"批量操作失败：{str(e)}"}), 500


# 8. 获取当前登录用户信息
@user_bp.route('/api/profile')
@login_required
def get_profile():
    user = User.query.get(session['user_id'])
    avatar = user.avatar or ''
    if avatar and not avatar.startswith('/'):
        avatar = '/' + avatar
    return jsonify({
        "code": 0,
        "data": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name or '',
            "email": user.email or '',
            "phone": user.phone or '',
            "department": user.department or '',
            "avatar": avatar,
            "role": user.role,
            "status": user.status,
            "created_at": user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else ''
        }
    })


# 9. 修改个人密码
@user_bp.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.form
        old_pwd = data.get('old_password', '')
        new_pwd = data.get('new_password', '')
        confirm_pwd = data.get('confirm_password', '')

        if not old_pwd or not new_pwd or not confirm_pwd:
            return jsonify({"code": 400, "msg": "请填写完整密码信息"}), 400
        if new_pwd != confirm_pwd:
            return jsonify({"code": 400, "msg": "两次新密码不一致"}), 400
        if len(new_pwd) < 6:
            return jsonify({"code": 400, "msg": "新密码长度不能少于6位"}), 400

        user = User.query.get(session['user_id'])
        if not check_password_hash(user.password, old_pwd):
            return jsonify({"code": 400, "msg": "原密码错误"}), 400

        user.password = generate_password_hash(new_pwd)
        db.session.commit()
        from utils.logger import log_action
        log_action('修改密码', user.username, '密码已更新，需重新登录')
        session.clear()
        return jsonify({"code": 0, "msg": "密码修改成功，请重新登录"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"修改失败：{str(e)}"}), 500


# 10. 头像上传接口（核心修复：存储站点绝对路径）
@user_bp.route('/api/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get("avatar_file")
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404
    if not file:
        return jsonify({"code": 400, "msg": "请选择图片文件"}), 400

    filename = file.filename
    if '.' not in filename:
        return jsonify({"code": 400, "msg": "文件格式不支持"}), 400
    ext = filename.rsplit('.', 1)[-1].lower()
    allow_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if ext not in allow_ext:
        return jsonify({"code": 400, "msg": "仅支持 png / jpg / jpeg / gif / webp 图片，最大5M"}), 400

    new_filename = f"{uuid.uuid4()}.{ext}"
    save_dir = "static/avatar"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, new_filename)
    file.save(save_path)

    # 生成200*200缩略图
    img = Image.open(save_path)
    img.thumbnail((200, 200))
    img.save(save_path)

    # 删除旧头像（URL路径转本地文件路径）
    old_avatar_url = user.avatar
    if old_avatar_url:
        old_file_path = old_avatar_url.lstrip('/')
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    # 存储站点根路径，前端直接访问不会404
    user.avatar = f"/static/avatar/{new_filename}"
    db.session.commit()

    return jsonify({
        "code": 0,
        "msg": "头像上传成功",
        "avatar_url": user.avatar
    })


# 11. 用户Excel导出接口
@user_bp.route('/api/export_user')
@admin_required
def export_user():
    try:
        keyword = request.args.get("keyword", "").strip()
        role = request.args.get("role", "").strip()
        status = request.args.get("status", "").strip()
        select_ids = request.args.getlist("ids")

        query = User.query
        if keyword:
            query = query.filter(User.username.like(f"%{keyword}%") | User.real_name.like(f"%{keyword}%"))
        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)
        if select_ids:
            id_list = [int(i) for i in select_ids if i.isdigit()]
            if id_list:
                query = query.filter(User.id.in_(id_list))

        user_all = query.all()
        export_rows = []
        for u in user_all:
            export_rows.append({
                "用户ID": u.id,
                "登录账号": u.username,
                "真实姓名": u.real_name if u.real_name else "",
                "邮箱": u.email if u.email else "",
                "联系电话": u.phone if u.phone else "",
                "所属部门": u.department if u.department else "",
                "用户角色": "管理员" if u.role == "admin" else "普通用户",
                "账号状态": "正常启用" if u.status == "active" else "已禁用",
                "头像存储路径": u.avatar if u.avatar else "无",
                "创建时间": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
                "更新时间": u.updated_at.strftime("%Y-%m-%d %H:%M") if u.updated_at else "",
                "登录密码": "******"
            })

        df = pd.DataFrame(export_rows)
        output_stream = BytesIO()
        with pd.ExcelWriter(output_stream, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="用户列表")
        output_stream.seek(0)

        return send_file(
            output_stream,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="系统用户数据.xlsx"
        )
    except Exception as e:
        return jsonify({"code": 500, "msg": f"导出失败：{str(e)}"}), 500