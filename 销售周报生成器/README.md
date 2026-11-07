# Day21 销售周报生成器
> Python基础阶段总验收项目，仅使用前20天所学知识点开发

## 项目说明
这是学习计划第21天的综合练习项目，完成一个完整的销售数据统计周报生成工具，覆盖Python基础阶段全部核心知识点：
- 文件读写操作
- 异常处理
- 函数封装
- pandas数据读取、清洗、分组统计、排序
- JSON格式处理
- 模块化代码组织

## 目录结构
```
销售周报生成器/
├── data/                  # 原始数据目录
│   └── sales_oct_2026.csv # 模拟销售数据（含脏数据用于练习清洗）
├── src/                   # 源代码目录
│   └── sales_report.py    # 主程序
└── output/                # 输出结果目录
    ├── cleaned_sales.csv  # 清洗后的干净数据
    ├── sales_summary.json # JSON格式统计结果
    └── 销售周报.md        # Markdown格式销售周报
```

## 运行方法
1. 确保已安装pandas依赖：
```bash
pip install pandas openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. 进入src目录运行主程序：
```bash
cd src
python sales_report.py
```

## 功能特性
1. **数据读取**：自动识别utf-8/gbk编码，解决中文乱码问题
2. **数据清洗**：
   - 按订单ID自动去重
   - 自动过滤退款订单
   - 缺失区域填充为"未知区域"
   - 异常数量值用约束倒推优先、中位数兜底
   - 日期格式自动转换
3. **统计分析**：
   - 核心指标汇总（总销售额、订单数、客单价）
   - 区域维度销售统计+占比计算
   - 销售员业绩排名
   - 产品类别销售统计
   - 热销产品TOP10排名
4. **结果导出**：
   - 导出清洗后干净的CSV数据
   - 导出JSON格式完整统计结果
   - 自动生成结构化Markdown周报

## 知识点对照（前20天所学）
| 知识点 | 对应代码位置 |
|--------|-------------|
| Day15 文件操作 | load_data、export_report函数中的文件读写 |
| Day16 异常处理 | load_data中的try/except、主程序全局异常捕获 |
| Day17 pip包管理 | pandas依赖安装 |
| Day18 pandas入门 | pd.read_csv、df.head/shape/columns、筛选、分组统计、排序 |
| Day19 pandas进阶 | drop_duplicates去重、fillna缺失值填充、类型转换、布尔索引筛选 |
| Day20 JSON处理 | json.dump导出JSON统计报告 |


