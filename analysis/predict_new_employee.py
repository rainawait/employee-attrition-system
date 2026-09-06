"""
任务七：预测新员工离职风险（改进版）
融合了同学的可视化报告 + 我们之前的严格预处理
"""
import os
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_dir = os.path.join(BASE_DIR, 'models')

# ========== 1. 加载模型 ==========
print("📂 加载模型...")
lr = joblib.load(os.path.join(model_dir, 'logistic_regression.pkl'))
rf = joblib.load(os.path.join(model_dir, 'random_forest.pkl'))
scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
encoders = joblib.load(os.path.join(model_dir, 'label_encoders.pkl'))
feature_cols = joblib.load(os.path.join(model_dir, 'feature_names.pkl'))
categorical_cols = joblib.load(os.path.join(model_dir, 'categorical_cols.pkl'))

print(f"✅ 模型加载成功: {len(feature_cols)} 个特征, {len(categorical_cols)} 个分类特征")

# ========== 2. 新员工数据 ==========
new_employee = {
    'Age': 28,
    'DailyRate': 800,
    'DistanceFromHome': 15,
    'Education': 3,
    'EnvironmentSatisfaction': 2,
    'Gender': 'Male',
    'JobInvolvement': 3,
    'JobLevel': 1,
    'JobSatisfaction': 1,
    'MaritalStatus': 'Single',
    'MonthlyIncome': 3500,
    'MonthlyRate': 15000,
    'NumCompaniesWorked': 2,
    'OverTime': 'Yes',
    'PercentSalaryHike': 11,
    'PerformanceRating': 3,
    'RelationshipSatisfaction': 3,
    'StockOptionLevel': 0,
    'TotalWorkingYears': 5,
    'TrainingTimesLastYear': 2,
    'WorkLifeBalance': 2,
    'YearsAtCompany': 1,
    'YearsInCurrentRole': 1,
    'YearsSinceLastPromotion': 0,
    'YearsWithCurrManager': 1,
    'Department': 'Sales',
    'JobRole': 'Sales Executive',
    'EducationField': 'Marketing',
    'BusinessTravel': 'Travel_Frequently'
}

# ========== 3. 构建 DataFrame ==========
df_new = pd.DataFrame([new_employee])

# 只保留模型需要的特征，缺失补默认值
for col in feature_cols:
    if col not in df_new.columns:
        print(f"⚠️ 特征 '{col}' 缺失，填充为 0")
        df_new[col] = 0

df_new = df_new[feature_cols]

# ========== 4. 编码分类变量 ==========
print("\n🔄 编码分类变量...")
for col in categorical_cols:
    le = encoders[col]
    val = df_new[col].iloc[0]
    try:
        df_new[col] = le.transform([str(val)])[0]
        print(f"  ✅ {col}: '{val}' → {df_new[col].iloc[0]}")
    except ValueError:
        # 训练集未出现的类别，用最常见的类别替代
        most_common = le.classes_[0]
        print(f"  ⚠️ {col}: '{val}' 未在训练集中出现，替换为 '{most_common}'")
        df_new[col] = le.transform([most_common])[0]

# 数值列保持不变
print("\n📊 数值特征（保持不变）:")
for col in ['Age', 'MonthlyIncome', 'TotalWorkingYears', 'YearsAtCompany']:
    print(f"  {col}: {df_new[col].iloc[0]}")

# ========== 5. 标准化 ==========
X_scaled = scaler.transform(df_new)

# ========== 6. 预测 ==========
lr_prob = lr.predict_proba(X_scaled)[0][1]
rf_prob = rf.predict_proba(X_scaled)[0][1]
avg_prob = (lr_prob + rf_prob) / 2

# ========== 7. 输出报告 ==========
print("\n" + "=" * 70)
print("🔮 新员工离职风险预测报告")
print("=" * 70)

print(f"""
📋 基本信息:
  年龄: 28岁 | 性别: 男 | 婚姻: 单身
  部门: Sales | 岗位: Sales Executive
  月薪: 3,500 | 司龄: 1年 | 总工龄: 5年
  加班: 是 | 出差: 频繁出差
  工作满意度: 1/4 | 工作生活平衡: 2/4
""")

print(f"📊 模型评分:")
print(f"  逻辑回归:  {lr_prob:.1%}  {'⚠️ 高危!' if lr_prob > 0.5 else '✅ 安全'}")
print(f"  随机森林:  {rf_prob:.1%}  {'⚠️ 高危!' if rf_prob > 0.5 else '✅ 安全'}")
print(f"  综合评分:  {avg_prob:.1%}")

# 风险等级
if avg_prob > 0.7:
    risk_level = "🔴 高危"
    advice = "建议HR立即安排1v1访谈"
elif avg_prob > 0.5:
    risk_level = "🟡 中危"
    advice = "建议纳入观察名单，定期跟进"
elif avg_prob > 0.3:
    risk_level = "🟢 低危"
    advice = "保持现状，关注满意度变化"
else:
    risk_level = "✅ 安全"
    advice = "员工稳定性良好"

print(f"  风险等级:  {risk_level}")
print(f"  建议:      {advice}")

# ========== 8. 风险因子分析 ==========
print("\n" + "-" * 70)
print("🔍 风险因子逐项分析")
print("-" * 70)

risk_factors = []
safe_factors = []

# 定义风险因子检查规则
risk_rules = {
    'OverTime': ('Yes', '经常加班'),
    'BusinessTravel': ('Travel_Frequently', '频繁出差'),
    'MaritalStatus': ('Single', '单身'),
    'JobSatisfaction': (lambda x: x <= 2, '工作满意度偏低'),
    'YearsAtCompany': (lambda x: x <= 2, '司龄短（高流失期）'),
    'MonthlyIncome': (lambda x: x < 5000, '月薪偏低'),
    'WorkLifeBalance': (lambda x: x <= 2, '工作生活平衡差'),
    'EnvironmentSatisfaction': (lambda x: x <= 2, '环境满意度低'),
    'NumCompaniesWorked': (lambda x: x >= 2, '频繁跳槽'),
    'JobLevel': (lambda x: x <= 1, '职级较低'),
}

for col, rule in risk_rules.items():
    if col not in new_employee:
        continue
    val = new_employee[col]
    if callable(rule):
        is_risk = rule(val)
    else:
        is_risk = (val == rule)
    desc = rule[1] if isinstance(rule, tuple) else str(rule)
    if is_risk:
        risk_factors.append(f"⚠️ {col}: {val} → {desc}")
    else:
        safe_factors.append(f"✅ {col}: {val} → 正常")

print("\n【危险信号】")
if risk_factors:
    for f in risk_factors:
        print(f"  {f}")
else:
    print("  ✅ 无明显危险信号")

print("\n【保护因素】")
for f in safe_factors[:5]:  # 只显示前5个
    print(f"  {f}")

# ========== 9. 特征贡献分析（逻辑回归） ==========
print("\n" + "-" * 70)
print("📊 逻辑回归特征贡献分析（Top 5 正/负贡献）")
print("-" * 70)

contributions = []
for i, col in enumerate(feature_cols):
    contrib = lr.coef_[0][i] * X_scaled[0][i]
    contributions.append((col, contrib))

contrib_df = pd.DataFrame(contributions, columns=['特征', '贡献']).sort_values('贡献', ascending=False)

print("\n推高离职风险（正贡献）:")
for _, row in contrib_df.head(5).iterrows():
    print(f"  + {row['特征']}: {row['贡献']:.4f}")

print("\n降低离职风险（负贡献）:")
for _, row in contrib_df.tail(5).iterrows():
    print(f"  - {row['特征']}: {row['贡献']:.4f}")

print("\n" + "=" * 70)
print("📌 预测完成！")