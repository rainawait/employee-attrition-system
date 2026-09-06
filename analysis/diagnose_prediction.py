"""
诊断脚本：排查预测结果异常的原因
"""
import os
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_dir = os.path.join(BASE_DIR, 'models')

# ========== 加载模型 ==========
lr = joblib.load(os.path.join(model_dir, 'logistic_regression.pkl'))
rf = joblib.load(os.path.join(model_dir, 'random_forest.pkl'))
scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
encoders = joblib.load(os.path.join(model_dir, 'label_encoders.pkl'))
feature_cols = joblib.load(os.path.join(model_dir, 'feature_names.pkl'))
categorical_cols = joblib.load(os.path.join(model_dir, 'categorical_cols.pkl'))

print("=" * 70)
print("🔍 诊断：预测数据流检查")
print("=" * 70)

# ========== 新员工数据 ==========
new_employee = {
    'Age': 28,
    'BusinessTravel': 'Travel_Frequently',
    'DailyRate': 800,
    'Department': 'Sales',
    'DistanceFromHome': 15,
    'Education': 3,
    'EducationField': 'Marketing',
    'EnvironmentSatisfaction': 2,
    'Gender': 'Male',
    'HourlyRate': 50,
    'JobInvolvement': 3,
    'JobLevel': 1,
    'JobRole': 'Sales Executive',
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
    'YearsWithCurrManager': 1
}

df_new = pd.DataFrame([new_employee])

# 补全特征
for col in feature_cols:
    if col not in df_new.columns:
        df_new[col] = 0
df_new = df_new[feature_cols]

print("\n📊 步骤1: 原始数据（部分数值特征）")
for col in ['Age', 'MonthlyIncome', 'TotalWorkingYears', 'YearsAtCompany']:
    print(f"  {col}: {df_new[col].iloc[0]}")

# ========== 编码分类变量 ==========
print("\n📊 步骤2: 分类变量编码")
for col in categorical_cols:
    le = encoders[col]
    val = df_new[col].iloc[0]
    try:
        encoded = le.transform([str(val)])[0]
        df_new[col] = encoded
        print(f"  {col}: '{val}' → {encoded}")
    except ValueError:
        most_common = le.classes_[0]
        print(f"  ⚠️ {col}: '{val}' → 替换为 '{most_common}'")
        df_new[col] = le.transform([most_common])[0]

# ========== 检查编码后的分类值 ==========
print("\n📊 步骤3: 编码后分类特征值")
for col in categorical_cols:
    print(f"  {col}: {df_new[col].iloc[0]}")

# ========== 标准化 ==========
X_scaled = scaler.transform(df_new)

print("\n📊 步骤4: 标准化后的数值（关键检查）")
for i, col in enumerate(feature_cols[:15]):
    val = X_scaled[0][i]
    status = "⚠️ 极端值!" if abs(val) > 5 else "✅"
    print(f"  {col}: {val:.4f} {status}")

# ========== 逻辑回归得分分析 ==========
print("\n📊 步骤5: 逻辑回归特征贡献分析")
contributions = []
for i, col in enumerate(feature_cols):
    contrib = lr.coef_[0][i] * X_scaled[0][i]
    contributions.append((col, contrib))

contrib_df = pd.DataFrame(contributions, columns=['特征', '贡献']).sort_values('贡献', ascending=False)

print("\n推高离职风险（正贡献 Top 5）:")
for _, row in contrib_df.head(5).iterrows():
    print(f"  + {row['特征']}: {row['贡献']:.4f}")

print("\n降低离职风险（负贡献 Top 5）:")
for _, row in contrib_df.tail(5).iterrows():
    print(f"  - {row['特征']}: {row['贡献']:.4f}")

total_score = lr.decision_function(X_scaled)[0]
print(f"\n📊 逻辑回归总得分: {total_score:.4f}")
print(f"   (得分 > 0 表示倾向于离职)")
print(f"   (得分 < 0 表示倾向于留任)")

# ========== 预测概率 ==========
lr_prob = lr.predict_proba(X_scaled)[0][1]
rf_prob = rf.predict_proba(X_scaled)[0][1]

print("\n" + "=" * 70)
print(f"📊 最终预测结果:")
print(f"  逻辑回归: {lr_prob:.1%}")
print(f"  随机森林: {rf_prob:.1%}")
print("=" * 70)

# ========== 诊断建议 ==========
print("\n🔧 诊断建议:")
if abs(total_score) > 10:
    print("  ⚠️ 总得分绝对值过大（>10），说明标准化后的数据存在极端值。")
    print("     请检查步骤4中是否有 |值| > 5 的特征，这些特征主导了预测结果。")
elif lr_prob > 0.9 and rf_prob < 0.5:
    print("  ⚠️ 逻辑回归极高但随机森林中等，说明模型对数据分布敏感。")
    print("     建议取随机森林结果作为参考（更稳健）。")
else:
    print("  ✅ 数据流正常，预测结果可信。")