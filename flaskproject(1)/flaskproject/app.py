import os
import random
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db_model import db, User, EmployeeBase, JobDetail, AttritionRisk

# ========== 1. 先创建 Flask app 实例 ==========
app = Flask(__name__)

# 配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key_2026_flask_login'

db.init_app(app)

# ========== 2. 导入蓝图（必须在 app 创建之后） ==========
from blueprints.employee import employee_bp
from blueprints.user import user_bp
from blueprints.dashboard import dashboard_bp
from blueprints.predict import predict_bp   # 预测蓝图

# ========== 3. 注册蓝图 ==========
app.register_blueprint(employee_bp)
app.register_blueprint(user_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(predict_bp)

# ========== 4. 初始化数据库与数据 ==========
with app.app_context():
    db.create_all()

    # 管理员账号
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        hash_pwd = generate_password_hash("123456")
        new_admin = User(
            username="admin",
            password=hash_pwd,
            real_name="系统管理员",
            role="admin",
            status="active"
        )
        db.session.add(new_admin)
        db.session.commit()
        print("[OK] 管理员账号初始化完成：admin / 123456")
    else:
        if not admin_user.role:
            admin_user.role = 'admin'
            admin_user.status = 'active'
            db.session.commit()

    # 导入员工数据（如果表为空）
    csv_path = "static/WA_Fn-UseC_-HR-Employee-Attrition.csv"
    if os.path.exists(csv_path) and EmployeeBase.query.count() == 0:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        base_cols = ['EmployeeNumber', 'Age', 'Gender', 'MaritalStatus',
                     'EducationField', 'Department', 'DistanceFromHome']
        df_base = df[base_cols].copy()
        job_cols = ['EmployeeNumber', 'JobRole', 'JobLevel', 'MonthlyIncome',
                    'NumCompaniesWorked', 'TotalWorkingYears',
                    'YearsInCurrentRole', 'YearsSinceLastPromotion', 'YearsWithCurrManager']
        df_job = df[job_cols].copy()
        risk_cols = ['EmployeeNumber', 'Attrition', 'OverTime',
                     'WorkLifeBalance', 'JobSatisfaction',
                     'EnvironmentSatisfaction', 'JobInvolvement', 'RelationshipSatisfaction',
                     'YearsAtCompany']
        df_risk = df[risk_cols].copy()
        # 为每条记录分配随机日期（2024-01 ~ 2026-06），支持按时间范围筛选
        base_date = datetime(2024, 1, 1)
        df_base['record_date'] = [base_date + timedelta(days=random.randint(0, 900))
                                  for _ in range(len(df_base))]
        df_base.to_sql('employee_base', db.engine, if_exists='replace', index=False)
        df_job.to_sql('job_detail', db.engine, if_exists='replace', index=False)
        df_risk.to_sql('attrition_risk', db.engine, if_exists='replace', index=False)
        print("[OK] 员工数据初始化完成")

# ===================== 页面路由 =====================
@app.route('/')
def index():
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    req_data = request.get_json(silent=True)
    if not req_data:
        return jsonify({"code": 1, "msg": "请求数据格式错误"})
    username = req_data.get("username")
    password = req_data.get("password")
    repassword = req_data.get("repassword")
    if not username or not password or not repassword:
        return jsonify({"code": 1, "msg": "用户名、密码不能为空"})
    if password != repassword:
        return jsonify({"code": 1, "msg": "两次输入密码不一致"})
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 1, "msg": "该用户名已被注册，请更换"})
    secure_pwd = generate_password_hash(password)
    new_user = User(username=username, password=secure_pwd, role='user', status='active')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"code": 0, "msg": "注册成功！即将跳转登录"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"code": 400, "msg": "未收到请求数据"})
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名或密码不能为空"})
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        from utils.logger import log_action
        log_action('登录失败', username or '', f'密码错误或用户不存在')
        return jsonify({"code": 401, "msg": "用户名或密码错误"})
    if user.status == 'disabled':
        return jsonify({"code": 403, "msg": "账号已被禁用，请联系管理员"})
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    from utils.logger import log_action
    log_action('登录成功', username, f'角色: {user.role}')
    return jsonify({"code": 200, "msg": "登录成功"})

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template("home.html",
                           username=session.get("username"),
                           role=session.get("role"))

@app.route('/report/history')
def report_history():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('report_history.html')


@app.route('/report/compare')
def report_compare():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('compare.html')


@app.route('/log/list')
def log_list():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('log_list.html')


@app.route('/log/stats')
def log_stats_page():
    """今日日志统计可视化页 (3.5)"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('log_stats.html')


@app.route('/log/overview')
def log_overview_page():
    """日志系统架构总览页 (3.1+3.2)"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('log_overview.html')


@app.route('/log/my')
def my_logs_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('user/my_logs.html')


@app.route('/log/api/my')
def api_my_logs():
    """我的操作记录 API —— 仅返回当前用户的日志"""
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '请先登录'})
    try:
        from db_model import OperationLog
        from datetime import datetime as dt

        action = request.args.get('action', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 15))

        query = OperationLog.query.filter(
            OperationLog.user_id == session['user_id']
        )
        if action:
            query = query.filter(OperationLog.action == action)
        if start_date:
            query = query.filter(OperationLog.created_at >= dt.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(OperationLog.created_at <= dt.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

        total = query.count()
        logs = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        data = [{
            'id': log.id,
            'action': log.action,
            'target': log.target or '',
            'detail': log.detail or '',
            'detail_short': (log.detail or '')[:50] + ('...' if len(log.detail or '') > 50 else ''),
            'ip': log.ip or '',
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
        } for log in logs]

        return jsonify({'code': 0, 'data': data, 'count': total})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@app.route('/log/api/stats/today')
def api_log_stats_today():
    """今日操作统计 —— 总次数 + 各类型分布"""
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '请先登录'})
    try:
        from db_model import OperationLog
        from datetime import datetime as dt
        from sqlalchemy import func

        today_start = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)

        query = OperationLog.query.filter(OperationLog.created_at >= today_start)
        total = query.count()

        type_counts = db.session.query(
            OperationLog.action, func.count(OperationLog.id)
        ).filter(
            OperationLog.created_at >= today_start
        ).group_by(OperationLog.action).order_by(func.count(OperationLog.id).desc()).all()

        return jsonify({
            'code': 0,
            'data': {
                'today_total': total,
                'type_distribution': [{'action': a, 'count': c} for a, c in type_counts]
            }
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@app.route('/log/api/clean', methods=['POST'])
def api_log_clean():
    """清理 90 天前的旧日志，返回删除条数"""
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '请先登录'})
    if session.get('role') != 'admin':
        return jsonify({'code': 403, 'msg': '仅管理员可操作'})
    try:
        from db_model import OperationLog
        from datetime import datetime as dt, timedelta

        cutoff = dt.now() - timedelta(days=90)
        count = OperationLog.query.filter(OperationLog.created_at < cutoff).delete()
        db.session.commit()
        return jsonify({'code': 0, 'msg': f'成功清理 {count} 条旧日志', 'deleted': count})
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@app.route('/logout')
def logout():
    from utils.logger import log_action
    log_action('退出登录', '', '')
    session.clear()
    return render_template("login.html")

if __name__ == '__main__':
    app.run(debug=True)