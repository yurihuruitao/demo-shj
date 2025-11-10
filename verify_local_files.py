#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证本地静态资源是否正确部署
"""
import os
import json
from pathlib import Path

def check_file(filepath, min_size=0):
    """检查文件是否存在且大小合理"""
    if not os.path.exists(filepath):
        return False, f"❌ 文件不存在: {filepath}"
    
    size = os.path.getsize(filepath)
    if size < min_size:
        return False, f"❌ 文件太小(可能损坏): {filepath} ({size} bytes)"
    
    return True, f"✅ {filepath} ({size:,} bytes)"

def validate_json(filepath):
    """验证JSON文件格式是否正确"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, f"✅ JSON格式正确,包含 {len(str(data))} 字符"
    except Exception as e:
        return False, f"❌ JSON格式错误: {e}"

def main():
    print("=" * 60)
    print("🔍 本地静态资源验证")
    print("=" * 60)
    print()
    
    # 检查目录
    print("📁 检查目录结构...")
    lib_dir = Path("static/lib")
    if lib_dir.exists():
        print(f"✅ static/lib 目录存在")
    else:
        print(f"❌ static/lib 目录不存在!")
        return
    print()
    
    # 检查ECharts
    print("📚 检查 ECharts 库...")
    echarts_path = "static/lib/echarts.min.js"
    status, msg = check_file(echarts_path, min_size=500000)  # 至少500KB
    print(msg)
    
    if status:
        # 检查是否包含echarts关键字
        with open(echarts_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # 读取前1000个字符
            if 'echarts' in content.lower():
                print("✅ 文件内容验证通过")
            else:
                print("⚠️ 文件内容可能不正确")
    print()
    
    # 检查地图数据
    print("🗺️ 检查中国地图数据...")
    china_path = "static/lib/china.json"
    status, msg = check_file(china_path, min_size=100000)  # 至少100KB
    print(msg)
    
    if status:
        status, msg = validate_json(china_path)
        print(msg)
        
        # 检查GeoJSON结构
        with open(china_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'features' in data:
                print(f"✅ 包含 {len(data['features'])} 个地理特征(省份)")
            else:
                print("⚠️ GeoJSON结构可能不正确")
    print()
    
    # 检查模板文件
    print("📄 检查模板文件...")
    templates = ['templates/index.html', 'templates/detail.html']
    for template in templates:
        if os.path.exists(template):
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
                if "url_for('static', filename='lib/echarts.min.js')" in content:
                    print(f"✅ {template} 已更新为使用本地文件")
                else:
                    print(f"⚠️ {template} 可能还在使用CDN")
        else:
            print(f"❌ {template} 不存在")
    print()
    
    # 总结
    print("=" * 60)
    print("📊 验证完成!")
    print("=" * 60)
    print()
    print("💡 提示:")
    print("  1. 确保Flask应用正在运行")
    print("  2. 访问 http://localhost:5000 测试地图")
    print("  3. 打开浏览器控制台查看日志")
    print("  4. 应该看到 '✅ ECharts loaded from local file'")
    print()

if __name__ == '__main__':
    main()
