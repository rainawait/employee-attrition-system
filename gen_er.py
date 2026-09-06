"""生成数据库 ER 图"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(22, 14))
ax.set_xlim(0, 22)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_facecolor('#f8f9fa')
fig.patch.set_facecolor('#f8f9fa')

# 实体定义: (x, y, 表名, 中文名, [(字段, 标记), ...])
# PK=主键, FK=外键, NN=非空, U=唯一
entities = [
    (1.0, 8.5, 'users', '用户表', [
        ('id (PK)', ''),
        ('username (U,NN)', ''),
        ('password (NN)', ''),
        ('real_name', ''),
        ('email', ''),
        ('role', ''),
        ('status', ''),
    ]),
    (5.0, 10.5, 'employee_base', '员工基础信息表', [
        ('EmployeeNumber (PK)', ''),
        ('Age', ''),
        ('Gender', ''),
        ('MaritalStatus', ''),
        ('EducationField', ''),
        ('Department', ''),
        ('DistanceFromHome', ''),
        ('record_date', ''),
    ]),
    (5.0, 5.5, 'job_detail', '工作详情表', [
        ('EmployeeNumber (PK,FK)', ''),
        ('JobRole', ''),
        ('JobLevel', ''),
        ('MonthlyIncome', ''),
        ('TotalWorkingYears', ''),
        ('YearsAtCompany', ''),
    ]),
    (5.0, 1.5, 'attrition_risk', '离职风险因素表', [
        ('EmployeeNumber (PK,FK)', ''),
        ('Attrition', ''),
        ('OverTime', ''),
        ('WorkLifeBalance', ''),
        ('JobSatisfaction', ''),
        ('YearsAtCompany', ''),
    ]),
    (17.0, 10.5, 'interventions', '干预措施记录表', [
        ('id (PK)', ''),
        ('employee_id (FK)', ''),
        ('type', ''),
        ('description', ''),
        ('result', ''),
        ('operator', ''),
        ('created_at', ''),
    ]),
    (11.0, 8.5, 'operation_logs', '操作日志表', [
        ('id (PK)', ''),
        ('user_id (FK)', ''),
        ('username', ''),
        ('action (NN)', ''),
        ('target', ''),
        ('detail', ''),
        ('ip', ''),
        ('created_at', ''),
    ]),
    (17.0, 3.5, 'report_records', '报告生成记录表', [
        ('id (PK)', ''),
        ('filename', ''),
        ('file_type', ''),
        ('file_size', ''),
        ('filters (JSON)', ''),
        ('generated_by', ''),
        ('created_at', ''),
    ]),
]

# 关系定义: (from_entity, to_entity, type, label)
relations = [
    ('employee_base', 'job_detail', '1:1', 'EmployeeNumber'),
    ('employee_base', 'attrition_risk', '1:1', 'EmployeeNumber'),
    ('employee_base', 'interventions', '1:N', 'EmployeeNumber → employee_id'),
    ('users', 'operation_logs', '1:N', 'id → user_id'),
]

# 位置查找
entity_pos = {e[2]: (e[0], e[1]) for e in entities}
entity_fields = {e[2]: e[4] for e in entities}
entity_names = {e[2]: (e[3], e[4]) for e in entities}

BOX_W = 3.8
ROW_H = 0.42
HEADER_H = 0.55

def draw_entity(x, y, ename, cname, fields):
    n = len(fields)
    total_h = HEADER_H + n * ROW_H
    color = '#3498db'
    light = '#d6eaf8'

    # 阴影
    shadow = FancyBboxPatch((x + 0.05, y - total_h - 0.05), BOX_W, total_h,
                           boxstyle="round,pad=0.08", facecolor='#00000015',
                           edgecolor='none', zorder=0)
    ax.add_patch(shadow)

    # 主体
    body = FancyBboxPatch((x, y - total_h), BOX_W, total_h,
                         boxstyle="round,pad=0.08", facecolor='white',
                         edgecolor=color, linewidth=2, zorder=2)
    ax.add_patch(body)

    # 表头
    header = FancyBboxPatch((x, y - HEADER_H), BOX_W, HEADER_H,
                           boxstyle="round,pad=0.08", facecolor=color,
                           edgecolor='none', zorder=3)
    ax.add_patch(header)

    # 表名
    ax.text(x + BOX_W/2, y - HEADER_H/2, f'{cname}\n({ename})',
            ha='center', va='center', fontsize=9, fontweight='bold',
            color='white', zorder=4)

    # 字段
    for i, (fname, fmark) in enumerate(fields):
        fy = y - HEADER_H - (i + 0.5) * ROW_H
        # 交替行背景
        if i % 2 == 0:
            stripe = plt.Rectangle((x + 0.05, fy - ROW_H/2), BOX_W - 0.1, ROW_H,
                                   facecolor='#f8fbff', edgecolor='none', zorder=1)
            ax.add_patch(stripe)

        # 字段名
        display = fname
        is_pk = '(PK)' in fname
        is_fk = '(FK)' in fname
        fontweight = 'bold' if (is_pk or is_fk) else 'normal'
        fcolor = '#c0392b' if is_pk else ('#e67e22' if is_fk else '#2c3e50')

        ax.text(x + 0.25, fy, display, ha='left', va='center',
                fontsize=7.5, fontfamily='monospace', fontweight=fontweight,
                color=fcolor, zorder=4)

        # PK/FK 标记
        mark = ''
        if is_pk and is_fk:
            mark = '[PK][FK]'
        elif is_pk:
            mark = '[PK]'
        elif is_fk:
            mark = '[FK]'
        if mark:
            ax.text(x + BOX_W - 0.2, fy, mark, ha='right', va='center',
                   fontsize=8, zorder=4)

        # 分隔线
        if i < n - 1:
            ax.plot([x + 0.15, x + BOX_W - 0.15],
                    [fy - ROW_H/2, fy - ROW_H/2],
                    color='#ecf0f1', linewidth=0.5, zorder=3)

    return x + BOX_W/2, y - total_h/2  # 中心点


# 绘制所有实体
centers = {}
for e in entities:
    cx, cy = draw_entity(e[0], e[1], e[2], e[3], e[4])
    centers[e[2]] = (cx, cy)

# 绘制关系线和标注
relationship_colors = {
    '1:1': '#27ae60',
    '1:N': '#e74c3c',
}

for rel in relations:
    from_e, to_e, rtype, label = rel
    x1, y1 = centers[from_e]
    x2, y2 = centers[to_e]

    color = relationship_colors.get(rtype, '#7f8c8d')

    # 直线连接
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=1.8, alpha=0.7,
            zorder=0)

    # 中点标注关系类型
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + 0.25, rtype, ha='center', va='bottom',
            fontsize=9, fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=color, alpha=0.9), zorder=5)

    # 下方标注关联字段
    ax.text(mx, my - 0.25, label, ha='center', va='top',
            fontsize=7, color='#7f8c8d', style='italic', zorder=5)

# 图例
legend_elements = [
    mpatches.Patch(color='#c0392b', label='PK = 主键 (Primary Key)'),
    mpatches.Patch(color='#e67e22', label='FK = 外键 (Foreign Key)'),
    plt.Line2D([0], [0], color='#27ae60', linewidth=2, label='1:1 关系'),
    plt.Line2D([0], [0], color='#e74c3c', linewidth=2, label='1:N 关系'),
]
ax.legend(handles=legend_elements, loc='lower center', ncol=4,
          fontsize=9, framealpha=0.9, edgecolor='#bdc3c7')

# 标题
ax.text(11, 13.5, '员工离职预警系统 — 数据库 ER 图',
        ha='center', va='center', fontsize=18, fontweight='bold',
        color='#2c3e50')
ax.text(11, 13.0, 'Entity-Relationship Diagram',
        ha='center', va='center', fontsize=11, color='#95a5a6',
        style='italic')

# 保存
output = r'C:\Users\ASUS\OneDrive\Desktop\ER图.png'
plt.tight_layout()
plt.savefig(output, dpi=180, bbox_inches='tight', facecolor='#f8f9fa')
plt.close()
print(f'ER图已保存至: {output}')
