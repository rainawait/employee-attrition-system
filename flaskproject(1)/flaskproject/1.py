import pandas as pd

# 读取数据
df = pd.read_csv('static/WA_Fn-UseC_-HR-Employee-Attrition.csv')

# 将离职标签转为数值：Yes -> 1, No -> 0
df['Attrition_num'] = df['Attrition'].map({'Yes': 1, 'No': 0})

# ========== 1. 性别 vs 离职率 ==========
gender_stats = df.groupby('Gender')['Attrition_num'].mean() * 100
print("=== 性别 vs 离职率 ===")
print(gender_stats.round(2))
print()

# ========== 2. 婚姻状态 vs 离职率 ==========
marital_stats = df.groupby('MaritalStatus')['Attrition_num'].mean() * 100
print("=== 婚姻状态 vs 离职率 ===")
print(marital_stats.round(2))
print()

# ========== 3. 出差频率 vs 离职率 ==========
# 注意：原始字段名为 BusinessTravel，可能包含 'Travel_Rarely', 'Travel_Frequently', 'Non-Travel'
travel_stats = df.groupby('BusinessTravel')['Attrition_num'].mean() * 100
print("=== 出差频率 vs 离职率 ===")
print(travel_stats.round(2))