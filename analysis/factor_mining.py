"""
因素挖掘 - 相关性分析与热力图（去掉 OverTime 后重新分析）
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder

# ===== 解决中文乱码 =====
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 1. 路径处理 ==========
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)
csv_path = os.path.join(project_dir, 'static', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"文件不存在: {csv_path}")

df = pd.read_csv(csv_path)
print(f"✅ 数据加载成功，共 {len(df)} 行，{len(df.columns)} 列")

# ========== 2. 编码所有分类变量（无警告） ==========
le = LabelEncoder()
# ★ 使用 df.dtypes[df.dtypes == 'object'].index 彻底避免警告
categorical_cols = df.dtypes[df.dtypes == 'object'].index

for col in categorical_cols:
    df[col] = le.fit_transform(df[col].astype(str))
print("✅ 分类变量编码完成（无警告）")

# ========== 3. 计算相关系数（排除 OverTime） ==========
all_corr = df.corr()['Attrition'].drop('Attrition').abs().sort_values(ascending=False)

# 排除 OverTime，取 Top 10
filtered_corr = all_corr.drop('OverTime', errors='ignore').head(10)
top_features = filtered_corr.index.tolist()

print("\n🔥 去掉 OverTime 后，与离职最相关的 Top 10 特征：")
for i, (feat, corr) in enumerate(filtered_corr.items(), 1):
    print(f"  {i}. {feat}: {corr:.4f}")

# 对比原相关性的变化（可选）
original_corr = all_corr.copy()
print("\n📌 对比：去掉 OverTime 前后变化（部分特征）")
for feat in ['JobSatisfaction', 'WorkLifeBalance', 'YearsAtCompany']:
    if feat in original_corr:
        old = original_corr[feat]
        new = filtered_corr.get(feat, 0)
        change = new - old
        print(f"   {feat}: 原 {old:.4f} → 新 {new:.4f} (变化 {change:+.4f})")
print(f"   OverTime 已被排除")

# ========== 4. 绘制热力图 ==========
plt.figure(figsize=(10, 8))
sns.heatmap(
    df[top_features + ['Attrition']].corr(),
    annot=True,
    fmt='.3f',
    cmap='coolwarm',
    center=0,
    square=True,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8}
)
plt.title('去掉 OverTime 后 Top 10 特征与离职的相关性热力图', fontsize=16, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()

# ========== 5. 保存 ==========
output_dir = os.path.join(project_dir, 'output')
os.makedirs(output_dir, exist_ok=True)
save_path = os.path.join(output_dir, 'heatmap_without_overtime.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"\n✅ 热力图已保存至: {save_path}")

plt.show()