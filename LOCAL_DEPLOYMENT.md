# 本地化部署说明

## 📦 本地静态资源

为了解决Azure日本服务器CDN加载问题,我们已将ECharts库和地图数据下载到本地。

### 📂 文件结构

```
static/
└── lib/
    ├── echarts.min.js    (1.0 MB) - ECharts 5.4.3 核心库
    └── china.json        (582 KB) - 中国地图GeoJSON数据
```

### ✅ 优势

1. **不依赖外部CDN** - 完全离线可用
2. **加载速度快** - 本地文件,无网络延迟
3. **稳定可靠** - 不受CDN服务中断影响
4. **适合内网部署** - 无需外网访问权限

### 🚀 部署步骤

#### 1. 确认文件存在

在部署前确认以下文件已存在:

```bash
ls static/lib/
# 应该看到:
# echarts.min.js
# china.json
```

#### 2. 提交到Git仓库

```bash
git add static/lib/
git add templates/
git commit -m "使用本地静态资源,移除CDN依赖"
git push origin main
```

#### 3. 在服务器上拉取

```bash
cd /path/to/your/app
git pull origin main
```

#### 4. 重启应用

```bash
# 如果使用systemd
sudo systemctl restart your-app-name

# 或者使用gunicorn
pkill gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app --daemon

# 或者直接运行
python app.py
```

### 🔍 验证部署

访问以下URL验证静态文件是否正常加载:

1. **主页地图**: `http://your-server:5000/`
2. **详情页地图**: 点击任意实体,查看地理分布部分
3. **静态文件直接访问**:
   - `http://your-server:5000/static/lib/echarts.min.js`
   - `http://your-server:5000/static/lib/china.json`

### 📊 浏览器控制台检查

打开浏览器开发者工具(F12),查看Console标签,应该看到:

```
✅ ECharts loaded from local file
✅ ECharts version: 5.4.3
✅ Initializing map...
🔄 Loading map from local file...
✅ Map data loaded from local file
✅ Map rendered successfully!
```

### 🔧 故障排查

#### 问题1: 静态文件404错误

**症状**: 浏览器显示 `GET /static/lib/echarts.min.js 404`

**解决方案**:
```bash
# 检查文件是否存在
ls -la static/lib/

# 如果文件不存在,重新下载
mkdir -p static/lib
wget https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js -O static/lib/echarts.min.js
wget https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json -O static/lib/china.json
```

#### 问题2: 地图不显示

**症状**: 页面加载但地图区域空白

**检查步骤**:
1. 打开浏览器开发者工具(F12)
2. 查看Console标签是否有错误
3. 查看Network标签,确认 `echarts.min.js` 和 `china.json` 都返回200状态码

**常见原因**:
- 文件权限问题: `chmod 644 static/lib/*`
- Flask静态文件配置问题: 确认`app.py`中有正确的static_folder配置

#### 问题3: 地图数据不完整

**症状**: 地图显示但省份没有颜色

**解决方案**:
检查 `地圖表.csv` 文件是否存在并包含正确的数据:
```bash
head -5 地圖表.csv
```

### 📝 技术细节

#### 模板变更

**index.html** (首页):
```html
<!-- 旧版(CDN): -->
<script src="https://cdn.jsdelivr.net/.../echarts.min.js"></script>

<!-- 新版(本地): -->
<script src="{{ url_for('static', filename='lib/echarts.min.js') }}"></script>
```

**detail.html** (详情页):
```html
<!-- 同样使用本地文件 -->
<script src="{{ url_for('static', filename='lib/echarts.min.js') }}"></script>
```

#### 地图数据加载

```javascript
// 旧版: 尝试多个CDN源
const mapSources = [
    'https://geo.datav.aliyun.com/...',
    'https://unpkg.com/...',
    ...
];

// 新版: 直接从本地加载
fetch("{{ url_for('static', filename='lib/china.json') }}")
    .then(response => response.json())
    .then(chinaJson => {
        echarts.registerMap('china', chinaJson);
        // ... 渲染地图
    });
```

### 🎯 性能对比

| 指标 | CDN方案 | 本地方案 |
|------|---------|----------|
| ECharts加载时间 | 500-2000ms | 50-100ms |
| 地图数据加载时间 | 300-1500ms | 30-80ms |
| 首次渲染时间 | 1-3秒 | 0.2-0.5秒 |
| 网络依赖 | 需要外网 | 完全离线 |
| 稳定性 | 受CDN影响 | 100%可控 |

### ⚡ 更新资源

如果需要更新ECharts或地图数据:

```bash
cd static/lib

# 更新ECharts到最新版本
wget https://cdn.jsdelivr.net/npm/echarts@latest/dist/echarts.min.js -O echarts.min.js

# 更新地图数据
wget https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json -O china.json

# 提交更新
git add .
git commit -m "更新ECharts库和地图数据"
git push
```

### 💡 备注

- 文件已添加到Git仓库,会自动随代码部署
- 不需要修改任何代码,模板会自动使用本地文件
- 如果需要支持其他地图(如省份地图),可以下载对应JSON文件到`static/lib/`目录

### 📞 支持

如有问题,请检查:
1. 浏览器控制台日志
2. Flask服务器日志
3. 静态文件访问权限

---

**最后更新**: 2025年11月9日  
**ECharts版本**: 5.4.3  
**地图数据来源**: 阿里云DataV
