"""数据看板蓝图 - 提供页面和API"""
import pandas as pd
from flask import Blueprint, render_template, jsonify, session, redirect, request
from db_model import db, EmployeeBase, JobDetail, AttritionRisk

dashboard_bp = Blueprint('dashboard', __name__)

def get_employee_df():
    try:
        results = db.session.query(
            EmployeeBase.EmployeeNumber,
            EmployeeBase.Age,
            EmployeeBase.Gender,
            EmployeeBase.Department,
            EmployeeBase.MaritalStatus,          # 新增婚姻状况
            JobDetail.JobRole,
            JobDetail.MonthlyIncome,
            AttritionRisk.Attrition,
            AttritionRisk.OverTime,
            AttritionRisk.WorkLifeBalance,
            AttritionRisk.JobSatisfaction,
            AttritionRisk.YearsAtCompany,
        ).outerjoin(
            JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        ).outerjoin(
            AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
        ).all()

        df = pd.DataFrame([{
            'EmployeeNumber': r.EmployeeNumber,
            'Age': r.Age,
            'Gender': r.Gender,
            'Department': r.Department,
            'MaritalStatus': r.MaritalStatus,
            'JobRole': r.JobRole,
            'MonthlyIncome': r.MonthlyIncome,
            'Attrition': r.Attrition,
            'OverTime': r.OverTime,
            'WorkLifeBalance': r.WorkLifeBalance,
            'JobSatisfaction': r.JobSatisfaction,
            'YearsAtCompany': r.YearsAtCompany,
        } for r in results])
        df['Attrition'] = df['Attrition'].map({'Yes': 1, 'No': 0}).fillna(0).astype(int)
        return df
    except Exception as e:
        print(f"❌ get_employee_df 错误: {e}")
        return pd.DataFrame()

@dashboard_bp.route('/welcome')
@dashboard_bp.route('/dashboard')
def index():
    # 导出截图时允许内部访问（带 token 参数）
    if request.args.get('token') == 'export_internal':
        return render_template('welcome.html',
                               username='数据看板',
                               role='admin',
                               export_mode=True)
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('welcome.html',
                           username=session.get('username', '用户'),
                           role=session.get('role', 'user'))

# ----- 总览卡片 -----
@dashboard_bp.route('/api/stats/overview')
def api_overview():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": {"total":0, "attrition_count":0, "active_count":0, "attrition_rate":0}})
        total = len(df)
        attrition_count = int(df['Attrition'].sum())
        active_count = total - attrition_count
        rate = round(attrition_count / total * 100, 2) if total else 0
        return jsonify({
            "code": 200,
            "data": {
                "total": total,
                "attrition_count": attrition_count,
                "active_count": active_count,
                "attrition_rate": rate
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 部门离职率（柱状图）-----
@dashboard_bp.route('/api/stats/department')
def api_department():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": {"departments": [], "rates": []}})
        df['Department'] = df['Department'].str.strip()
        grouped = df.groupby('Department').agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        grouped['rate'] = grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0,
            axis=1
        )
        grouped = grouped.sort_values('rate', ascending=False)
        return jsonify({
            "code": 200,
            "data": {
                "departments": grouped['Department'].tolist(),
                "rates": grouped['rate'].tolist()
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 岗位分布饼图 -----
@dashboard_bp.route('/api/stats/role')
def api_role():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": {"names": [], "counts": []}})
        attrition_df = df[df['Attrition'] == 1]
        role_counts = attrition_df['JobRole'].value_counts()
        return jsonify({
            "code": 200,
            "data": {
                "names": role_counts.index.tolist(),
                "counts": role_counts.values.tolist()
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 年龄段趋势折线图 -----
@dashboard_bp.route('/api/stats/age_trend')
def api_age_trend():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": {"age_groups": [], "rates": []}})
        df['age_group'] = pd.cut(
            df['Age'],
            bins=[18, 25, 30, 35, 40, 45, 50, 55, 60],
            labels=['18-25', '26-30', '31-35', '36-40', '41-45', '46-50', '51-55', '56-60'],
            right=False
        )
        grouped = df.groupby('age_group', observed=False).agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        grouped['rate'] = grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0,
            axis=1
        )
        return jsonify({
            "code": 200,
            "data": {
                "age_groups": grouped['age_group'].astype(str).tolist(),
                "rates": grouped['rate'].tolist()
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 工作年限折线图 -----
@dashboard_bp.route('/api/stats/year_trend')
def api_year_trend():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": {"year_groups": [], "rates": []}})
        df['year_group'] = pd.cut(
            df['YearsAtCompany'],
            bins=[0, 3, 6, 11, 16, 100],
            labels=['0-2', '3-5', '6-10', '11-15', '16+'],
            right=False
        )
        grouped = df.groupby('year_group', observed=False).agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        grouped['rate'] = grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0,
            axis=1
        )
        return jsonify({
            "code": 200,
            "data": {
                "year_groups": grouped['year_group'].astype(str).tolist(),
                "rates": grouped['rate'].tolist()
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 婚姻状况离职率（水平柱状图）----- 练习1
@dashboard_bp.route('/api/stats/marital')
def api_marital():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": {"statuses": [], "rates": []}})
        df['MaritalStatus'] = df['MaritalStatus'].str.strip()
        grouped = df.groupby('MaritalStatus').agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        grouped['rate'] = grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0,
            axis=1
        )
        grouped = grouped.sort_values('rate', ascending=False)
        return jsonify({
            "code": 200,
            "data": {
                "statuses": grouped['MaritalStatus'].tolist(),
                "rates": grouped['rate'].tolist()
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 月薪 vs 离职率散点图 ----- 练习4
@dashboard_bp.route('/api/stats/salary_scatter')
def api_salary_scatter():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": []})
        # 月薪分段
        df['salary_group'] = pd.cut(
            df['MonthlyIncome'],
            bins=[0, 3000, 6000, 9000, 12000, 15000, 20000, 30000],
            labels=['0-3k', '3-6k', '6-9k', '9-12k', '12-15k', '15-20k', '20k+'],
            right=False
        )
        grouped = df.groupby('salary_group', observed=False).agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        grouped['rate'] = grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0,
            axis=1
        )
        # 为散点图构造数据：x 用薪资段索引（或者数字），y 为离职率
        # 用每个段的中位数或直接使用分段标签的序号
        # 为了方便展示，我们用数值型 x（比如薪资段的中值）
        salary_mid = {
            '0-3k': 1500, '3-6k': 4500, '6-9k': 7500, '9-12k': 10500,
            '12-15k': 13500, '15-20k': 17500, '20k+': 25000
        }
        scatter_data = []
        for _, row in grouped.iterrows():
            label = row['salary_group']
            if label in salary_mid:
                x = salary_mid[label]
            else:
                x = 0
            scatter_data.append({
                'salary': x,
                'rate': row['rate'],
                'label': label
            })
        return jsonify({
            "code": 200,
            "data": scatter_data
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

# ----- 部门排名表格 -----
@dashboard_bp.route('/api/stats/ranking')
def api_ranking():
    try:
        df = get_employee_df()
        if df.empty:
            return jsonify({"code": 200, "data": []})
        df['Department'] = df['Department'].str.strip()
        grouped = df.groupby('Department').agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        grouped['rate'] = grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0,
            axis=1
        )
        grouped = grouped.sort_values('rate', ascending=False)
        return jsonify({
            "code": 200,
            "data": grouped.to_dict('records')
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ----- 看板一键导出 PNG -----
@dashboard_bp.route('/api/stats/export_dashboard')
def api_export_dashboard():
    """使用 Playwright 截取数据看板页面整页截图（包含全部 7 张图表）"""
    try:
        from flask import current_app, send_file
        from playwright.sync_api import sync_playwright
        import os, time

        # 截图保存路径
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        filepath = os.path.join(report_dir, f'dashboard_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png')

        # 获取当前服务的端口
        port = request.host.split(':')[-1] if ':' in request.host else '5000'
        host = request.host.split(':')[0] if ':' in request.host else '127.0.0.1'
        dashboard_url = f'http://127.0.0.1:{port}/dashboard?token=export_internal'

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1400, 'height': 900})
            page.goto(dashboard_url, wait_until='networkidle', timeout=30000)

            # 等待 ECharts 图表全部渲染完成
            page.wait_for_timeout(2000)

            # 滚动到底部确保懒加载内容都出现
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(500)
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(500)

            # 等待所有 canvas（ECharts 图表）渲染
            page.wait_for_selector('canvas', timeout=10000)

            # 额外等待确保动画完成
            page.wait_for_timeout(1500)

            # 整页截图
            page.screenshot(path=filepath, full_page=True)
            browser.close()

        return send_file(filepath, mimetype='image/png', as_attachment=True,
                         download_name=f'数据看板汇总_{pd.Timestamp.now().strftime("%Y%m%d")}.png')
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"code": 500, "msg": f'截图导出失败: {str(e)}'}), 500