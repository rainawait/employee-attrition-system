# 员工离职预测与风险管理决策支持系统

基于 Flask 的员工离职预测与风险管理决策支持系统，集成机器学习模型、数据分析与可视化看板。

## 项目结构

```
├── app.py                  # 应用入口
├── blueprints/             # 蓝图模块（dashboard、employee、predict、user）
├── models/                 # 机器学习模型（pkl）
├── analysis/               # 数据分析与模型训练脚本
├── report/                 # 报告生成模块
├── reports/                # 生成的报告（PDF、Excel、图片）
├── output/                 # 分析输出（图表、CSV）
├── static/                 # 静态资源（CSS、JS、字体、图片）
├── templates/              # HTML 模板
├── utils/                  # 工具函数
├── db_model.py             # 数据库模型
├── requirements.txt        # 依赖清单
├── convert_to_docx.py      # 文档转换工具
├── gen_doc.py              # 文档生成工具
├── gen_ppt.py              # PPT 生成工具
└── gen_er.py               # ER 图生成工具
```

## 运行方式

```bash
pip install -r requirements.txt
python app.py
```
