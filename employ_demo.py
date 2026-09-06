import pandas as pd

# 读取static目录下的csv文件
df = pd.read_csv('static/WA_Fn-UseC_-HR-Employee-Attrition - 脏数据.csv')

print(f"数据形状: {df.shape}")
print(f"\n前5行:\n{df.head()}")
print(f"\n后3行:\n{df.tail(3)}")
print(f"\n列名:\n{df.columns.tolist()}")

print("=== 数据基本信息 ===")
df.info()  # 每列的非空数量、数据类型

print("\n=== 数值列统计描述 ===")
print(df.describe())  # count, mean, std, min, 25%, 50%, 75%, max

print("\n=== 缺失值统计 ===")
missing = df.isnull().sum()                # 每列缺失数
missing_pct = (missing / len(df)) * 100    # 缺失率
missing_df = pd.DataFrame({
    '缺失数': missing,
    '缺失率(%)': missing_pct.round(2)
})
print(missing_df[missing_df['缺失数'] > 0])  # 只看有缺失的列

print(f"\n=== 重复行: {df.duplicated().sum()} ===")

# IQR异常检测函数
def detect_outliers_iqr(df, column):
    """用 IQR 四分位距法检测异常值"""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower) | (df[column] > upper)]
    return outliers, lower, upper

