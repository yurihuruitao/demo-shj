# 首页全局网络图功能

## 🎯 新增功能

### 1. 全局知识网络可视化
在首页添加了一个超大的交互式网络图，展示《山海经》中所有知识元素之间的关系。

### 2. 可点击的标题导航
"Knowledge Elements" 标题现在可以点击返回首页。

## 🌐 全局网络图特性

### 节点颜色编码
- **红色** (🔴) - 高度连接 (20+ 个连接)
- **橙色** (🟠) - 良好连接 (10-20 个连接)
- **蓝色** (🔵) - 一般连接 (5-10 个连接)
- **灰色** (⚪) - 较少连接 (< 5 个连接)

### 节点大小
- 节点大小根据连接数量动态调整
- 连接越多，节点越大
- 最小 10px，最大 50px

### 性能优化
- **节点限制**: 显示前 500 个最重要的节点
- **智能筛选**: 按连接数排序，优先显示核心实体
- **物理引擎优化**: 使用 Barnes-Hut 算法，迭代次数 200 次
- **边缘透明度**: 半透明边缘 (opacity: 0.3) 减少视觉混乱

## 🎨 视觉设计

### 深色主题
- **背景**: 深蓝渐变 (#1a1a2e → #16213e)
- **节点**: 彩色编码，白色标签
- **边缘**: 半透明灰色连接线

### 信息面板
1. **统计面板**: 显示节点数和连接数
2. **图例面板**: 解释颜色含义
3. **说明横幅**: 交互提示

## 🖱️ 交互功能

### 鼠标操作
- **拖动节点**: 点击并拖动任意节点调整位置
- **拖动背景**: 在空白区域拖动平移视图
- **滚轮缩放**: 放大/缩小网络图
- **悬停显示**: 鼠标悬停节点查看详细信息

### 内置控制
- **导航按钮**: 右上角放大/缩小/适应视图按钮
- **筛选菜单**: 可以筛选特定节点
- **搜索功能**: 可以搜索特定实体

## 📊 数据统计

### 节点选择策略
```python
# 按连接数排序，取前 500 个
sorted_nodes = sorted(node_connections.items(), 
                     key=lambda x: x[1]['count'], 
                     reverse=True)
limited_nodes = dict(sorted_nodes[:500])
```

### 关系过滤
- 过滤"无关"关系
- 去除重复边
- 只保留有效连接

## 🔧 技术实现

### 后端函数
**`network_generator.py`** - `create_global_network_graph()`
```python
def create_global_network_graph(
    df: pd.DataFrame, 
    width: str = "100%", 
    height: str = "800px",
    max_nodes: int = 500
) -> str
```

**参数**:
- `df`: 共现数据 DataFrame
- `width`: 网络图宽度
- `height`: 网络图高度 (默认 800px)
- `max_nodes`: 最大节点数 (默认 500)

### 前端集成
**`app.py`** - 首页路由
```python
@app.route('/')
def index():
    categories = get_category_structure()
    global_network_html = None
    if COOCCURRENCE_DF is not None:
        global_network_html = create_global_network_graph(
            COOCCURRENCE_DF, 
            width="100%", 
            height="800px",
            max_nodes=500
        )
    return render_template('index.html', 
                         categories=categories,
                         global_network_html=global_network_html)
```

### 模板显示
**`templates/index.html`**
```html
{% if global_network_html %}
<div class="global-network-section">
    <h2>🌐 Global Knowledge Network</h2>
    <p class="network-intro">...</p>
    <div class="global-network-wrapper">
        {{ global_network_html|safe }}
    </div>
</div>
{% endif %}
```

## 🎯 标题导航功能

### 修改内容
**`templates/base.html`**
```html
<div class="sidebar-header">
    <a href="{{ url_for('index') }}" class="logo-link">
        <h1>Knowledge Elements</h1>
        <p class="subtitle">山海经知识元</p>
    </a>
</div>
```

### CSS 样式
```css
.sidebar-header .logo-link {
    display: block;
    text-decoration: none;
    color: white;
    transition: opacity 0.2s;
}

.sidebar-header .logo-link:hover {
    opacity: 0.8;
}
```

## 📈 性能指标

### 加载时间
- **数据加载**: ~500ms (启动时一次性加载)
- **图形生成**: ~2-3s (500 节点)
- **渲染时间**: ~1-2s (初次稳定)

### 内存占用
- **节点数据**: ~2-3MB
- **DOM 元素**: ~500 个节点 + 边
- **总内存**: ~50-80MB

### 推荐配置
- **最佳**: 500 节点 (当前默认)
- **可接受**: 1000 节点
- **不推荐**: > 1500 节点 (会卡顿)

## 🎨 样式说明

### 全局网络容器
```css
.global-network-section {
    margin-top: 3rem;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
```

### 深色网络背景
```css
.global-network-container {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
```

## 🚀 使用指南

### 首次访问
1. 打开 http://127.0.0.1:5000
2. 等待 2-3 秒加载网络图
3. 查看统计面板和图例

### 探索网络
1. **查看核心实体**: 红色和橙色节点是最重要的实体
2. **拖动节点**: 调整布局，查看隐藏的连接
3. **缩放视图**: 放大查看细节，缩小查看全局
4. **悬停节点**: 查看实体名称和连接数

### 返回首页
- 点击侧边栏顶部的 "Knowledge Elements" 标题
- 标题悬停时透明度变化，提示可点击

## 🔍 高级功能

### 内置筛选
网络图右上角有筛选菜单：
- 可以按节点类型筛选
- 可以按连接数筛选
- 可以搜索特定实体

### 物理引擎设置
```javascript
"barnesHut": {
    "gravitationalConstant": -15000,  // 斥力
    "centralGravity": 0.1,            // 中心引力
    "springLength": 200,              // 节点间距
    "springConstant": 0.02,           // 弹簧强度
    "damping": 0.15,                  // 阻尼
    "avoidOverlap": 0.2               // 重叠避免
}
```

## 📝 数据来源

### CSV 文件
`shanhaijing_cooccurrence_expanded_result.csv`

### 使用字段
- **名字**: 主实体名称
- **名字（拼音）**: 主实体拼音
- **相关人物**: 相关实体列表 (逗号分隔)
- **相关人物（拼音）**: 相关实体拼音 (逗号分隔)
- **关系**: 关系类型列表 (逗号分隔)

## ⚠️ 注意事项

### 浏览器要求
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Edge 80+
- ⚠️ Safari 13+ (性能较差)
- ❌ IE 11 (不支持)

### 性能建议
1. 关闭其他占用 CPU 的标签页
2. 等待网络图完全稳定后再操作
3. 避免频繁拖动大量节点
4. 如遇卡顿，刷新页面重新加载

### 数据限制
- 当前仅显示前 500 个最重要节点
- 如需查看所有节点，修改 `max_nodes` 参数
- 但不推荐超过 1000 个节点

## 🎉 效果展示

### 首页布局
```
┌─────────────────────────────────────────┐
│  Welcome Section                        │
│  - 标题和简介                           │
│  - 统计卡片                             │
│  - 快速入门                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  🌐 Global Knowledge Network            │
│  ┌─────────────────────────────────┐   │
│  │  📊 Statistics Panel             │   │
│  │  500 Nodes | 1234 Connections   │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  🎨 Color Legend                 │   │
│  │  🔴 🟠 🔵 ⚪                      │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  🔍 Interactive Network          │   │
│  │  [    Nodes and Edges    ]      │   │
│  │  [     Drag & Zoom       ]      │   │
│  │                                  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 📚 相关文档
- `INTERACTIVE_NETWORK.md` - 交互式网络图详细说明
- `CHANGELOG_SPLIT_OCCURRENCES.md` - 原文拆分功能更新日志
- `FEATURES.md` - 完整功能列表

---

**更新时间**: 2025年11月9日  
**新增功能**: 全局网络可视化 + 可点击标题导航  
**影响范围**: 首页、侧边栏标题  
**性能**: 优化至 500 节点，加载时间 2-3秒
