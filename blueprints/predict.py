"""
预测蓝图 - 单员工预测 + 风险排名 + 离职洞察
"""
import os
import joblib
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session, redirect
from db_model import db, EmployeeBase, JobDetail, AttritionRisk
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from report.generate_analysis_report import generate as generate_report

predict_bp = Blueprint('predict', __name__, url_prefix='/predict')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_dir = os.path.join(BASE_DIR, 'models')

# 确保报表存储位置与生成脚本保持一致
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../reports'))

# ========== 1. 检查模型文件 ==========
required_models = [
    'logistic_regression.pkl',
    'random_forest.pkl',
    'scaler.pkl',
    'label_encoders.pkl',
    'feature_names.pkl',
    'categorical_cols.pkl'
]
missing = [f for f in required_models if not os.path.exists(os.path.join(model_dir, f))]
if missing:
    raise FileNotFoundError(f"模型文件缺失: {', '.join(missing)}。请先运行 train_model.py 生成模型。")

# ========== 2. 加载模型和预处理工具 ==========
lr = joblib.load(os.path.join(model_dir, 'logistic_regression.pkl'))
rf = joblib.load(os.path.join(model_dir, 'random_forest.pkl'))
scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
le_dict = joblib.load(os.path.join(model_dir, 'label_encoders.pkl'))
feature_names = joblib.load(os.path.join(model_dir, 'feature_names.pkl'))
categorical_cols = joblib.load(os.path.join(model_dir, 'categorical_cols.pkl'))

# sklearn 1.9+ 移除了 multi_class 参数但内部仍引用，补上该属性
if not hasattr(lr, 'multi_class'):
    lr.multi_class = 'auto'
if not hasattr(rf, 'multi_class'):
    rf.multi_class = 'auto'

print("[OK] 双模型加载成功（逻辑回归 + 随机森林）")


# ========== 3. 辅助函数 ==========
def encode_and_scale(df):
    """编码 + 标准化（单条预测）"""
    for col in categorical_cols:
        if col in df.columns:
            le = le_dict[col]
            try:
                df[col] = le.transform(df[col].astype(str))
            except ValueError:
                df[col] = le.transform([le.classes_[0]])[0]
        else:
            df[col] = 0
    df = df[feature_names]
    return scaler.transform(df)


def predict_prob(emp_dict):
    """双模型预测单员工，返回平均概率"""
    full_data = {col: emp_dict.get(col, 0) for col in feature_names}
    df = pd.DataFrame([full_data])
    X = encode_and_scale(df)
    prob_lr = lr.predict_proba(X)[0][1]
    prob_rf = rf.predict_proba(X)[0][1]
    return (prob_lr + prob_rf) / 2


def batch_predict(df_employees):
    """
    批量预测（传入包含所有特征列的DataFrame）
    返回概率数组
    """
    for col in feature_names:
        if col not in df_employees.columns:
            df_employees[col] = 0
    df_employees = df_employees[feature_names].copy()

    for col in categorical_cols:
        le = le_dict[col]
        try:
            df_employees[col] = le.transform(df_employees[col].astype(str))
        except ValueError:
            most_common = le.classes_[0]
            df_employees[col] = le.transform([most_common])[0]

    X = scaler.transform(df_employees)
    prob_lr = lr.predict_proba(X)[:, 1]
    prob_rf = rf.predict_proba(X)[:, 1]
    return (prob_lr + prob_rf) / 2


# ========== 4. 页面路由 ==========
@predict_bp.route('/')
def predict_page():
    return render_template('predict.html')


@predict_bp.route('/risk_list')
def risk_list_page():
    return render_template('risk_list.html')


@predict_bp.route('/insight')
def insight_page():
    return render_template('insight.html')


# ========== 5. API 接口 ==========

# 5.1 单员工预测（单结果版本）
@predict_bp.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'msg': '请求数据为空'})

        # 补全默认值（包含所有新增字段）
        default_values = {
            'Age': 30,
            'DailyRate': 800,
            'DistanceFromHome': 10,
            'Education': 3,
            'EducationField': 'Marketing',
            'EnvironmentSatisfaction': 3,
            'Gender': 'Male',
            'HourlyRate': 50,
            'JobInvolvement': 3,
            'JobLevel': 1,
            'MonthlyRate': 15000,
            'NumCompaniesWorked': 1,
            'PercentSalaryHike': 11,
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 3,
            'StockOptionLevel': 0,
            'TotalWorkingYears': 5,
            'TrainingTimesLastYear': 2,
            'WorkLifeBalance': 3,
            'YearsInCurrentRole': 2,
            'YearsSinceLastPromotion': 1,
            'YearsWithCurrManager': 2,
            'Department': 'Sales',
            'MaritalStatus': 'Single',
            'BusinessTravel': 'Travel_Rarely',
            'YearsAtCompany': 2
        }
        for key, val in default_values.items():
            if key not in data or data[key] is None:
                data[key] = val

        prob = predict_prob(data)
        risk_level = '低风险' if prob < 0.3 else '中风险' if prob < 0.7 else '高风险'

        from utils.logger import log_action
        log_action('单次预测', f'员工 {data.get("EmployeeNumber","")}', f'评分: {int(prob*100)}%, 等级: {risk_level}')

        return jsonify({
            'code': 0,
            'data': {
                'risk_score': int(prob * 100),
                'risk_level': risk_level
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


# 5.2 批量预测（风险排名）
@predict_bp.route('/api/batch')
def api_batch():
    try:
        # 查询所有在职员工（包含 JobSatisfaction 和 WorkLifeBalance）
        results = db.session.query(
            EmployeeBase.EmployeeNumber,
            EmployeeBase.Age,
            EmployeeBase.Gender,
            EmployeeBase.Department,
            EmployeeBase.DistanceFromHome,
            JobDetail.JobRole,
            JobDetail.JobLevel,
            JobDetail.MonthlyIncome,
            JobDetail.TotalWorkingYears,
            AttritionRisk.OverTime,
            AttritionRisk.JobSatisfaction,
            AttritionRisk.EnvironmentSatisfaction,
            AttritionRisk.WorkLifeBalance,
            AttritionRisk.YearsAtCompany,
            AttritionRisk.Attrition
        ).join(
            JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        ).join(
            AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
        ).filter(AttritionRisk.Attrition == 'No').all()

        if not results:
            return jsonify({'code': 0, 'data': []})

        df = pd.DataFrame([{
            'EmployeeNumber': r.EmployeeNumber,
            'Age': r.Age,
            'Department': r.Department,
            'JobRole': r.JobRole,
            'MonthlyIncome': r.MonthlyIncome,
            'OverTime': r.OverTime,
            'YearsAtCompany': r.YearsAtCompany,
            'TotalWorkingYears': r.TotalWorkingYears,
            'JobSatisfaction': r.JobSatisfaction,
            'WorkLifeBalance': r.WorkLifeBalance,
            'EnvironmentSatisfaction': r.EnvironmentSatisfaction,
            'Gender': r.Gender,
            'DistanceFromHome': r.DistanceFromHome,
            'JobLevel': r.JobLevel,
        } for r in results])

        default_fill = {
            'DailyRate': 800,
            'Education': 3,
            'HourlyRate': 50,
            'JobInvolvement': 3,
            'MonthlyRate': 15000,
            'NumCompaniesWorked': 1,
            'PercentSalaryHike': 11,
            'PerformanceRating': 3,
            'RelationshipSatisfaction': 3,
            'StockOptionLevel': 0,
            'TrainingTimesLastYear': 2,
            'YearsInCurrentRole': 2,
            'YearsSinceLastPromotion': 1,
            'YearsWithCurrManager': 2,
            'BusinessTravel': 'Travel_Rarely',      # 临时默认值
            'MaritalStatus': 'Single',
            'EducationField': 'Life Sciences'
        }
        for col, val in default_fill.items():
            if col not in df.columns:
                df[col] = val

        probs = batch_predict(df)
        df['probability'] = probs

        df_sorted = df.sort_values('probability', ascending=False)
        result_data = []
        for _, row in df_sorted.iterrows():
            prob = row['probability']
            level = '高风险' if prob >= 0.7 else '中风险' if prob >= 0.3 else '低风险'
            advice = '建议立即1v1访谈' if level == '高风险' else '建议定期关注' if level == '中风险' else '保持现状'
            result_data.append({
                'EmployeeNumber': int(row['EmployeeNumber']),
                'Department': row['Department'],
                'JobRole': row['JobRole'],
                'OverTime': row['OverTime'],
                'YearsAtCompany': int(row['YearsAtCompany']) if pd.notna(row['YearsAtCompany']) else 0,
                'MonthlyIncome': int(row['MonthlyIncome']) if pd.notna(row['MonthlyIncome']) else 0,
                'Age': int(row['Age']) if pd.notna(row['Age']) else 0,
                'JobSatisfaction': int(row['JobSatisfaction']) if pd.notna(row['JobSatisfaction']) else 3,
                'WorkLifeBalance': int(row['WorkLifeBalance']) if pd.notna(row['WorkLifeBalance']) else 3,
                'BusinessTravel': row.get('BusinessTravel', 'Travel_Rarely'),  # 从 df 中取
                'probability': round(prob, 4),
                'risk_level': level,
                'risk_score': int(prob * 100),
                'advice': advice
            })

        from utils.logger import log_action
        log_action('批量预测', '', f'共 {len(result_data)} 名员工')

        return jsonify({'code': 0, 'data': result_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 1, 'msg': f'批量预测失败: {str(e)}'})

# 5.3 离职洞察（七大维度，月薪以2k为单位，显示为10k）
@predict_bp.route('/api/insight')
def api_insight():
    try:
        results = db.session.query(
            EmployeeBase.EmployeeNumber,
            EmployeeBase.Age,
            EmployeeBase.Gender,
            EmployeeBase.MaritalStatus,
            EmployeeBase.EducationField,
            EmployeeBase.Department,
            EmployeeBase.DistanceFromHome,
            JobDetail.JobRole,
            JobDetail.JobLevel,
            JobDetail.MonthlyIncome,
            JobDetail.TotalWorkingYears,
            AttritionRisk.OverTime,
            AttritionRisk.JobSatisfaction,
            AttritionRisk.EnvironmentSatisfaction,
            AttritionRisk.WorkLifeBalance,
            AttritionRisk.YearsAtCompany,
            AttritionRisk.JobInvolvement,
            AttritionRisk.RelationshipSatisfaction,
            AttritionRisk.Attrition
        ).join(
            JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        ).join(
            AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
        ).filter(AttritionRisk.Attrition == 'No').all()

        if not results:
            return jsonify({'code': 0, 'data': {'indicators': [], 'high': [], 'mid': [], 'low': []}})

        df = pd.DataFrame([{
            'EmployeeNumber': r.EmployeeNumber,
            'Age': r.Age,
            'Gender': r.Gender,
            'MaritalStatus': r.MaritalStatus,
            'EducationField': r.EducationField,
            'Department': r.Department,
            'DistanceFromHome': r.DistanceFromHome,
            'JobRole': r.JobRole,
            'JobLevel': r.JobLevel,
            'MonthlyIncome': r.MonthlyIncome,
            'TotalWorkingYears': r.TotalWorkingYears,
            'OverTime': r.OverTime,
            'JobSatisfaction': r.JobSatisfaction,
            'EnvironmentSatisfaction': r.EnvironmentSatisfaction,
            'WorkLifeBalance': r.WorkLifeBalance,
            'YearsAtCompany': r.YearsAtCompany,
            'JobInvolvement': r.JobInvolvement,
            'RelationshipSatisfaction': r.RelationshipSatisfaction
        } for r in results])

        default_fill = {
            'DailyRate': 800,
            'Education': 3,
            'HourlyRate': 50,
            'MonthlyRate': 15000,
            'NumCompaniesWorked': 1,
            'PercentSalaryHike': 11,
            'PerformanceRating': 3,
            'StockOptionLevel': 0,
            'TrainingTimesLastYear': 2,
            'YearsInCurrentRole': 2,
            'YearsSinceLastPromotion': 1,
            'YearsWithCurrManager': 2,
            'BusinessTravel': 'Travel_Rarely',
            'MaritalStatus': 'Single',
            'EducationField': 'Life Sciences'
        }
        for col, val in default_fill.items():
            if col not in df.columns:
                df[col] = val

        probs = batch_predict(df)
        df['probability'] = probs

        def risk_group(p):
            return 'high' if p >= 0.7 else 'mid' if p >= 0.3 else 'low'
        df['risk_group'] = df['probability'].apply(risk_group)
        df['OverTime_num'] = df['OverTime'].map({'Yes': 1, 'No': 0})

        # 七大维度，月薪除以2000（2k为单位），轴最大值设为5（对应10k），显示为“月薪（10k）”
        indicators = [
            {'name': '加班比例', 'max': 1},
            {'name': '工作满意度', 'max': 4},
            {'name': '月薪（10k）', 'max': 5},
            {'name': '工作生活平衡', 'max': 4},
            {'name': '平均通勤（10km）', 'max': 3},
            {'name': '环境满意度', 'max': 4},
            {'name': '工作投入度', 'max': 4}
        ]

        group_means = df.groupby('risk_group').agg({
            'OverTime_num': 'mean',
            'JobSatisfaction': 'mean',
            'MonthlyIncome': 'mean',
            'WorkLifeBalance': 'mean',
            'DistanceFromHome': 'mean',
            'EnvironmentSatisfaction': 'mean',
            'JobInvolvement': 'mean'
        }).reset_index()

        result = {'indicators': indicators, 'high': [], 'mid': [], 'low': []}
        for _, row in group_means.iterrows():
            group = row['risk_group']
            values = [
                row['OverTime_num'],
                row['JobSatisfaction'],
                row['MonthlyIncome'] / 2000.0,  # 除以2000，10k对应5
                row['WorkLifeBalance'],
                row['DistanceFromHome'] / 10.0,
                row['EnvironmentSatisfaction'],
                row['JobInvolvement']
            ]
            result[group] = [round(v, 2) for v in values]

        return jsonify({'code': 0, 'data': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 1, 'msg': f'洞察数据获取失败: {str(e)}', 'trace': traceback.format_exc()})


# ========== 5.3b 综合报告 PNG 导出 ==========
def _get_employee_report_df():
    """查询员工数据（与 dashboard 一致）"""
    results = db.session.query(
        EmployeeBase.EmployeeNumber,
        EmployeeBase.Age,
        EmployeeBase.Gender,
        EmployeeBase.Department,
        EmployeeBase.MaritalStatus,
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


@predict_bp.route('/api/report')
def api_report():
    """生成综合报告图（部门柱状图 + 岗位饼图 + 年龄折线图 + 分析结论），返回 PNG"""
    try:
        df = _get_employee_report_df()
        if df.empty:
            return jsonify({'code': 1, 'msg': '暂无员工数据'})

        # ---- 中文字体设置 ----
        zh_font = fm.FontProperties(fname='C:/Windows/Fonts/simhei.ttf', size=13)
        zh_font_title = fm.FontProperties(fname='C:/Windows/Fonts/simhei.ttf', size=17)
        zh_font_small = fm.FontProperties(fname='C:/Windows/Fonts/simhei.ttf', size=10)
        zh_font_text = fm.FontProperties(fname='C:/Windows/Fonts/msyh.ttc', size=11)

        # ---- 数据预处理 ----
        df['Department'] = df['Department'].str.strip()

        # 部门离职率
        dept_grouped = df.groupby('Department').agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        dept_grouped['rate'] = dept_grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0, axis=1)
        dept_grouped = dept_grouped.sort_values('rate', ascending=True)

        # 离职岗位分布
        attrition_df = df[df['Attrition'] == 1]
        role_counts = attrition_df['JobRole'].value_counts()

        # 年龄段离职率
        df['age_group'] = pd.cut(
            df['Age'],
            bins=[18, 25, 30, 35, 40, 45, 50, 55, 60],
            labels=['18-25', '26-30', '31-35', '36-40', '41-45', '46-50', '51-55', '56-60'],
            right=False
        )
        age_grouped = df.groupby('age_group', observed=False).agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', 'sum')
        ).reset_index()
        age_grouped['rate'] = age_grouped.apply(
            lambda r: round(r['attrition'] / r['total'] * 100, 2) if r['total'] else 0, axis=1)

        # 关键指标
        total_emp = len(df)
        total_att = int(df['Attrition'].sum())
        overall_rate = round(total_att / total_emp * 100, 2) if total_emp else 0
        high_dept = dept_grouped.iloc[-1] if len(dept_grouped) > 0 else None
        highest_role = role_counts.idxmax() if len(role_counts) > 0 else '无'
        overtime_rate = round(
            len(df[(df['OverTime'] == 'Yes') & (df['Attrition'] == 1)]) / max(total_att, 1) * 100, 2)
        young_rate = round(
            len(df[(df['Age'] < 30) & (df['Attrition'] == 1)]) / max(total_att, 1) * 100, 2)

        # ---- 创建画布 2x2 + 底部结论栏 ----
        fig = plt.figure(figsize=(18, 13), dpi=150)
        fig.patch.set_facecolor('#f5f7fa')

        gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.30,
                              left=0.06, right=0.94, top=0.93, bottom=0.28)

        # ===== 子图1: 部门离职率（水平柱状图） =====
        ax1 = fig.add_subplot(gs[0, 0])
        colors1 = ['#5FB878' if v < overall_rate else '#FFB800' if v < overall_rate * 1.5 else '#FF5722'
                   for v in dept_grouped['rate']]
        bars = ax1.barh(dept_grouped['Department'], dept_grouped['rate'], color=colors1, edgecolor='white', height=0.65)
        for bar, val in zip(bars, dept_grouped['rate']):
            ax1.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                     f'{val}%', va='center', fontsize=8, fontproperties=zh_font_small, color='#333')
        ax1.set_title('各部门离职率对比', fontproperties=zh_font_title, pad=12, color='#1a2332')
        ax1.set_xlabel('离职率 (%)', fontproperties=zh_font, color='#666')
        ax1.set_yticklabels(dept_grouped['Department'], fontproperties=zh_font_small)
        ax1.axvline(x=overall_rate, color='#e74c3c', linestyle='--', linewidth=1.2, alpha=0.7,
                    label=f'整体离职率 {overall_rate}%')
        ax1.legend(prop=zh_font_small, loc='lower right')
        ax1.set_xlim(right=dept_grouped['rate'].max() * 1.25)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.tick_params(labelsize=8)

        # ===== 子图2: 离职岗位分布（饼图） =====
        ax2 = fig.add_subplot(gs[0, 1])
        pie_colors = ['#FF5722', '#FF9800', '#FFB800', '#5FB878', '#409eff', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
        explode = [0.03] * len(role_counts)
        wedges, texts, autotexts = ax2.pie(
            role_counts.values, labels=role_counts.index, autopct='%1.1f%%',
            startangle=90, colors=pie_colors[:len(role_counts)],
            explode=explode, pctdistance=0.6, labeldistance=1.12,
            textprops={'fontproperties': zh_font_small}
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_fontweight('bold')
            at.set_color('#1a2332')
        ax2.set_title('离职员工岗位分布', fontproperties=zh_font_title, pad=12, color='#1a2332')

        # ===== 子图3: 年龄段离职率（折线图） =====
        ax3 = fig.add_subplot(gs[1, 0])
        x = range(len(age_grouped))
        ax3.plot(x, age_grouped['rate'], color='#409eff', marker='o', linewidth=2.5,
                 markersize=9, markerfacecolor='white', markeredgewidth=2, markeredgecolor='#409eff')
        for i, val in enumerate(age_grouped['rate']):
            ax3.annotate(f'{val}%', (x[i], age_grouped['rate'].iloc[i]),
                         textcoords="offset points", xytext=(0, 14),
                         ha='center', fontsize=9, fontweight='bold', color='#1a2332',
                         fontproperties=zh_font_small)
        ax3.set_xticks(x)
        ax3.set_xticklabels(age_grouped['age_group'], fontproperties=zh_font_small)
        ax3.set_title('各年龄段离职率趋势', fontproperties=zh_font_title, pad=12, color='#1a2332')
        ax3.set_ylabel('离职率 (%)', fontproperties=zh_font, color='#666')
        ax3.set_ylim(bottom=0, top=age_grouped['rate'].max() * 1.35)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.grid(axis='y', linestyle='--', alpha=0.3)
        ax3.tick_params(labelsize=8)

        # ===== 子图4: 分析结论（文本） =====
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        ax4.set_xlim(0, 10)
        ax4.set_ylim(0, 10)

        conclusions = [
            f'【员工离职分析综合报告】',
            '',
            f'▸ 员工总数: {total_emp} 人    离职人数: {total_att} 人    整体离职率: {overall_rate}%',
            '',
            f'▸ 高离职率部门: {high_dept["Department"] if high_dept is not None else "无"} '
            f'({high_dept["rate"]}%)，需重点排查',
            f'▸ 离职最集中岗位: {highest_role}（{role_counts.max() if len(role_counts) > 0 else 0} 人）',
            f'▸ 加班员工占离职: {overtime_rate}%，加班是重要风险因子',
            f'▸ 30岁以下占离职: {young_rate}%，年轻员工留存值得关注',
            '',
            f'▸ 建议1: 对 {high_dept["Department"] if high_dept is not None else "高离职率部门"} 开展专项留任面谈',
            f'▸ 建议2: 优化 {highest_role} 岗位的职业发展与薪酬体系',
            f'▸ 建议3: 控制加班时长，关注工作生活平衡',
            f'▸ 建议4: 对年轻员工建立导师制与快速成长通道',
        ]

        y_pos = 9.5
        for i, line in enumerate(conclusions):
            if line.startswith('【'):
                ax4.text(0.3, y_pos, line, fontproperties=zh_font_title, fontsize=14, color='#1a2332', va='top')
            elif line.startswith('▸ 建议'):
                ax4.text(0.5, y_pos, line, fontproperties=zh_font_text, fontsize=10.5, color='#009688', va='top')
            elif line.startswith('▸'):
                ax4.text(0.5, y_pos, line, fontproperties=zh_font_text, fontsize=10.5, color='#2c3e50', va='top')
            else:
                ax4.text(0.3, y_pos, line, fontproperties=zh_font_text, fontsize=10, color='#666', va='top')
            y_pos -= 0.78 if line else 0.35

        # ===== 底部标题栏 =====
        fig.text(0.5, 0.13, 'Employee Attrition Insight Report  |  员工离职洞察报告',
                 ha='center', va='center', fontsize=16, fontweight='bold', color='#1a2332',
                 fontproperties=zh_font_title)
        fig.text(0.5, 0.08, f'生成时间: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}  |  '
                 f'数据范围: 全体 {total_emp} 名员工  |  '
                 f'整体离职率: {overall_rate}%',
                 ha='center', va='center', fontsize=9, color='#8c939d',
                 fontproperties=zh_font_small)

        # ---- 输出为 PNG bytes ----
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        buf.seek(0)

        return send_file(
            buf,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'离职洞察综合报告_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.png'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 1, 'msg': f'报告生成失败: {str(e)}'})


# ========== 5.3c Excel 导出（含图表） ==========
@predict_bp.route('/api/report/excel')
def api_report_excel():
    """导出多 Sheet Excel 报告：部门离职率明细+图表、高风险员工名单"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.chart import BarChart, Reference

        wb = Workbook()
        header_font = Font(name='Microsoft YaHei', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='1B3A5C', end_color='1B3A5C', fill_type='solid')
        header_align = Alignment(horizontal='center', vertical='center')
        cell_align = Alignment(horizontal='center', vertical='center')
        thin_border = Border(left=Side(style='thin', color='D0D0D0'), right=Side(style='thin', color='D0D0D0'),
                             top=Side(style='thin', color='D0D0D0'), bottom=Side(style='thin', color='D0D0D0'))

        def style_header(ws, row, ncols):
            for c in range(1, ncols+1):
                cl = ws.cell(row=row, column=c); cl.font=header_font; cl.fill=header_fill; cl.alignment=header_align; cl.border=thin_border
        def style_row(ws, row, ncols):
            for c in range(1, ncols+1):
                cl = ws.cell(row=row, column=c); cl.alignment=cell_align; cl.border=thin_border; cl.font=Font(name='Microsoft YaHei', size=10)

        # -- 数据准备：查询所有员工（含离职和在职） --
        df = _get_employee_report_df()
        if df.empty: return jsonify({'code':1, 'msg':'暂无员工数据'})

        # 清理部门名称空白
        df['Department'] = df['Department'].str.strip()

        # 计算部门离职率
        dept_stats = df.groupby('Department').agg(total=('EmployeeNumber','count'), attrition=('Attrition','sum')).reset_index()
        dept_stats['rate'] = (dept_stats['attrition'] / dept_stats['total'] * 100).round(1)
        dept_stats = dept_stats.sort_values('rate', ascending=False)

        # 跑预测获取风险评分（在职员工）
        att_val = df['Attrition'].iloc[0] if len(df) > 0 else 'No'
        is_numeric = isinstance(att_val, (int, float, np.integer, np.floating))
        if is_numeric:
            active_df = df[df['Attrition'] == 0].copy()
        else:
            active_df = df[df['Attrition'].isin(['No', 'NO', 'no'])].copy()
        if not active_df.empty:
            for col in feature_names:
                if col not in active_df.columns: active_df[col] = 0
            probs = batch_predict(active_df)
            active_df['risk_score'] = (probs * 100).round(1)
            active_df['risk_level'] = pd.cut(active_df['risk_score'], bins=[0,30,70,100], labels=['低风险','中风险','高风险'])
        else:
            active_df = active_df.assign(risk_score=0, risk_level='')

        # ==================== Sheet 1: 部门离职率明细 ====================
        ws1 = wb.active
        ws1.title = '部门离职率明细'
        h1 = ['部门', '总人数', '离职人数', '离职率(%)']
        for c, h in enumerate(h1, 1): ws1.cell(row=1, column=c, value=h)
        style_header(ws1, 1, 4)
        for i, (_, r) in enumerate(dept_stats.iterrows()):
            ws1.cell(row=i+2, column=1, value=r['Department']); ws1.cell(row=i+2, column=2, value=r['total'])
            ws1.cell(row=i+2, column=3, value=r['attrition']); ws1.cell(row=i+2, column=4, value=r['rate'])
            style_row(ws1, i+2, 4)
            if r['rate'] >= 20: ws1.cell(row=i+2, column=4).font = Font(name='Microsoft YaHei', size=10, color='FF5722', bold=True)
        ws1.column_dimensions['A'].width = 24
        for c in ['B','C','D']: ws1.column_dimensions[c].width = 14

        # 嵌入柱状图
        nrows = len(dept_stats) + 1
        if nrows > 1:
            chart = BarChart()
            chart.type = 'col'; chart.title = '各部门离职率对比'; chart.y_axis.title = '离职率 (%)'
            chart.style = 10; chart.width = 22; chart.height = 13
            chart.add_data(Reference(ws1, min_col=4, min_row=1, max_row=nrows), titles_from_data=True)
            chart.set_categories(Reference(ws1, min_col=1, min_row=2, max_row=nrows))
            chart.series[0].graphicalProperties.solidFill = "409EFF"
            ws1.add_chart(chart, 'A' + str(nrows + 3))

        # ==================== Sheet 2: 高风险员工名单 ====================
        ws2 = wb.create_sheet('高风险员工名单')
        h2 = ['员工编号', '部门', '岗位', '月薪', '加班', '工作满意度', '工作生活平衡', '司龄', '风险评分', '风险等级']
        for c, h in enumerate(h2, 1): ws2.cell(row=1, column=c, value=h)
        style_header(ws2, 1, len(h2))
        risk_sorted = active_df.sort_values('risk_score', ascending=False)
        for i, (_, r) in enumerate(risk_sorted.iterrows()):
            vals = [r.get('EmployeeNumber',''), r.get('Department',''), r.get('JobRole',''),
                    r.get('MonthlyIncome',''), r.get('OverTime',''), r.get('JobSatisfaction',''),
                    r.get('WorkLifeBalance',''), r.get('YearsAtCompany',''),
                    r.get('risk_score',''), r.get('risk_level','')]
            for c, v in enumerate(vals, 1): ws2.cell(row=i+2, column=c, value=v)
            style_row(ws2, i+2, len(h2))
            rl = r.get('risk_level','')
            if rl == '高风险': ws2.cell(row=i+2, column=10).font = Font(name='Microsoft YaHei', size=10, color='FF5722', bold=True)
            elif rl == '中风险': ws2.cell(row=i+2, column=10).font = Font(name='Microsoft YaHei', size=10, color='FFB800', bold=True)
            else: ws2.cell(row=i+2, column=10).font = Font(name='Microsoft YaHei', size=10, color='5FB878', bold=True)
        for c, w in enumerate([12,18,20,12,8,14,16,8,12,12], 1): ws2.column_dimensions[ws2.cell(row=1,column=c).column_letter].width = w

        # ==================== Sheet 3: 干预记录汇总 ====================
        ws3 = wb.create_sheet('干预记录汇总')
        h3 = ['员工编号', '部门', '干预类型', '描述摘要', '处理结果', '操作人', '操作时间']
        for c, h in enumerate(h3, 1): ws3.cell(row=1, column=c, value=h)
        style_header(ws3, 1, len(h3))

        # 从数据库查询所有干预记录，联查员工部门
        from db_model import Intervention
        interventions = Intervention.query.order_by(Intervention.created_at.desc()).all()

        if interventions:
            type_map = {'salary': '调薪', 'transfer': '转岗', 'interview': '面谈',
                        'training': '培训', 'other': '其他'}
            for i, inv in enumerate(interventions):
                row = i + 2
                # 通过 relationship 获取部门
                dept = inv.employee.Department if inv.employee else ''
                # 干预类型中文映射
                type_cn = type_map.get(inv.type, inv.type)
                vals = [inv.employee_id, dept, type_cn,
                        inv.description or '', inv.result or '',
                        inv.operator, inv.created_at.strftime('%Y-%m-%d %H:%M') if inv.created_at else '']
                for c, v in enumerate(vals, 1):
                    ws3.cell(row=row, column=c, value=v)
                style_row(ws3, row, len(h3))
                # 高风险干预记录标红提示
                if inv.type in ('salary', 'transfer'):
                    ws3.cell(row=row, column=3).font = Font(name='Microsoft YaHei', size=10, color='FF5722', bold=True)
        else:
            ws3.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(h3))
            ws3.cell(row=2, column=1, value='（暂无干预记录）').font = Font(name='Microsoft YaHei', size=10, color='999999')
            for c in range(1, len(h3)+1): ws3.cell(row=2, column=c).alignment = cell_align

        col_widths = [12, 18, 12, 36, 28, 14, 18]
        for c, w in enumerate(col_widths, 1):
            ws3.column_dimensions[ws3.cell(row=1, column=c).column_letter].width = w

        # -- 输出 --
        buf = BytesIO()
        wb.save(buf); buf.seek(0)

        from report.generate_analysis_report import save_record
        excel_path = os.path.join(REPORT_DIR, 'analysis_report.xlsx')
        wb.save(excel_path)
        from flask import current_app as ca
        save_record(ca._get_current_object(), excel_path, 'Excel')

        ts = pd.Timestamp.now().strftime('%Y%m%d')
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'员工离职分析报告_{ts}.xlsx')
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': f'Excel 导出失败: {str(e)}'})


# ========== 5.3c2 筛选选项 API ==========
@predict_bp.route('/api/filters', methods=['GET'])
def api_filters():
    """返回可用的筛选选项（部门列表等）"""
    try:
        from sqlalchemy import func
        depts = db.session.query(
            func.trim(EmployeeBase.Department)
        ).distinct().order_by(
            func.trim(EmployeeBase.Department)
        ).all()
        department_list = [d[0] for d in depts if d[0]]
        return jsonify({
            'code': 0,
            'data': {
                'departments': department_list,
                'risk_levels': [
                    {'value': '', 'label': '全部'},
                    {'value': 'high', 'label': '高风险'},
                    {'value': 'mid', 'label': '中风险'},
                    {'value': 'low', 'label': '低风险'},
                ]
            }
        })
    except Exception as e:
        return jsonify({'code': 1, 'msg': f'获取筛选选项失败: {str(e)}'})


# ========== 5.3d 生成与导出综合报告 API ==========
@predict_bp.route('/api/report/generate/analysis', methods=['POST'])
def api_generate_analysis():
    """生成综合离职分析报告图（PNG），保存到 reports/ 目录，支持筛选参数"""
    try:
        req_data = request.get_json(silent=True) or {}
        filters = {
            'departments': req_data.get('departments'),
            'risk_level': req_data.get('risk_level'),
            'date_start': req_data.get('date_start'),
            'date_end': req_data.get('date_end'),
        }
        app = current_app._get_current_object()
        filepath = generate_report(app, filters=filters)
        from report.generate_analysis_report import save_record
        save_record(app, filepath, 'PNG', filters)
        from utils.logger import log_action
        log_action('生成报告', os.path.basename(filepath), str(filters)[:200])
        return jsonify({'code': 200, 'message': '分析报告生成成功', 'file': filepath})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'报告生成失败: {str(e)}'})


@predict_bp.route('/api/report/download/analysis', methods=['GET'])
def download_analysis_report():
    """下载或预览已生成的综合离职分析报告图"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    filepath = os.path.join(REPORT_DIR, 'analysis_report.png')
    if not os.path.exists(filepath):
        return jsonify({'code': 404, 'message': '报告图尚未生成，请先生成后再试'}), 404

    from utils.logger import log_action
    log_action('下载报告', 'analysis_report.png', 'PNG 格式')
    return send_file(
        filepath,
        mimetype='image/png',
        as_attachment=True,
        download_name='员工离职综合分析报告.png'
    )


# ========== 5.3d2 PDF 导出 API ==========
@predict_bp.route('/api/report/export/pdf', methods=['POST'])
def api_export_pdf():
    try:
        req_data = request.get_json(silent=True) or {}
        filters = {k: req_data.get(k) for k in ['departments', 'risk_level', 'date_start', 'date_end']}
        from report.export_pdf import export_pdf
        app = current_app._get_current_object()
        filepath = export_pdf(app, filters=filters)
        from report.generate_analysis_report import save_record
        save_record(app, filepath, 'PDF', filters)
        return send_file(filepath, mimetype='application/pdf',
                         as_attachment=True, download_name='员工离职分析报告.pdf')
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 500, 'message': f'PDF 导出失败: {str(e)}'})


# ========== 5.3e 报告历史 API ==========
@predict_bp.route('/api/report/history', methods=['GET'])
def api_report_history():
    """获取报告历史，支持文件类型和时间范围筛选"""
    try:
        from db_model import ReportRecord
        from datetime import datetime as dt
        file_type = request.args.get('file_type', '')
        date_start = request.args.get('date_start', '')
        date_end = request.args.get('date_end', '')
        q = ReportRecord.query
        if file_type and file_type in ('PNG', 'Excel', 'PDF'):
            q = q.filter(ReportRecord.file_type == file_type)
        if date_start:
            q = q.filter(ReportRecord.created_at >= dt.strptime(date_start, '%Y-%m-%d'))
        if date_end:
            q = q.filter(ReportRecord.created_at <= dt.strptime(date_end + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        records = q.order_by(ReportRecord.created_at.desc()).limit(200).all()
        return jsonify({'code': 0, 'data': [{
            'id': r.id, 'filename': r.filename, 'file_type': r.file_type,
            'file_size': r.file_size, 'filters': r.filters, 'generated_by': r.generated_by,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else '',
        } for r in records]})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/report/delete/<int:record_id>', methods=['DELETE'])
def api_report_delete(record_id):
    try:
        from db_model import ReportRecord
        r = ReportRecord.query.get(record_id)
        if not r: return jsonify({'code': 404, 'msg': '记录不存在'})
        fp = os.path.join(REPORT_DIR, r.filename)
        if os.path.exists(fp): os.remove(fp)
        db.session.delete(r); db.session.commit()
        return jsonify({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/report/download/<int:record_id>', methods=['GET'])
def api_report_download_by_id(record_id):
    try:
        from db_model import ReportRecord
        r = ReportRecord.query.get(record_id)
        if not r: return jsonify({'code': 404, 'msg': '记录不存在'})
        fp = os.path.join(REPORT_DIR, r.filename)
        if not os.path.exists(fp): return jsonify({'code': 404, 'msg': '文件不存在'})
        mime = {'PNG': 'image/png', 'Excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'PDF': 'application/pdf'}
        return send_file(fp, mimetype=mime.get(r.file_type, 'application/octet-stream'),
                         as_attachment=True, download_name=r.filename)
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/report/batch_download', methods=['GET'])
def api_report_batch_download():
    """批量下载报告 — 将选中的文件打包为 zip"""
    try:
        import zipfile
        from io import BytesIO
        ids_str = request.args.get('ids', '')
        if not ids_str:
            return jsonify({'code': 400, 'msg': '请选择要下载的报告'})
        ids = [int(i) for i in ids_str.split(',') if i.strip()]
        if not ids:
            return jsonify({'code': 400, 'msg': '参数无效'})
        from db_model import ReportRecord
        records = ReportRecord.query.filter(ReportRecord.id.in_(ids)).all()
        if not records:
            return jsonify({'code': 404, 'msg': '未找到选中文件'})
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for r in records:
                fp = os.path.join(REPORT_DIR, r.filename)
                if os.path.exists(fp):
                    zf.write(fp, r.filename)
        buf.seek(0)
        return send_file(buf, mimetype='application/zip', as_attachment=True,
                         download_name=f'报告批量下载_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.zip')
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/report/send_mail', methods=['POST'])
def api_send_mail():
    try:
        data = request.get_json(silent=True) or {}
        recipient = data.get('recipient', '')
        if not recipient or '@' not in recipient:
            return jsonify({'code': 400, 'msg': '请输入有效的收件人邮箱'})
        from report.mailer import send_report_email
        send_report_email(recipient)
        from utils.logger import log_action
        log_action('发送报告邮件', recipient, '')
        return jsonify({'code': 200, 'msg': f'报告已发送至 {recipient}'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 500, 'msg': f'邮件发送失败: {str(e)}'})


# ========== 5.3e2 对比分析 API ==========
@predict_bp.route('/api/compare', methods=['GET'])
def api_compare():
    """对比两个时段的数据"""
    try:
        dim = request.args.get('dim', 'Department')
        a_start = request.args.get('a_start', '')
        a_end = request.args.get('a_end', '')
        b_start = request.args.get('b_start', '')
        b_end = request.args.get('b_end', '')

        results = db.session.query(
            EmployeeBase.EmployeeNumber, EmployeeBase.Age, EmployeeBase.Department,
            EmployeeBase.record_date,
            JobDetail.JobRole, JobDetail.MonthlyIncome,
            AttritionRisk.Attrition
        ).outerjoin(JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        ).outerjoin(AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber).all()

        df = pd.DataFrame([{
            'EmployeeNumber': r.EmployeeNumber, 'Age': r.Age, 'Department': (r.Department or '').strip(),
            'record_date': r.record_date, 'JobRole': r.JobRole, 'MonthlyIncome': r.MonthlyIncome,
            'Attrition': 1 if str(r.Attrition).strip().lower() in ('yes','1') else 0
        } for r in results])

        def filter_period(data, start, end):
            if start:
                data = data[pd.to_datetime(data['record_date']) >= pd.to_datetime(start)]
            if end:
                data = data[pd.to_datetime(data['record_date']) <= pd.to_datetime(end) + pd.Timedelta(days=1)]
            return data

        df_a = filter_period(df.copy(), a_start, a_end)
        df_b = filter_period(df.copy(), b_start, b_end)

        def calc_dim(data):
            if dim == 'Department':
                grp = data.groupby('Department')
            elif dim == 'JobRole':
                grp = data.groupby('JobRole')
            else:
                data['AgeGroup'] = pd.cut(data['Age'], bins=[18,25,30,35,40,45,50,55,60],
                                          labels=['18-25','26-30','31-35','36-40','41-45','46-50','51-55','56-60'])
                grp = data.groupby('AgeGroup', observed=False)
            t = grp.agg(total=('EmployeeNumber','count'), att=('Attrition','sum'))
            t['rate'] = (t['att'] / t['total'] * 100).round(1)
            return t

        stats_a = calc_dim(df_a)
        stats_b = calc_dim(df_b)
        all_labels = sorted(set(stats_a.index.tolist()) | set(stats_b.index.tolist()), key=lambda x: str(x))

        return jsonify({'code': 0, 'data': {
            'labels': all_labels,
            'a_totals': [int(stats_a.loc[l,'total']) if l in stats_a.index else 0 for l in all_labels],
            'a_att': [int(stats_a.loc[l,'att']) if l in stats_a.index else 0 for l in all_labels],
            'a_rates': [float(stats_a.loc[l,'rate']) if l in stats_a.index else 0 for l in all_labels],
            'b_totals': [int(stats_b.loc[l,'total']) if l in stats_b.index else 0 for l in all_labels],
            'b_att': [int(stats_b.loc[l,'att']) if l in stats_b.index else 0 for l in all_labels],
            'b_rates': [float(stats_b.loc[l,'rate']) if l in stats_b.index else 0 for l in all_labels],
        }})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


# ========== 5.3f 报告历史页面 ==========
@predict_bp.route('/report_history')
def report_history_page():
    return render_template('report_history.html')


# ========== 5.4 AI 风险分析（使用阿里云 DashScope） ==========
import dashscope
from dashscope import Generation
import os

# 配置 API Key（建议从环境变量读取）
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "sk-ws-H.EDDPMYD.xCG8.MEYCIQC_BW6s6Puaj3BD5jF4ZTx31w-Nm2AVBA8EJYf19mgsrAIhALr4DNuNIPTbpWR4TDYjHOweZzFOaKPFpSy51kF8Yk6Z")

@predict_bp.route('/ai_analyze', methods=['POST'])
def ai_analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据为空'})

        # 1. 从请求中获取员工信息
        emp_id = data.get('EmployeeNumber')
        dept = data.get('Department', '未知')
        role = data.get('JobRole', '未知')
        age = data.get('Age', 0)
        years = data.get('YearsAtCompany', 0)
        income = data.get('MonthlyIncome', 0)
        overtime = '是' if data.get('OverTime') == 'Yes' else '否'
        satisfaction = data.get('JobSatisfaction', 3)
        work_life = data.get('WorkLifeBalance', 3)
        env_satisfaction = data.get('EnvironmentSatisfaction', 3)
        marital = data.get('MaritalStatus', '未知')
        business_travel = data.get('BusinessTravel', '很少出差')
        risk_score = data.get('risk_score', 0)
        risk_level = data.get('risk_level', '未知')

        # 2. 构建 Prompt（要求600字左右，格式规范）
        prompt = f"""你是一位精通组织心理学与数据驱动分析的企业高级人力资源专家（CHO）。请针对以下员工的详细特征进行深度穿透分析，并提供优化的管理方案。

【员工基本信息】
- 工号：{emp_id}
- 部门：{dept}
- 岗位：{role}
- 年龄：{age} 岁
- 司龄：{years} 年
- 月收入：{income} 元
- 婚姻状况：{marital}
- 出差频率：{business_travel}

【工作状态】
- 是否加班：{overtime}
- 工作满意度（1~4）：{satisfaction}
- 工作生活平衡（1~4）：{work_life}
- 环境满意度（1~4）：{env_satisfaction}

【风险概况】
- 当前风险评分：{risk_score}%
- 当前风险等级：{risk_level}

请从以下四个维度进行详细分析，总字数控制在 **600字左右**，每个维度展开 3-5 句话：

1. 离职风险核心驱动因素分析：结合该员工的具体特征表现，深入分析最可能触发离职的 2-3 个关键因素，并解释其内在逻辑。

2. 潜在的组织/团队问题：从团队管理、工作分配、职业发展、激励机制等角度，剖析该员工所处的组织环境问题。

3. 个性化管理建议（3-4条）：针对该员工的具体情况，给出具体、可执行的行动建议，每条建议需包含明确的负责人和时间节点。

4. 风险预警等级评估：结合所有特征和风险评分，给出最终的风险等级判断，并说明理由和紧急程度。

要求：语言专业、简洁、有洞察力，避免空泛套话，每条建议都要具体可执行。请使用统一的中文标点符号（中文逗号、句号）。"""

        # 3. 调用阿里云通义千问模型
        response = Generation.call(
            model='qwen-plus',
            prompt=prompt,
            temperature=0.7,
            max_tokens=800,        # 从 400 改为 800，确保600字左右
            top_p=0.9,
            stop=None
        )

        # 4. 解析响应
        if response.status_code == 200:
            analysis = response.output.text
        else:
            return jsonify({
                'code': 500,
                'msg': f'AI 调用失败：{response.message}'
            })

        # 5. 返回分析结果
        return jsonify({
            'code': 0,
            'data': {
                'analysis': analysis,
                'emp_id': emp_id
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': f'服务器错误：{str(e)}'})


# ========== 6. 干预措施跟踪 API ==========

@predict_bp.route('/interventions')
def interventions_page():
    """干预措施管理页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('interventions.html')


@predict_bp.route('/interventions/effectiveness')
def interventions_effectiveness_page():
    """干预效果统计可视化页 (2.4)"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('effectiveness.html')


@predict_bp.route('/api/interventions', methods=['GET'])
def api_interventions_list():
    """获取干预记录列表，支持按类型、日期范围筛选 + 分页，联查部门+岗位"""
    try:
        from db_model import Intervention
        from datetime import datetime as dt

        type_filter = request.args.get('type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 15))

        results = db.session.query(
            Intervention,
            EmployeeBase.EmployeeNumber,
            EmployeeBase.Department,
            JobDetail.JobRole,
        ).outerjoin(
            EmployeeBase, Intervention.employee_id == EmployeeBase.EmployeeNumber
        ).outerjoin(
            JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        )

        if type_filter:
            results = results.filter(Intervention.type == type_filter)
        if start_date:
            results = results.filter(Intervention.created_at >= dt.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            results = results.filter(Intervention.created_at <= dt.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

        total = results.count()
        results = results.order_by(Intervention.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        data = []
        for inv, emp_num, dept, role in results:
            desc = inv.description or ''
            data.append({
                'id': inv.id,
                'employee_id': inv.employee_id,
                'employee_number': emp_num or inv.employee_id,
                'department': dept or '',
                'job_role': role or '',
                'type': inv.type,
                'description': desc,
                'description_short': desc[:30] + ('……' if len(desc) > 30 else ''),
                'result': inv.result or '',
                'operator': inv.operator or '',
                'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S') if inv.created_at else '',
            })

        return jsonify({'code': 0, 'data': data, 'count': total})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/interventions', methods=['POST'])
def api_interventions_create():
    """新增干预记录"""
    try:
        from db_model import Intervention
        data = request.get_json(silent=True) or {}
        employee_id = data.get('employee_id')
        if not employee_id:
            return jsonify({'code': 400, 'msg': '员工工号不能为空'})

        inv = Intervention(
            employee_id=int(employee_id),
            type=data.get('type', '其他'),
            description=data.get('description', ''),
            result=data.get('result', ''),
            operator=data.get('operator', ''),
        )
        db.session.add(inv)
        db.session.commit()
        from utils.logger import log_action
        log_action('添加干预记录', f'员工 {employee_id}', f'类型：{inv.type}, 操作人：{inv.operator}')
        return jsonify({'code': 0, 'msg': '干预记录已添加', 'data': {'id': inv.id}})
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/interventions/<int:inv_id>', methods=['PUT'])
def api_interventions_update(inv_id):
    """更新干预记录（主要用于补充处理结果）"""
    try:
        from db_model import Intervention
        inv = Intervention.query.get(inv_id)
        if not inv:
            return jsonify({'code': 404, 'msg': '记录不存在'})

        data = request.get_json(silent=True) or {}
        if 'type' in data:
            inv.type = data['type']
        if 'description' in data:
            inv.description = data['description']
        if 'result' in data:
            inv.result = data['result']
        if 'operator' in data:
            inv.operator = data['operator']

        db.session.commit()
        return jsonify({'code': 0, 'msg': '更新成功'})
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/interventions/<int:inv_id>', methods=['DELETE'])
def api_interventions_delete(inv_id):
    """删除干预记录"""
    try:
        from db_model import Intervention
        inv = Intervention.query.get(inv_id)
        if not inv:
            return jsonify({'code': 404, 'msg': '记录不存在'})
        db.session.delete(inv)
        db.session.commit()
        return jsonify({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/interventions/stats', methods=['GET'])
def api_interventions_stats():
    """干预记录统计：总数 + 各类型计数"""
    try:
        from db_model import Intervention
        from sqlalchemy import func
        total = Intervention.query.count()
        type_counts = db.session.query(
            Intervention.type, func.count(Intervention.id)
        ).group_by(Intervention.type).all()

        stats = {'total': total}
        for t, cnt in type_counts:
            stats[t] = cnt
        # 确保常见类型都有值
        for t in ['调薪', '转岗', '面谈', '培训', '其他']:
            if t not in stats:
                stats[t] = 0

        return jsonify({'code': 0, 'data': stats})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/interventions/employee/<int:emp_id>', methods=['GET'])
def api_interventions_employee(emp_id):
    """获取某员工的完整信息 + 全部干预记录（时间线数据）"""
    try:
        from db_model import Intervention
        # 查员工基本信息
        emp = db.session.query(
            EmployeeBase, JobDetail, AttritionRisk
        ).outerjoin(
            JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        ).outerjoin(
            AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
        ).filter(
            EmployeeBase.EmployeeNumber == emp_id
        ).first()

        if not emp:
            return jsonify({'code': 404, 'msg': '员工不存在'})

        e, j, a = emp
        employee_info = {
            'employee_number': e.EmployeeNumber,
            'age': e.Age or 0,
            'department': (e.Department or '').strip(),
            'job_role': j.JobRole if j else '',
            'monthly_income': int(j.MonthlyIncome) if j and j.MonthlyIncome else 0,
            'years_at_company': int(a.YearsAtCompany) if a and a.YearsAtCompany else 0,
            'gender': e.Gender or '',
            'marital_status': e.MaritalStatus or '',
            'overtime': a.OverTime if a else '',
            'job_satisfaction': a.JobSatisfaction if a else 0,
            'work_life_balance': a.WorkLifeBalance if a else 0,
        }

        # 获取该员工全部干预记录（时间倒序）
        interventions_list = Intervention.query.filter_by(
            employee_id=emp_id
        ).order_by(Intervention.created_at.desc()).all()

        timeline = [{
            'id': inv.id,
            'type': inv.type,
            'description': inv.description or '',
            'result': inv.result or '',
            'operator': inv.operator or '',
            'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S') if inv.created_at else '',
        } for inv in interventions_list]

        # 尝试获取最近风险评分（如果有预测数据）
        risk_level = ''
        try:
            df_check = pd.read_sql(
                f"SELECT * FROM employee_base WHERE EmployeeNumber = {emp_id}", db.engine)
            if not df_check.empty:
                # 用 batch_predict 获取评分
                for col in feature_names:
                    if col not in df_check.columns:
                        df_check[col] = 0
                probs = batch_predict(df_check[feature_names].copy())
                prob = probs[0]
                risk_level = '高风险' if prob >= 0.7 else '中风险' if prob >= 0.3 else '低风险'
        except:
            pass

        return jsonify({'code': 0, 'data': {
            'employee': employee_info,
            'interventions': timeline,
            'risk_level': risk_level,
            'total_interventions': len(timeline),
        }})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


@predict_bp.route('/api/interventions/effectiveness', methods=['GET'])
def api_interventions_effectiveness():
    """干预效果统计：对比已干预 vs 未干预的高风险员工离职率"""
    try:
        from db_model import Intervention

        # 1. 获取所有员工数据 + 预测评分
        results = db.session.query(
            EmployeeBase.EmployeeNumber, EmployeeBase.Age, EmployeeBase.Gender,
            EmployeeBase.Department, EmployeeBase.DistanceFromHome,
            JobDetail.JobRole, JobDetail.JobLevel, JobDetail.MonthlyIncome,
            JobDetail.TotalWorkingYears,
            AttritionRisk.OverTime, AttritionRisk.JobSatisfaction,
            AttritionRisk.EnvironmentSatisfaction, AttritionRisk.WorkLifeBalance,
            AttritionRisk.YearsAtCompany, AttritionRisk.Attrition,
        ).join(JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
        ).join(AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
        ).all()

        if not results:
            return jsonify({'code': 0, 'data': {
                'intervened': {'total': 0, 'attrition': 0, 'rate': 0},
                'not_intervened': {'total': 0, 'attrition': 0, 'rate': 0},
                'high_risk_total': 0,
                'note': '暂无员工数据',
            }})

        df = pd.DataFrame([{
            'EmployeeNumber': r.EmployeeNumber, 'Age': r.Age, 'Department': r.Department,
            'JobRole': r.JobRole, 'MonthlyIncome': r.MonthlyIncome, 'OverTime': r.OverTime,
            'YearsAtCompany': r.YearsAtCompany, 'TotalWorkingYears': r.TotalWorkingYears,
            'JobSatisfaction': r.JobSatisfaction, 'WorkLifeBalance': r.WorkLifeBalance,
            'EnvironmentSatisfaction': r.EnvironmentSatisfaction,
            'Gender': r.Gender, 'DistanceFromHome': r.DistanceFromHome,
            'JobLevel': r.JobLevel, 'Attrition': r.Attrition,
        } for r in results])

        # 补充缺失特征列
        default_fill = {
            'DailyRate': 800, 'Education': 3, 'HourlyRate': 50, 'JobInvolvement': 3,
            'MonthlyRate': 15000, 'NumCompaniesWorked': 1, 'PercentSalaryHike': 11,
            'PerformanceRating': 3, 'RelationshipSatisfaction': 3, 'StockOptionLevel': 0,
            'TrainingTimesLastYear': 2, 'YearsInCurrentRole': 2, 'YearsSinceLastPromotion': 1,
            'YearsWithCurrManager': 2, 'BusinessTravel': 'Travel_Rarely',
            'MaritalStatus': 'Single', 'EducationField': 'Life Sciences',
        }
        for col, val in default_fill.items():
            if col not in df.columns:
                df[col] = val

        probs = batch_predict(df)
        df['probability'] = probs

        # 2. 筛选高风险（≥70%）
        high_risk = df[df['probability'] >= 0.7].copy()
        if len(high_risk) == 0:
            return jsonify({'code': 0, 'data': {
                'intervened': {'total': 0, 'attrition': 0, 'rate': 0},
                'not_intervened': {'total': 0, 'attrition': 0, 'rate': 0},
                'high_risk_total': 0,
                'note': '当前无高风险员工',
            }})

        # 3. 获取已有干预的员工 ID 集合
        intervened_records = db.session.query(Intervention.employee_id).distinct().all()
        intervened_ids = set(r[0] for r in intervened_records)

        # 4. 分组统计
        intervened = high_risk[high_risk['EmployeeNumber'].astype(int).isin(intervened_ids)]
        not_intervened = high_risk[~high_risk['EmployeeNumber'].astype(int).isin(intervened_ids)]

        def calc(data):
            t = len(data)
            a = int((data['Attrition'].astype(str).str.strip().str.lower().isin(['yes', '1'])).sum()) if t > 0 else 0
            r = round(a / t * 100, 1) if t > 0 else 0
            return {'total': t, 'attrition': a, 'rate': r}

        return jsonify({'code': 0, 'data': {
            'high_risk_total': len(high_risk),
            'intervened': calc(intervened),
            'not_intervened': calc(not_intervened),
        }})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'code': 1, 'msg': str(e)})


# ========== 7. 操作日志 API ==========

@predict_bp.route('/api/logs', methods=['GET'])
def api_logs_list():
    """获取操作日志列表，支持操作人/操作类型/时间范围筛选 + 分页"""
    try:
        from db_model import OperationLog
        from datetime import datetime as dt

        username = request.args.get('username', '')
        action = request.args.get('action', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 15))

        query = OperationLog.query
        if username:
            query = query.filter(OperationLog.username.like(f'%{username}%'))
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
            'username': log.username or '',
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


@predict_bp.route('/api/logs/actions', methods=['GET'])
def api_logs_actions():
    """返回所有操作类型列表（供筛选下拉）"""
    try:
        from db_model import OperationLog
        from sqlalchemy import func
        actions = db.session.query(
            OperationLog.action, func.count(OperationLog.id)
        ).group_by(OperationLog.action).order_by(func.count(OperationLog.id).desc()).all()
        return jsonify({'code': 0, 'data': [{'name': a, 'count': c} for a, c in actions]})
    except Exception as e:
        return jsonify({'code': 1, 'msg': str(e)})