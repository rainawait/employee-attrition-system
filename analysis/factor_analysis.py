"""
加班 × 满意度 组合分析（含图表）
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

# ===== 解决中文乱码 =====
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ========== 1. 智能路径处理 ==========
# 获取脚本所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))
# 项目根目录（假设脚本在 analysis/ 下）
project_dir = os.path.dirname(base_dir)

# 尝试多个可能的路径
possible_paths = [
    os.path.join(project_dir, 'static', 'WA_Fn-UseC_-HR-Employee-Attrition.csv'),
    os.path.join(project_dir, 'WA_Fn-UseC_-HR-Employee-Attrition.csv'),
    'static/WA_Fn-UseC_-HR-Employee-Attrition.csv',
]

csv_path = None
for p in possible_paths:
    if os.path.exists(p):
        csv_path = p
        break

if csv_path is None:
    raise FileNotFoundError("找不到数据文件，请确认 static/ 目录下是否存在 WA_Fn-UseC_-HR-Employee-Attrition.csv")

# ========== 2. 加载数据 ==========
df = pd.read_csv(csv_path)
df['Attrition_num'] = df['Attrition'].map({'Yes': 1, 'No': 0})
print(f"数据加载成功，共 {len(df)} 行")

# ========== 3. 创建组合字段 ==========
def sat_group(val):
    return '高满意度' if val >= 3 else '低满意度'

def ot_group(val):
    return '加班' if val == 'Yes' else '不加班'

df['JobSatisfaction_group'] = df['JobSatisfaction'].apply(sat_group)
df['OverTime_group'] = df['OverTime'].apply(ot_group)
df['combo'] = df['OverTime_group'] + ' + ' + df['JobSatisfaction_group']

# ========== 4. 分组统计 ==========
combo_stats = df.groupby('combo').agg(
    人数=('Attrition', 'count'),
    离职率=('Attrition_num', 'mean')
).reset_index()
combo_stats['离职率'] = combo_stats['离职率'] * 100
combo_stats = combo_stats.sort_values('离职率', ascending=False)

# ========== 5. 打印输出 ==========
print("\n" + "=" * 55)
print("加班 × 满意度 组合离职率")
print("=" * 55)
for _, row in combo_stats.iterrows():
    bar = '█' * int(row['离职率'] / 2)
    print(f"{row['combo']:30s} | 人数: {row['人数']:4d} | 离职率: {row['离职率']:5.1f}% {bar}")

# ========== 6. 重点对比 ==========
best_combo = df[(df['OverTime_group'] == '不加班') & (df['JobSatisfaction_group'] == '高满意度')]
worst_combo = df[(df['OverTime_group'] == '加班') & (df['JobSatisfaction_group'] == '低满意度')]
overall_rate = df['Attrition_num'].mean() * 100

print("\n" + "=" * 55)
print("重点对比：最好 vs 最差 vs 整体")
print("=" * 55)
print(f"不加班 + 高满意度（最好）: {best_combo['Attrition_num'].mean() * 100:.1f}%")
print(f"加班 + 低满意度（最差）:   {worst_combo['Attrition_num'].mean() * 100:.1f}%")
print(f"整体离职率:                {overall_rate:.1f}%")
print(f"差距（最差 - 最好）:       {(worst_combo['Attrition_num'].mean() - best_combo['Attrition_num'].mean()) * 100:.1f} 个百分点")

# ================================================================
# 绘制条形图
# ================================================================
plt.figure(figsize=(10, 6))

# 颜色：最差=红色，最好=绿色，其他=蓝色
colors = []
for combo in combo_stats['combo']:
    if combo == '加班 + 低满意度':
        colors.append('#ef4444')
    elif combo == '不加班 + 高满意度':
        colors.append('#10b981')
    else:
        colors.append('#3b82f6')

bars = plt.bar(combo_stats['combo'], combo_stats['离职率'], color=colors, edgecolor='black', linewidth=0.8)

# 数据标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 1.5,
             f'{height:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

# 整体离职率参考线
plt.axhline(y=overall_rate, color='red', linestyle='--', linewidth=1.5, label=f'整体离职率 {overall_rate:.1f}%')

plt.title('加班 × 满意度 组合离职率对比', fontsize=16, fontweight='bold')
plt.xlabel('加班 + 满意度', fontsize=12)
plt.ylabel('离职率 (%)', fontsize=12)
plt.xticks(rotation=15, ha='right')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.ylim(0, max(combo_stats['离职率']) + 15)

# 注释（不使用 Emoji）
max_combo = combo_stats.iloc[0]
plt.annotate('最高风险组',
             xy=(max_combo['combo'], max_combo['离职率']),
             xytext=(1, 45),
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=12, color='red', fontweight='bold')

min_combo = combo_stats.iloc[-1]
plt.annotate('最低风险组',
             xy=(min_combo['combo'], min_combo['离职率']),
             xytext=(1, 5),
             arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
             fontsize=12, color='green', fontweight='bold')

plt.tight_layout()

# 保存图片
output_dir = os.path.join(project_dir, 'output')
os.makedirs(output_dir, exist_ok=True)
save_path = os.path.join(output_dir, 'overtime_satisfaction_attrition.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"\n图表已保存至: {save_path}")

plt.show()