import pandas as pd
import numpy as np

# 读取原始脏数据
df = pd.read_csv("static/WA_Fn-UseC_-HR-Employee-Attrition - 脏数据.csv")

# ====================== 1. 查看并填充缺失值 ======================
print("===== 缺失值统计查看 =====")
for col in df.columns:
    null_count = df[col].isnull().sum()
    if null_count > 0:
        print(f"{col}: 缺失 {null_count} 条 ({null_count/len(df)*100:.2f}%)")
    else:
        print(f"{col}: 无缺失值")

# 数值列中位数填充
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
for col in numeric_cols:
    df[col] = df[col].fillna(df[col].median())

# 类别列众数填充
cat_cols = df.select_dtypes(include=['object', 'string']).columns
for col in cat_cols:
    df[col] = df[col].fillna(df[col].mode()[0])

# ====================== 删除重复行 ======================
print("\n===== 重复数据处理 =====")
print(f"去重前重复行数：{df.duplicated().sum()}")
df = df.drop_duplicates()
print(f"✅ 已删除重复行，当前总行数：{len(df)}")

# ====================== 2. 标准IQR异常检测函数 ======================
def detect_outliers_iqr(df, column):
    """用 IQR 法检测异常值"""
    Q1 = df[column].quantile(0.25)  # 第一四分位数
    Q3 = df[column].quantile(0.75)  # 第三四分位数
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR          # 下界
    upper = Q3 + 1.5 * IQR          # 上界
    outliers = df[(df[column] < lower) | (df[column] > upper)]
    return outliers, lower, upper

# ====================== 3. 月薪 MonthlyIncome 异常检测+截断 ======================
outliers_money, low_money, high_money = detect_outliers_iqr(df, 'MonthlyIncome')
print("\n===== MonthlyIncome（月薪）异常值检测结果 =====")
print(f"数据合理区间: {low_money:.0f} ~ {high_money:.0f}")
print(f"识别出异常数据条数: {len(outliers_money)}")
print(f"异常数据占全部样本比例: {len(outliers_money)/len(df)*100:.2f}%\n")

# 对月薪异常值进行截断修正
df['MonthlyIncome'] = np.clip(df['MonthlyIncome'], low_money, high_money)
print(f"已将MonthlyIncome极端值截断至范围 [{low_money:.0f}, {high_money:.0f}]\n")

# ====================== 4. 总工龄 TotalWorkingYears 异常检测+截断 ======================
outliers_year, low_year, high_year = detect_outliers_iqr(df, 'TotalWorkingYears')
print("===== TotalWorkingYears（总工龄）异常值检测结果 =====")
print(f"数据合理区间: {low_year:.0f} ~ {high_year:.0f}")
print(f"识别出异常数据条数: {len(outliers_year)}")
print(f"异常数据占全部样本比例: {len(outliers_year)/len(df)*100:.2f}%\n")

# 对总工龄异常值进行截断修正
df['TotalWorkingYears'] = np.clip(df['TotalWorkingYears'], low_year, high_year)

# ====================== 5. 两个字段异常数量对比 ======================
print("===== 两个字段异常数据数量对比 =====")
print(f"月薪字段检测到异常条数：{len(outliers_money)}")
print(f"总工龄字段检测到异常条数：{len(outliers_year)}")
diff_num = len(outliers_money) - len(outliers_year)
print(f"两者异常条数差值：{diff_num}")

# ======================  1%/99%分位数批量截断 ======================
print("\n===== 执行1%~99%分位数温和截断（月薪、总工龄、司龄） =====")
clip_cols = ['MonthlyIncome', 'TotalWorkingYears', 'YearsAtCompany']
for col in clip_cols:
    q01 = df[col].quantile(0.01)
    q99 = df[col].quantile(0.99)
    df[col] = np.clip(df[col], q01, q99)
    print(f"√ {col} 已截断至 [{q01:.1f}, {q99:.1f}]")

# ====================== 6. 数据校验 + 保存清洗后文件 ======================
print("\n===== 清洗完成后数据校验信息 =====")
print(f"当前数据集全部缺失值总数: {df.isnull().sum().sum()}")
print(f"数据集中重复行总数: {df.duplicated().sum()}")
print(f"清洗后数据集总记录行数: {len(df)}")

df.to_csv('WA_Fn-UseC_-HR-Employee-Attrition.csv', index=False, encoding="utf-8-sig")
print("\n全部数据清洗流程结束，清洗后的文件已保存")