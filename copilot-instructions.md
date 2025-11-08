# AI Coding Agent Instructions

本项目为《山海经》语料与衍生内容的分析与可视化原型：
- 数据来源：`shanhaijing/` 原始分卷文本；结构化分类 CSV 位于 `csv_by_category/` 与英文转写版本 `csv_by_category_English/`；生成的共现结果在根目录多个 `shanhaijing_cooccurrence*.csv`。
- 交互展示（占位）：`streamlit-page.py` 当前为空，需实现基于分类 CSV 与图像的浏览与检索功能。
- 研究/加工流程主要在多个 Notebook 中：切分 (`切分.ipynb`)→ 拼音与转写 (`加拼音.ipynb`)→ prompt 生成 (`获得prompt.ipynb`)→ 图像生成调用百炼 / DashScope (`获得图片.ipynb`)→ 关系与共现分析 (`分析共现.ipynb`, `分析关系.ipynb`).

## 数据结构与约定
CSV 典型列（示例：`csv_by_category/地名/山名.csv`）：`名字, 一级类目, 二级类目, 出处书名, 版本, 描述, prompt, image_path, 显示名字, prompt翻译`。
- 读取时保持原始列名（含中文与空格），勿强行英文化；新增英文辅助列时使用小写蛇形：`pinyin_name`, `english_prompt`。
- `image_path` 为相对路径（如 `地名\山名\桃山.png`），展示层需用 `images/<一级类目>/...` 拼接。
- 英文版本目录文件名包含英文+中文括号，保持原状避免重命名破坏对照关系。

## 关键模式与实现提示
- Notebook 中多次出现硬编码 API Key（例如 `api_key='sk-...'`）。新代码务必改为读取环境变量：PowerShell 设置示例：`$env:DASHSCOPE_API_KEY="你的key"`，Python 获取：`os.getenv("DASHSCOPE_API_KEY")` / `os.getenv("OPENAI_API_KEY")`。
- 批量生成（prompt 或 图像）使用 `ThreadPoolExecutor`；添加：重试（指数退避）、速率限制（time.sleep）与失败日志（记录到 `failed_items.csv`）。
- 拼音处理使用 `pypinyin.lazy_pinyin`; 若需要保留声调可用 `Style.TONE3`；对含罕见字需加异常捕获并原样返回。
- 共现分析：在 `分析共现.ipynb` 中聚合多个分类 CSV；抽取实体时使用去重+排序。迁移到模块时建议封装：`load_category_csv(category_root) -> DataFrame` 与 `compute_cooccurrence(texts: list[str]) -> DataFrame`。
- 图像与 prompt 的生成链路：CSV 中 `prompt`（中文）→ 英文翻译列（`prompt翻译`）→ 传入模型生成更精炼 `actual_prompt` → 保存 URL / 下载到 `images/`。

## 建议的 Streamlit 页面骨架
`streamlit-page.py` 目标：
1. 侧边栏：选择一级类目→二级类目→搜索名字（支持拼音模糊）。
2. 主区：展示表格（分页）、选择行后显示 prompt / 翻译 / 图像。
3. 统计：加载共现 CSV 生成网络图（使用 `networkx` + `pyvis` 或简单度量）。
实现时优先创建工具模块：`data_loader.py`, `analysis.py`, `app_components.py`，减少 Notebook 逻辑重复。

## 环境与依赖（推断）
需要的包：`pandas`, `requests`, `openai`, `dashscope`, `pypinyin`, `streamlit`，以及可能的 `networkx`, `pyvis`（可选）。若转为脚本，请添加 `requirements.txt` 并固定主版本号（例如 `pandas>=2.0,<3.0`）。

## 工作流速览
1. 准备环境：`python -m venv .venv` → 激活 → 安装依赖。
2. 清理敏感信息：扫描 Notebook 中硬编码 Key 并替换为环境变量读取；必要时生成脱敏副本。
3. 将高价值 Notebook 逻辑抽取成 Python 模块以便测试与复用。
4. 实现 `streamlit-page.py` 基础浏览与检索后再扩展分析功能。

## 质量 & 安全
- 禁止再次提交明文 API Key；PR 检查：搜索 `sk-` / `api_key=`。
- 处理大 CSV 时使用 `dtype` / `usecols` 限制内存占用；对嵌套循环改为向量化或集合操作。
- 多线程调用外部 API 时限制最大并发（例如 5-10），防止速率封禁。

## 扩展与后续（低风险优先）
- 添加 `requirements.txt`、`README.md`（现不存在）。
- 增补英文列自动生成脚本：`generate_english_columns.py`。
- 引入简单单元测试：验证 CSV 读取完整性与 prompt 生成函数输出。

## 代理行动准则
- 任何新增脚本须引用现有目录结构，不重排文件命名。
- 优先消除 Notebook 中硬编码、重复代码与手工步骤。
- 小步提交：先数据加载模块，再分析，再前端。
- 变更前若文件 >5MB（大型 Notebook）避免整体重写，仅抽取核心逻辑。

请审阅：是否已有隐藏依赖、计划补充的可视化库或运行目标（例如 Docker 化）未在此列出？反馈后可迭代完善。