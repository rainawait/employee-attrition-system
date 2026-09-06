import pandas as pd
# ====== Series 演示 ======
ages = pd.Series([41, 32, 28, 55, 37], name='Age')
print(ages)
print(f"\n平均年龄: {ages.mean()}")
print(f"最大年龄: {ages.max()}")
print(f"最小年龄: {ages.min()}")
print(f"年龄标准差: {ages.std():.2f}")

# ====== DataFrame 演示 ======
df = pd.DataFrame({
    'Name': ['张三', '李四', '王五'],
    'Age': [41, 32, 28],
    'Department': ['Sales', 'R&D', 'HR'],
    'MonthlyIncome': [5993, 2500, 3200]
})
print(df)
print(f"\n形状: {df.shape}")        # (3行, 4列)
print(f"列名: {df.columns.tolist()}")
print(f"数据类型:\n{df.dtypes}")
print(f"\n描述统计:\n{df.describe()}")