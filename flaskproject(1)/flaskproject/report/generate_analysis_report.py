"""
综合离职分析报告生成模块
使用 GridSpec 网格布局，生成包含标题、柱状图、玫瑰图(ECharts)、折线图、结论的 A4 报告
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from report.config import COLORS, A4_SIZE, REPORT_DPI
from db_model import db, EmployeeBase, JobDetail, AttritionRisk

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'reports'))

# ========== pyecharts 玫瑰图颜色（与首页 ECharts 一致） ==========
ROSE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444',
               '#14b8a6', '#f472b6', '#6366f1', '#84cc16', '#f97316']


def get_employee_df(app):
    """JOIN 查询三表并返回 DataFrame —— 所有 API 的数据源"""
    with app.app_context():
        results = db.session.query(
            EmployeeBase.EmployeeNumber,
            EmployeeBase.Age,
            EmployeeBase.Gender,
            EmployeeBase.Department,
            EmployeeBase.record_date,
            JobDetail.JobRole,
            JobDetail.MonthlyIncome,
            JobDetail.TotalWorkingYears,
            AttritionRisk.Attrition,
            AttritionRisk.OverTime,
            AttritionRisk.WorkLifeBalance,
            AttritionRisk.JobSatisfaction,
            AttritionRisk.YearsAtCompany
        ).outerjoin(JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber) \
         .outerjoin(AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber) \
         .all()

        df = pd.DataFrame([{
            'EmployeeNumber': r.EmployeeNumber,
            'Age': r.Age,
            'Gender': r.Gender,
            'Department': r.Department,
            'record_date': r.record_date,
            'JobRole': r.JobRole,
            'MonthlyIncome': r.MonthlyIncome,
            'TotalWorkingYears': r.TotalWorkingYears,
            'Attrition': r.Attrition,
            'OverTime': r.OverTime,
            'WorkLifeBalance': r.WorkLifeBalance,
            'JobSatisfaction': r.JobSatisfaction,
            'YearsAtCompany': r.YearsAtCompany,
        } for r in results])

        return df


def _render_rose_chart(role_dist):
    """
    使用 pyecharts + playwright 渲染 ECharts 玫瑰图，返回 PNG 文件路径
    （与首页 welcome.html 的 rose 图表完全一致）
    """
    from pyecharts.charts import Pie
    from pyecharts import options as opts

    # 构建数据（前10项，其余合并为"其他"）
    names = role_dist.index.tolist()
    counts = role_dist.values.tolist()
    show_count = min(len(names), 10)
    display_names = names[:show_count]
    display_counts = counts[:show_count]
    if len(names) > show_count:
        display_names.append('其他')
        other_count = sum(counts[show_count:])
        display_counts.append(other_count)

    data_pairs = [(name, int(cnt)) for name, cnt in zip(display_names, display_counts)]

    pie = (
        Pie(init_opts=opts.InitOpts(
            width='1050px', height='850px',
            bg_color='#ffffff',
            animation_opts=opts.AnimationOpts(animation=False)
        ))
        .add(
            series_name='离职岗位分布',
            data_pair=data_pairs,
            radius=['12%', '88%'],
            center=['50%', '50%'],
            rosetype='area',
            itemstyle_opts=opts.ItemStyleOpts(
                border_color='#fff', border_width=2, border_radius=4
            ),
            label_opts=opts.LabelOpts(
                position='outer', font_size=22,
                font_weight='bold',
                color='#1a2332',
                formatter='{b}\n{d}%',
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=''),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                trigger='item', formatter='{b}: {c} 人 ({d}%)'
            ),
        )
        .set_colors(ROSE_COLORS)
    )

    os.makedirs(REPORT_DIR, exist_ok=True)
    html_path = os.path.join(REPORT_DIR, '_rose_chart.html')
    png_path = os.path.join(REPORT_DIR, '_rose_chart.png')

    pie.render(html_path)

    # 将 CDN 的 echarts 替换为本地文件，避免网络加载失败
    base_dir = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
    local_echarts = os.path.join(base_dir, 'static', 'js', 'echarts.min.js')

    # 直接内联 echarts.js 内容，避免 file:// 协议的安全限制
    with open(local_echarts, 'r', encoding='utf-8') as f:
        echarts_js = f.read()

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 替换所有CDN引用为内联脚本
    import re
    # 用 lambda 替代 f-string，避免 echarts.js 中的 \d \1 等被 re.sub 误解析
    html_content = re.sub(
        r'<script[^>]*src="https://assets\.pyecharts\.org[^"]*"[^>]*></script>',
        lambda m: '<script>' + echarts_js + '</script>',
        html_content
    )

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 用 playwright 截图
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1050, 'height': 850})
        page.goto('file:///' + html_path.replace('\\', '/'), wait_until='networkidle')
        page.wait_for_timeout(800)  # 等 ECharts 渲染完成
        page.screenshot(path=png_path, full_page=False)
        browser.close()

    return png_path


def generate(app, filters=None):
    """
    生成综合离职分析报告图，保存到 reports/ 目录
    参数:
        app: Flask app 实例（用于 app_context）
        filters: dict, 可选键 'departments'(list), 'risk_level'(str),
                 'date_start'(str), 'date_end'(str), 'compare_mode'(bool)
    返回: 生成的文件路径
    """
    if filters is None:
        filters = {}

    df = get_employee_df(app)

    # ===== 应用筛选条件 =====
    # 部门筛选
    depts = filters.get('departments') or []
    if isinstance(depts, list) and len(depts) > 0:
        df['Department'] = df['Department'].str.strip()
        df = df[df['Department'].isin([d.strip() for d in depts])]

    # 日期范围筛选
    date_start = filters.get('date_start')
    date_end = filters.get('date_end')
    if date_start:
        df = df[pd.to_datetime(df['record_date']) >= pd.to_datetime(date_start)]
    if date_end:
        df = df[pd.to_datetime(df['record_date']) <= pd.to_datetime(date_end) + pd.Timedelta(days=1)]

    # 风险等级筛选（需要先跑 ML 预测）
    risk_level = (filters.get('risk_level') or '').lower()
    if risk_level in ('high', 'mid', 'low'):
        from blueprints.predict import batch_predict, feature_names, categorical_cols, scaler, le_dict, lr, rf
        # 为预测准备特征列
        for col in feature_names:
            if col not in df.columns:
                df[col] = 0
        probs = batch_predict(df[feature_names].copy() if set(feature_names).issubset(df.columns) else df)
        df['probability'] = probs
        df['risk_group'] = df['probability'].apply(
            lambda p: 'high' if p >= 0.7 else ('mid' if p >= 0.3 else 'low'))
        df = df[df['risk_group'] == risk_level]

    # 校验数据是否足够
    if len(df) == 0:
        raise ValueError('当前筛选条件下无匹配数据，请调整筛选条件后重试。')

    # ========== 计算各图表所需数据 ==========

    # 部门离职率（柱状图数据）
    dept_stats = df.groupby('Department').agg(
        total=('EmployeeNumber', 'count'),
        attrition=('Attrition', lambda x: (x == 'Yes').sum())
    )
    dept_stats['rate'] = dept_stats['attrition'] / dept_stats['total'] * 100
    # 过滤掉离职率为 0 的部门
    dept_stats = dept_stats[dept_stats['rate'] > 0]
    dept_stats = dept_stats.sort_values('rate', ascending=False)

    # 离职员工岗位分布（玫瑰图数据——只统计已离职的）
    attrited = df[df['Attrition'] == 'Yes']
    role_dist = attrited['JobRole'].value_counts()

    # 各年龄段离职率趋势（折线图数据）
    df['AgeGroup'] = pd.cut(df['Age'], bins=[18, 25, 30, 35, 40, 45, 50, 55, 60],
                            labels=['18-25', '26-30', '31-35', '36-40',
                                    '41-45', '46-50', '51-55', '56-60'])
    age_stats = df.groupby('AgeGroup', observed=False).agg(
        total=('EmployeeNumber', 'count'),
        attrition=('Attrition', lambda x: (x == 'Yes').sum())
    )
    age_stats['rate'] = age_stats['attrition'] / age_stats['total'] * 100

    # 关键指标
    total_emp_all = len(df)
    total_att = int((df['Attrition'] == 'Yes').sum())
    overall_rate = round(total_att / total_emp_all * 100, 2) if total_emp_all else 0
    highest_role = role_dist.idxmax() if len(role_dist) > 0 else '无'
    overtime_rate = round(
        len(df[(df['OverTime'] == 'Yes') & (df['Attrition'] == 'Yes')]) / max(total_att, 1) * 100, 2)

    # ========== 用 ECharts 渲染玫瑰图 ==========
    rose_png_path = _render_rose_chart(role_dist)

    # ========== 组装报告画布 ==========
    fig = plt.figure(figsize=A4_SIZE)  # A4 竖版
    gs = GridSpec(4, 2, figure=fig, height_ratios=[0.5, 3.8, 2.5, 0.8],
                  width_ratios=[0.8, 1.2],
                  hspace=0.50, wspace=0.25)

    # ===== 区域1：标题区（占满第一行） =====
    simple_mode = filters.get('simple_mode', False)
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis('off')
    ax_title.text(0.5, 0.5, '数据看板汇总' if simple_mode else '员工离职分析报告',
                  fontsize=18, fontweight="bold", ha="center", va="center",
                  color=COLORS['dark'])

    # ===== 环比对比数据准备 =====
    compare_mode = filters.get('compare_mode', False)
    prev_dept_stats = None
    if compare_mode:
        now = pd.Timestamp.now()
        this_month = df[pd.to_datetime(df['record_date']) >= now.replace(day=1)]
        prev_month = df[(pd.to_datetime(df['record_date']) >= (now - pd.DateOffset(months=1)).replace(day=1)) &
                        (pd.to_datetime(df['record_date']) < now.replace(day=1))]
        prev_dept = prev_month.groupby('Department').agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', lambda x: (x == 'Yes').sum()))
        prev_dept['rate'] = prev_dept['attrition'] / prev_dept['total'] * 100
        prev_dept_stats = prev_dept[prev_dept['rate'] > 0]
        # 重新计算本月
        this_dept = this_month.groupby('Department').agg(
            total=('EmployeeNumber', 'count'),
            attrition=('Attrition', lambda x: (x == 'Yes').sum()))
        this_dept['rate'] = this_dept['attrition'] / this_dept['total'] * 100
        dept_stats = this_dept[this_dept['rate'] > 0]
        dept_stats = dept_stats.sort_values('rate', ascending=False)

    # ===== 区域2：第二行左——各部门离职率（柱状图） =====
    ax_bar = fig.add_subplot(gs[1, 0])
    if compare_mode and prev_dept_stats is not None and len(prev_dept_stats) > 0:
        all_depts = sorted(set(dept_stats.index) | set(prev_dept_stats.index))
        x = np.arange(len(all_depts))
        w = 0.35
        this_rates = [dept_stats.loc[d, 'rate'] if d in dept_stats.index else 0 for d in all_depts]
        prev_rates = [prev_dept_stats.loc[d, 'rate'] if d in prev_dept_stats.index else 0 for d in all_depts]
        ax_bar.bar(x - w/2, this_rates, w, color=COLORS['primary'], edgecolor='white', label='本月')
        ax_bar.bar(x + w/2, prev_rates, w, color=COLORS['gray'], edgecolor='white', label='上月')
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(all_depts, rotation=30, ha='right', fontsize=8)
        ax_bar.legend(fontsize=8)
        max_r = max(max(this_rates, default=0), max(prev_rates, default=0))
    else:
        bars = ax_bar.bar(dept_stats.index, dept_stats['rate'],
                          color=COLORS['primary'], edgecolor='white', width=0.6)
        for bar, val in zip(bars, dept_stats['rate']):
            if val > 0:
                ax_bar.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                            f'{val:.1f}%', ha='center', va='bottom', fontsize=9,
                            color=COLORS['dark'])
        ax_bar.set_xticks(range(len(dept_stats.index)))
        ax_bar.set_xticklabels(dept_stats.index, rotation=30, ha='right', fontsize=8)
        max_r = dept_stats['rate'].max()
    ax_bar.set_title('各部门离职率对比' + ('（本月 vs 上月）' if compare_mode else ''), fontsize=11, fontweight='bold', color=COLORS['dark'])
    ax_bar.set_ylabel('离职率 (%)')
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.set_ylim(top=max_r * 1.3 if max_r > 0 else 10)

    # ===== 区域3：第二行右——离职员工岗位分布（ECharts 玫瑰图） =====
    ax_rose = fig.add_subplot(gs[1, 1])
    ax_rose.axis('off')
    rose_img = plt.imread(rose_png_path)
    ax_rose.imshow(rose_img, aspect='equal')
    ax_rose.set_title('离职员工岗位分布', fontsize=11, fontweight='bold',
                      color=COLORS['dark'], pad=8)

    # ===== 区域4：第三行（占满）——各年龄段离职率趋势（折线图） =====
    ax_line = fig.add_subplot(gs[2, :])
    ax_line.plot(age_stats.index.astype(str), age_stats['rate'],
                 marker='o', linewidth=2.5, markersize=9,
                 markerfacecolor='white', markeredgewidth=2,
                 color=COLORS['primary'])
    ax_line.fill_between(range(len(age_stats)), age_stats['rate'],
                         alpha=0.25, color=COLORS['primary'])
    for i, val in enumerate(age_stats['rate']):
        ax_line.annotate(f'{val:.1f}%',
                         (age_stats.index.astype(str)[i], val),
                         textcoords="offset points", xytext=(0, 14),
                         ha='center', fontsize=9, fontweight='bold',
                         color=COLORS['dark'])
    ax_line.set_ylabel('离职率 (%)')
    ax_line.set_title('各年龄段离职率趋势', fontsize=11, fontweight='bold',
                      color=COLORS['dark'])
    ax_line.spines['top'].set_visible(False)
    ax_line.spines['right'].set_visible(False)
    ax_line.grid(axis='y', alpha=0.3)
    ax_line.set_ylim(bottom=0, top=age_stats['rate'].max() * 1.3)
    ax_line.tick_params(axis='x', labelsize=9)

    # ===== 区域5：结论与建议（占满第四行，simple_mode 跳过） =====
    if simple_mode:
        # 直接保存，不画结论
        os.makedirs(REPORT_DIR, exist_ok=True)
        filepath = os.path.join(REPORT_DIR, 'analysis_report.png')
        plt.savefig(filepath, dpi=REPORT_DPI, bbox_inches='tight', pad_inches=0.15)
        plt.close(fig)
        return filepath

    ax_conc = fig.add_subplot(gs[3, :])
    ax_conc.axis('off')
    max_dept = dept_stats.index[0] if len(dept_stats) > 0 else '无'
    max_rate = dept_stats['rate'].iloc[0] if len(dept_stats) > 0 else 0
    second_dept = dept_stats.index[1] if len(dept_stats) > 1 else ''
    second_rate = dept_stats['rate'].iloc[1] if len(dept_stats) > 1 else 0
    max_age = age_stats['rate'].idxmax() if len(age_stats) > 0 else '未知'
    max_age_rate = age_stats['rate'].max() if len(age_stats) > 0 else 0

    conclusion_text = (
        f'综合分析结论：\n'
        f'① 离职率最高部门：{max_dept}（{max_rate:.1f}%），占比远超均值；'
        f'其次为{second_dept}（{second_rate:.1f}%），需同步关注。\n'
        f'② 年龄维度：{max_age}岁年龄段离职率最高（{max_age_rate:.1f}%），中青年骨干流失风险突出。\n'
        f'③ 岗位维度：{highest_role if highest_role != "无" else ""}岗位离职人数最多，建议深挖岗位倦怠因素。\n'
        f'④ 加班因素：加班员工中离职占比{overtime_rate}%，加班管控是降离职率的有效抓手。\n'
        f'\n管理建议：\n'
        f'- 短期：HR对{max_dept}启动紧急留任访谈，1v1了解离职动机；'
        f'优化{max_age}岁员工薪酬带宽与晋升机制。\n'
        f'- 中期：建立岗位轮换制度，减少单一岗位倦怠；'
        f'将加班时长纳入部门考核，倒逼管理改善。\n'
        f'- 长期：构建「薪酬+成长+文化」三位一体留任体系，'
        f'每季度更新离职风险评估报告。'
    )
    ax_conc.text(
        0.02,
        0.5,
        conclusion_text,
        fontsize=10,
        verticalalignment='center',
        color=COLORS['dark'],
    )

    # ===== 为每个子图添加水印 =====
    watermark_text = '内部资料 - 仅限 HR 部门使用'
    watermark_subplots = [ax_title, ax_bar, ax_rose, ax_line, ax_conc]
    for ax in watermark_subplots:
        ax.text(0.5, 0.5, watermark_text,
                transform=ax.transAxes,
                fontsize=16, color=COLORS['dark'],
                alpha=0.06, rotation=30,
                ha='center', va='center',
                fontweight='bold')

    # ===== 保存输出 =====
    os.makedirs(REPORT_DIR, exist_ok=True)
    filepath = os.path.join(REPORT_DIR, 'analysis_report.png')
    plt.savefig(filepath, dpi=REPORT_DPI, bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)

    return filepath


def save_record(app, filepath, file_type, filters=None):
    """写入报告生成记录"""
    import json
    from db_model import db, ReportRecord
    try:
        fsize = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        with app.app_context():
            db.session.add(ReportRecord(
                filename=os.path.basename(filepath),
                file_type=file_type,
                file_size=fsize,
                filters=json.dumps(filters, ensure_ascii=False) if filters else '{}',
                generated_by='系统',
            ))
            db.session.commit()
    except Exception as e:
        print(f'[WARN] 记录写入失败: {e}')
