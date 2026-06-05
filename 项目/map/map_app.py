# -*- coding: utf-8 -*-

import requests
import json
import io
import math
from flask import Flask, request, jsonify, render_template_string, send_file
app = Flask(__name__)

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>地址坐标展示</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: #f5f5f5;
            height: 100vh;
            overflow: hidden;
        }
        .main-layout {
            display: flex;
            height: 100vh;
        }
        /* 左侧地址列表 */
        .sidebar {
            width: 320px;
            min-width: 320px;
            max-width: 320px;
            background: white;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            transition: width 0.3s ease, min-width 0.3s ease, max-width 0.3s ease;
            position: relative;
        }
        .sidebar.collapsed {
            width: 0;
            min-width: 0;
            max-width: 0;
            overflow: hidden;
            border-right: none;
        }
        /* 折叠按钮 */
        .sidebar-toggle {
            position: fixed;
            left: 320px;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            z-index: 1000;
            box-shadow: 2px 0 8px rgba(0,0,0,0.15);
            transition: left 0.3s ease;
        }
        .sidebar-toggle:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        .sidebar-toggle .arrow {
            transition: transform 0.3s ease;
        }
        /* 当侧边栏收起时，按钮移到最左边 */
        body:has(.sidebar.collapsed) .sidebar-toggle {
            left: 0;
        }
        body:has(.sidebar.collapsed) .sidebar-toggle .arrow {
            transform: rotate(180deg);
        }
        .sidebar-header {
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            flex-shrink: 0;
        }
        .sidebar-header h2 {
            font-size: 16px;
            margin-bottom: 10px;
        }
        .input-tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }
        .input-tab {
            padding: 5px 10px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            color: white;
        }
        .input-tab.active {
            background: rgba(255,255,255,0.3);
        }
        .input-group {
            display: flex;
            gap: 5px;
        }
        .input-group input {
            flex: 1;
            padding: 8px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
        }
        .input-group textarea {
            flex: 1;
            padding: 8px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            min-height: 100px;
            resize: vertical;
            font-family: inherit;
        }
        .input-group button {
            padding: 8px 12px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .input-group button:hover {
            background: rgba(255,255,255,0.3);
        }
        .error {
            color: #ff6b6b;
            font-size: 11px;
            margin-top: 5px;
            display: none;
        }
        .address-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        .address-item {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 8px;
            border-left: 3px solid #667eea;
            font-size: 12px;
            overflow: hidden;
        }
        .address-item > div {
            flex: 1;
            min-width: 0;
            overflow: hidden;
        }
        .address-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 3px;
            word-wrap: break-word;
            word-break: break-all;
            overflow-wrap: break-word;
        }
        .address-coords {
            color: #999;
            font-size: 10px;
        }
        .delete-btn {
            background: #ff4757;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        }
        .route-controls {
            padding: 10px;
            border-top: 1px solid #eee;
            background: #fafafa;
        }
        .route-controls select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 8px;
        }
        .route-buttons {
            display: flex;
            gap: 5px;
        }
        .route-buttons button {
            flex: 1;
            padding: 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        }
        .route-btn {
            background: #11998e;
            color: white;
        }
        .clear-btn {
            background: #ff6b6b;
            color: white;
        }
        /* 右侧主图区域 */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
        }
        .map-header {
            padding: 15px 20px;
            background: white;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .map-header h1 {
            font-size: 18px;
            color: #333;
        }
        .map-info {
            font-size: 12px;
            color: #666;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 300px;
        }
        /* 地图悬停提示 */
        .map-tooltip {
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 250px;
            word-wrap: break-word;
            display: none;
        }
        .map-tooltip .tooltip-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .map-tooltip .tooltip-coords {
            color: #ccc;
            font-size: 10px;
        }
        /* 路线详情模态框 */
        .route-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .route-modal-content {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .route-modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .route-modal-header h2 {
            font-size: 18px;
            margin: 0;
        }
        .route-modal-close {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 24px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            line-height: 1;
        }
        .route-modal-close:hover {
            background: rgba(255,255,255,0.3);
        }
        .route-modal-body {
            padding: 20px;
            max-height: 60vh;
            overflow-y: auto;
        }
        .route-step {
            display: flex;
            align-items: flex-start;
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        .route-step:last-child {
            border-bottom: none;
        }
        .route-step-number {
            width: 32px;
            height: 32px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        }
        .route-step-content {
            flex: 1;
            margin-left: 15px;
        }
        .route-step-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .route-step-coords {
            color: #999;
            font-size: 12px;
        }
        .route-step-distance {
            color: #667eea;
            font-size: 12px;
            margin-top: 3px;
        }
        .route-total {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
            text-align: center;
        }
        .route-detail-btn {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 8px;
        }
        .route-detail-btn:hover {
            box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);
        }
        .map-canvas {
            flex: 1;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            background: #fafafa;
            padding: 20px;
            overflow: auto;
            position: relative;
        }
        .map-wrapper {
            width: 100%;
            min-height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: auto;
            cursor: grab;
        }
        .map-wrapper:active {
            cursor: grabbing;
        }
        .map-wrapper img {
            max-width: none;
            max-height: none;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transform-origin: center center;
            will-change: transform;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }
        .zoom-controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 10;
        }
        .zoom-btn {
            width: 36px;
            height: 36px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .zoom-btn:hover {
            background: #f0f0f0;
        }
        .zoom-level {
            background: white;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .placeholder {
            color: #999;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="main-layout">
        <!-- 左侧边栏 -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h2>📍 地址列表</h2>
                <div class="input-group">
                    <textarea id="addressInput" placeholder="输入地址，支持批量粘贴多个地址&#10;格式1：店铺名 + 制表符/空格 + 地址（直接从Excel/表格复制）&#10;格式2：店铺名|地址（手动输入）&#10;示例：伊人国度旗舰店    杭州市上城区九和中心B栋8楼"></textarea>
                    <button onclick="addAddress()">添加</button>
                </div>
                <div class="error" id="error"></div>
            </div>
            
            <div class="address-list" id="addressList"></div>
            
            <div class="route-controls" id="routeControls" style="display:none;">
                <select id="startPointSelect">
                    <option value="">选择起点生成路线</option>
                    <option value="gps" id="gpsOption">📍 我的当前位置 (点击刷新获取)</option>
                </select>
                <div class="route-buttons">
                    <button class="route-btn" onclick="generateRoute()">生成路线</button>
                    <button class="clear-btn" onclick="clearRoute()">清除</button>
                </div>
            </div>
            
            <div class="import-export-controls">
                <button onclick="exportAddresses()" style="padding:4px 8px;font-size:12px;background:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer;margin-right:5px;">📤 导出地址</button>
                <button onclick="document.getElementById('importFile').click()" style="padding:4px 8px;font-size:12px;background:#2196F3;color:white;border:none;border-radius:4px;cursor:pointer;">📥 导入地址</button>
                <input type="file" id="importFile" accept=".json" style="display:none" onchange="importAddresses(this)">
            </div>
        </div>
        
        <!-- 右侧主图 -->
        <div class="main-content">
            <div class="map-header">
                <div class="map-info" id="mapInfo"></div>
                <h1>🗺️ 坐标位置图</h1>
                <div>
                    <button class="route-detail-btn" id="routeDetailBtn" onclick="showRouteDetails()" style="display:none;">查看路线详情</button>
                </div>
            </div>
            <div class="map-canvas" id="mapCanvas">
                <div class="map-wrapper" id="mapWrapper">
                    <img id="mapImage" src="" style="display:none;" />
                    <span class="placeholder" id="mapPlaceholder">请添加地址查看坐标图</span>
                </div>
                <div class="zoom-controls">
                    <button class="zoom-btn" onclick="zoomIn()">+</button>
                    <div class="zoom-level" id="zoomLevel">100%</div>
                    <button class="zoom-btn" onclick="zoomOut()">−</button>
                    <button class="zoom-btn" onclick="resetZoom()" title="重置">⟲</button>
                </div>
                <div class="map-tooltip" id="mapTooltip">
                    <div class="tooltip-name"></div>
                    <div class="tooltip-coords"></div>
                </div>
            </div>
            
            <!-- 路线详情模态框 -->
            <div class="route-modal" id="routeModal" style="display:none;">
                <div class="route-modal-content">
                    <div class="route-modal-header">
                        <h2>🚗 路线详情</h2>
                        <button class="route-modal-close" onclick="closeRouteModal()">×</button>
                    </div>
                    <div class="route-modal-body" id="routeModalBody"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let addresses = [];
        let currentRoute = null;
        let currentZoom = 1;
        let lastFailedAddresses = [];
        const minZoom = 0.5;
        const maxZoom = 5;

        // 侧边栏折叠功能
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
        }

        function generateMapImage() {
            if (addresses.length === 0) {
                document.getElementById('mapImage').style.display = 'none';
                document.getElementById('mapPlaceholder').style.display = 'block';
                return;
            }

            // 取消之前的请求（如果有）
            if (window._mapRequestAbort) {
                window._mapRequestAbort.abort();
            }
            
            // 创建新的AbortController
            const abortController = new AbortController();
            window._mapRequestAbort = abortController;

            document.getElementById('mapPlaceholder').style.display = 'none';
            document.getElementById('mapImage').style.display = 'block';
            
            // 重置图片状态，移除旧的事件监听器
            const mapImg = document.getElementById('mapImage');
            mapImg.onerror = null;
            mapImg.onload = null;
            
            // 释放旧的blob URL（如果有）
            if (window._lastMapBlobUrl) {
                URL.revokeObjectURL(window._lastMapBlobUrl);
            }

            // 使用POST请求发送数据，避免URL长度限制
            const postData = {
                addresses: addresses,
                route: currentRoute && currentRoute.length > 0 ? currentRoute : [],
                gps_lng: gpsCenter ? gpsCenter.lng : null,
                gps_lat: gpsCenter ? gpsCenter.lat : null
            };

            fetch('/map_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(postData),
                signal: abortController.signal
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`服务器错误: ${response.status}`);
                }
                return response.blob();
            })
            .then(blob => {
                console.log('地图图片大小:', blob.size, '字节, 类型:', blob.type);
                
                if (blob.size === 0) {
                    throw new Error('服务器返回空数据');
                }
                
                const url = URL.createObjectURL(blob);
                window._lastMapBlobUrl = url;
                
                // 使用新函数绑定事件，避免闭包问题
                mapImg.src = url;
                
                mapImg.onerror = function(e) {
                    console.error('地图图片加载失败', e);
                    this.style.display = 'none';
                    document.getElementById('mapPlaceholder').style.display = 'block';
                    document.getElementById('mapPlaceholder').textContent = `地图加载失败 (${blob.size}B)`;
                };
                
                mapImg.onload = function() {
                    console.log('地图加载成功, 尺寸:', this.naturalWidth, 'x', this.naturalHeight);
                    // 自动适配视图，让地图完整显示在可视区域内
                    const canvas = document.getElementById('mapCanvas');
                    const canvasRect = canvas.getBoundingClientRect();
                    const padding = 40;
                    const availableWidth = canvasRect.width - padding * 2;
                    const availableHeight = canvasRect.height - padding * 2;

                    const imgWidth = this.naturalWidth;
                    const imgHeight = this.naturalHeight;

                    const scaleX = availableWidth / imgWidth;
                    const scaleY = availableHeight / imgHeight;
                    const fitScale = Math.min(scaleX, scaleY, 1);

                    // 直接设置图片显示尺寸，让图片自然居中
                    this.style.width = Math.round(imgWidth * fitScale) + 'px';
                    this.style.height = Math.round(imgHeight * fitScale) + 'px';

                    currentZoom = 1;
                    currentTranslateX = 0;
                    currentTranslateY = 0;
                    applyZoom();
                };
            })
            .catch(error => {
                // 忽略AbortError（快速添加时旧请求被取消是正常的）
                if (error.name === 'AbortError') {
                    console.log('请求被取消（正常行为）');
                    return;
                }
                console.error('加载地图失败:', error);
                document.getElementById('mapImage').style.display = 'none';
                document.getElementById('mapPlaceholder').style.display = 'block';
                document.getElementById('mapPlaceholder').textContent = '地图加载失败: ' + error.message;
            });

            }

        // 获取GPS位置并更新地图中心
        let gpsCenter = null;

        function getGPSLocation() {
            if (!navigator.geolocation) {
                alert('浏览器不支持GPS定位');
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    gpsCenter = {
                        lng: position.coords.longitude,
                        lat: position.coords.latitude
                    };
                    console.log('GPS位置:', gpsCenter);

                    const gpsOption = document.getElementById('gpsOption');
                    if (gpsOption) {
                        gpsOption.textContent = '📍 我的当前位置 (' + gpsCenter.lng.toFixed(4) + ', ' + gpsCenter.lat.toFixed(4) + ') ✓';
                    }

                    generateMapImage();
                },
                (error) => {
                    console.log('GPS定位失败:', error.message);
                    let errorMsg = 'GPS定位失败';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg = '请允许浏览器获取位置权限';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg = '位置信息不可用';
                            break;
                        case error.TIMEOUT:
                            errorMsg = '定位超时，请重试';
                            break;
                    }
                    alert(errorMsg);
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }

        // 缩放功能
        function zoomIn() {
            if (currentZoom < maxZoom) {
                currentZoom = Math.min(currentZoom + 0.25, maxZoom);
                applyZoom();
            }
        }
        
        function zoomOut() {
            if (currentZoom > minZoom) {
                currentZoom = Math.max(currentZoom - 0.25, minZoom);
                applyZoom();
            }
        }
        
        function resetZoom() {
            currentZoom = 1;
            currentTranslateX = 0;
            currentTranslateY = 0;
            applyZoom();
        }
        
        function applyZoom() {
            const img = document.getElementById('mapImage');
            if (img.style.display !== 'none') {
                // 同时应用平移和缩放
                img.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px) scale(${currentZoom})`;
                document.getElementById('zoomLevel').textContent = Math.round(currentZoom * 100) + '%';
            }
        }
        
        // 地图拖拽功能 - 使用CSS transform实现实时拖拽
        let isDragging = false;
        let startX, startY;
        let currentTranslateX = 0, currentTranslateY = 0;
        let initialTranslateX = 0, initialTranslateY = 0;
        let mapWrapper, mapImage;
        
        // 初始化地图交互事件（DOM加载完成后执行）
        function initMapInteraction() {
            mapWrapper = document.getElementById('mapWrapper');
            mapImage = document.getElementById('mapImage');
            
            // 滚轮缩放
            mapWrapper.addEventListener('wheel', function(e) {
                e.preventDefault();
                if (e.deltaY < 0) {
                    zoomIn();
                } else {
                    zoomOut();
                }
            });

            mapWrapper.addEventListener('mousedown', function(e) {
                // 如果点击的是按钮或交互元素，不启动拖拽
                if (e.target.closest('.zoom-btn')) return;

                isDragging = true;
                mapWrapper.style.cursor = 'grabbing';
                startX = e.clientX;
                startY = e.clientY;
                initialTranslateX = currentTranslateX;
                initialTranslateY = currentTranslateY;
                e.preventDefault();
            });
        }

        document.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                if (mapWrapper) {
                    mapWrapper.style.cursor = 'grab';
                }
            }
        });

        document.addEventListener('mousemove', function(e) {
            if (!isDragging || !mapImage) return;
            e.preventDefault();

            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;

            currentTranslateX = initialTranslateX + deltaX;
            currentTranslateY = initialTranslateY + deltaY;

            // 应用transform，结合缩放
            const scale = currentZoom;
            mapImage.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px) scale(${scale})`;
        });
        
        // 地图悬停提示
        function setupMapHover() {
            const mapCanvas = document.getElementById('mapCanvas');
            const tooltip = document.getElementById('mapTooltip');
            
            mapCanvas.addEventListener('mouseover', function(e) {
                const hoverArea = e.target.closest('.hover-area');
                if (hoverArea) {
                    const name = hoverArea.getAttribute('data-name');
                    const lng = hoverArea.getAttribute('data-lng');
                    const lat = hoverArea.getAttribute('data-lat');
                    
                    tooltip.querySelector('.tooltip-name').textContent = name;
                    tooltip.querySelector('.tooltip-coords').textContent = `经度: ${lng}, 纬度: ${lat}`;
                    tooltip.style.display = 'block';
                }
            });
            
            mapCanvas.addEventListener('mousemove', function(e) {
                const hoverArea = e.target.closest('.hover-area');
                if (hoverArea && tooltip.style.display === 'block') {
                    // 相对于mapCanvas定位
                    const rect = mapCanvas.getBoundingClientRect();
                    const x = e.clientX - rect.left + 15;
                    const y = e.clientY - rect.top + 15;
                    
                    tooltip.style.left = x + 'px';
                    tooltip.style.top = y + 'px';
                }
            });
            
            mapCanvas.addEventListener('mouseout', function(e) {
                const hoverArea = e.target.closest('.hover-area');
                if (hoverArea) {
                    tooltip.style.display = 'none';
                }
            });
        }
        
        // 打开路线详情页面
        function showRouteDetails() {
            if (!currentRoute || currentRoute.length < 1) return;
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/route_detail';
            form.target = '_blank';

            const addressesInput = document.createElement('input');
            addressesInput.type = 'hidden';
            addressesInput.name = 'addresses';
            addressesInput.value = JSON.stringify(addresses);
            form.appendChild(addressesInput);

            const routeInput = document.createElement('input');
            routeInput.type = 'hidden';
            routeInput.name = 'route';
            routeInput.value = JSON.stringify(currentRoute);
            form.appendChild(routeInput);

            const startIndex = document.getElementById('startPointSelect').value;
            const startInput = document.createElement('input');
            startInput.type = 'hidden';
            startInput.name = 'start';
            startInput.value = startIndex;
            form.appendChild(startInput);

            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
        }
        
        // 关闭路线详情模态框
        function closeRouteModal() {
            document.getElementById('routeModal').style.display = 'none';
        }
        
        // 初始化模态框事件
        function initModalEvents() {
            // 点击模态框外部关闭
            document.getElementById('routeModal').addEventListener('click', function(e) {
                if (e.target === this) {
                    closeRouteModal();
                }
            });
        }
        
        // 更新起点选择下拉框
        function updateStartPointSelect() {
            const select = document.getElementById('startPointSelect');
            const routeControls = document.getElementById('routeControls');
            
            if (addresses.length < 2) {
                routeControls.style.display = 'none';
                return;
            }
            
            routeControls.style.display = 'block';
            
            // 保存当前选择
            const currentSelection = select.value;
            
            // 清空并重新填充
            select.innerHTML = '<option value="">请选择起点地址</option>';
            addresses.forEach((addr, index) => {
                const option = document.createElement('option');
                option.value = index;
                const shopLabel = addr.shop_name ? `【${addr.shop_name}】` : '';
                option.textContent = `${index + 1}. ${shopLabel}${addr.name}`;
                select.appendChild(option);
            });
            
            // 恢复选择
            if (currentSelection && currentSelection < addresses.length) {
                select.value = currentSelection;
            }
        }
        
        // 从地址名称中提取区域（如：上城区、西湖区）
        function extractArea(name) {
            // 先匹配 "杭州市XX区"
            let match = name.match(/杭州市\s*([^\s]*?区|县)/);
            if (match) return match[1].replace(/\s+/g, '');
            // 再匹配 "杭州XX区"（不带"市"）
            match = name.match(/杭州\s*([^\s]*?区|县)/);
            if (match) return match[1].replace(/\s+/g, '');
            // 最后匹配独立的 "XX区" 或 "XX县"
            match = name.match(/([\u4e00-\u9fa5]{2,4}(?:区|县))/);
            return match ? match[1] : '其他区域';
        }

        // 生成路线图 - 按区域分组后使用最近邻算法
        function generateRoute() {
            const startIndex = document.getElementById('startPointSelect').value;

            if (startIndex === '') {
                showError('请先选择起点');
                return;
            }

            if (!addresses || addresses.length < 1) {
                showError('请至少添加1个地址');
                return;
            }

            let startPoint;
            let startName;
            let currentIdx;

            if (startIndex === 'gps') {
                if (!gpsCenter) {
                    showError('GPS位置未获取，请允许定位权限或选择其他起点');
                    return;
                }
                startPoint = { lat: gpsCenter.lat, lng: gpsCenter.lng, name: '当前位置' };
                startName = '当前位置';
                currentIdx = -1;
            } else {
                currentIdx = parseInt(startIndex);
                startPoint = addresses[currentIdx];
                startName = startPoint ? startPoint.name : '未知';
            }

            const route = [];
            const visited = new Set();

            if (currentIdx >= 0) {
                visited.add(currentIdx);
                route.push(currentIdx);
            }

            let currentPos = startPoint;

            // 按区域分组（包含所有地址）
            const areaGroups = {};
            for (let i = 0; i < addresses.length; i++) {
                const area = extractArea(addresses[i].name);
                if (!areaGroups[area]) areaGroups[area] = [];
                areaGroups[area].push(i);
            }

            // 从起点所在区域中移除起点
            if (currentIdx >= 0) {
                const startArea = extractArea(addresses[currentIdx].name);
                if (areaGroups[startArea]) {
                    areaGroups[startArea] = areaGroups[startArea].filter(idx => idx !== currentIdx);
                    if (areaGroups[startArea].length === 0) {
                        delete areaGroups[startArea];
                    }
                }
            }

            // 构建区域顺序：起点区域优先，其余按地理位置就近排列
            const areaOrder = [];
            const remainingAreas = new Set(Object.keys(areaGroups));

            // 找到起点所在的区域
            let startArea = '其他区域';
            if (currentIdx >= 0) {
                startArea = extractArea(addresses[currentIdx].name);
            }

            if (startArea && areaGroups[startArea]) {
                areaOrder.push(startArea);
                remainingAreas.delete(startArea);
            }
            // 如果起点区域不在分组中（如起点是该区唯一地址），
            // 找离起点最近的区域作为第一个
            if (areaOrder.length === 0 && remainingAreas.size > 0) {
                let nearestArea = null;
                let minDist = Infinity;
                for (const nextArea of remainingAreas) {
                    for (const idx of areaGroups[nextArea]) {
                        const dist = calculateDistance(currentPos.lat, currentPos.lng, addresses[idx].lat, addresses[idx].lng);
                        if (dist < minDist) {
                            minDist = dist;
                            nearestArea = nextArea;
                        }
                    }
                }
                if (nearestArea) {
                    areaOrder.push(nearestArea);
                    remainingAreas.delete(nearestArea);
                }
            }

            // 逐区域规划路线
            for (let ai = 0; ai < areaOrder.length; ai++) {
                const area = areaOrder[ai];
                const indices = areaGroups[area];
                const areaVisited = new Set();

                while (areaVisited.size < indices.length) {
                    let nearestIdx = -1;
                    let minDist = Infinity;

                    for (const i of indices) {
                        if (areaVisited.has(i)) continue;

                        const dist = calculateDistance(currentPos.lat, currentPos.lng, addresses[i].lat, addresses[i].lng);

                        if (dist < minDist) {
                            minDist = dist;
                            nearestIdx = i;
                        }
                    }

                    if (nearestIdx === -1) break;

                    areaVisited.add(nearestIdx);
                    visited.add(nearestIdx);
                    route.push(nearestIdx);
                    currentPos = addresses[nearestIdx];
                }

                // 当前区域走完后，找离 currentPos 最近的区域作为下一个
                if (remainingAreas.size > 0) {
                    let nearestArea = null;
                    let minDist = Infinity;
                    for (const nextArea of remainingAreas) {
                        for (const idx of areaGroups[nextArea]) {
                            const dist = calculateDistance(currentPos.lat, currentPos.lng, addresses[idx].lat, addresses[idx].lng);
                            if (dist < minDist) {
                                minDist = dist;
                                nearestArea = nextArea;
                            }
                        }
                    }
                    if (nearestArea) {
                        areaOrder.push(nearestArea);
                        remainingAreas.delete(nearestArea);
                    }
                }
            }

            currentRoute = route;

            const totalDistance = calculateTotalDistance(currentRoute, startIndex === 'gps' ? startPoint : null);
            document.getElementById('mapInfo').textContent = `路线：从${startName}出发，共${currentRoute.length}站，约${totalDistance.toFixed(1)}公里`;
            document.getElementById('routeDetailBtn').style.display = 'inline-block';

            generateMapImage();
        }
        
        // 清除路线
        function clearRoute() {
            currentRoute = null;
            document.getElementById('mapInfo').textContent = '';
            document.getElementById('startPointSelect').value = '';
            document.getElementById('routeDetailBtn').style.display = 'none';
            generateMapImage();
        }
        
        // 计算两点间距离（公里）
        function calculateDistance(lat1, lng1, lat2, lng2) {
            const R = 6371; // 地球半径（公里）
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLng = (lng2 - lng1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLng/2) * Math.sin(dLng/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }
        
        // 计算路线总距离
        function calculateTotalDistance(route, startPoint = null) {
            let total = 0;

            // 如果有起点，计算起点到第一个地址的距离
            if (startPoint && route.length > 0) {
                const first = addresses[route[0]];
                total += calculateDistance(startPoint.lat, startPoint.lng, first.lat, first.lng);
            }

            // 计算地址之间的距离
            for (let i = 0; i < route.length - 1; i++) {
                const p1 = addresses[route[i]];
                const p2 = addresses[route[i + 1]];
                total += calculateDistance(p1.lat, p1.lng, p2.lat, p2.lng);
            }
            return total;
        }

        // 解析批量地址
        function parseAddresses(text) {
            console.log('原始文本:', JSON.stringify(text));
            console.log('文本长度:', text.length);

            // 统一换行符为\\n，然后分割（使用字符串替换兼容所有换行符）
            const normalizedText = text.replace(/\\r\\n/g, '\\n').replace(/\\r/g, '\\n');
            const rawLines = normalizedText.split('\\n');

            console.log('分割后行数:', rawLines.length);

            const addresses = [];

            for (let i = 0; i < rawLines.length; i++) {
                let line = rawLines[i].trim();
                console.log(`行${i}: [${line}]`);

                // 跳过空行
                if (!line) continue;

                // 检测制表符或多个空格分隔的店铺名和地址
                // 匹配：店铺名 + (制表符或2个以上空格) + 地址
                const tabSplit = line.split(/\t+|\s{2,}/);
                if (tabSplit.length >= 2) {
                    // 提取店铺名（第一部分）和地址（剩余部分）
                    const shopName = tabSplit[0].trim();
                    const address = tabSplit.slice(1).join(' ').trim();
                    if (shopName && address && address.length >= 5) {
                        // 格式化为 店铺名|地址
                        addresses.push(`${shopName}|${address}`);
                        console.log('识别到店铺+地址:', shopName, '|', address);
                        continue;
                    }
                }

                // 如果一行内有多个地址（用逗号、句号、分号分隔），再分割
                const subAddresses = line.split(/[。；;，,]+/);

                for (let addr of subAddresses) {
                    addr = addr.trim();
                    // 过滤掉太短的地址（少于5个字符）
                    if (addr && addr.length >= 5) {
                        // 过滤掉纯数字、纯符号等无效内容，必须包含中文或英文
                        if (/[\u4e00-\u9fa5]/.test(addr) || /[a-zA-Z]/.test(addr)) {
                            addresses.push(addr);
                            console.log('识别到地址:', addr);
                        }
                    }
                }
            }

            console.log('总共识别地址数:', addresses.length);
            return addresses;
        }
        
        // 添加地址（自动判断单/批量）
        async function addAddress() {
            const input = document.getElementById('addressInput');
            const text = input.value.trim();
            
            if (!text) {
                showError('请输入地址');
                return;
            }
            
            // 解析地址
            const parsedAddresses = parseAddresses(text);
            
            if (parsedAddresses.length === 0) {
                showError('未识别到有效地址');
                return;
            }
            
            const btn = document.querySelector('.input-group button');
            btn.textContent = '添加中...';
            btn.disabled = true;

            let successCount = 0;
            let failCount = 0;
            let failedAddresses = [];
            const MAX_RETRY = 2;
            const total = parsedAddresses.length;
            const CONCURRENCY = 10;

            // 并发处理 geocode 请求
            async function processOne(address) {
                let shopName = '';
                let addrName = address;
                let geoAddress = address;
                if (address.includes('|')) {
                    const parts = address.split('|');
                    shopName = parts[0].trim();
                    addrName = parts[1].trim();
                    geoAddress = addrName;
                }

                const response = await fetch('/geocode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address: geoAddress })
                });

                const data = await response.json();

                if (data.success) {
                    if (shopName && addresses.some(a => a.shop_name === shopName)) {
                        return true;
                    }
                    addresses.push({
                        name: addrName,
                        shop_name: shopName,
                        full_name: data.display_name || addrName,
                        lng: data.lng,
                        lat: data.lat,
                        area: extractArea(addrName)
                    });
                    return true;
                } else {
                    console.error('地址解析失败:', address, data.message);
                    return false;
                }
            }

            // 分批并发处理
            for (let i = 0; i < parsedAddresses.length; i += CONCURRENCY) {
                const batch = parsedAddresses.slice(i, i + CONCURRENCY);
                document.getElementById('mapInfo').textContent = `正在解析: ${Math.min(i + CONCURRENCY, total)}/${total} (已成功 ${successCount}, 失败 ${failCount})`;
                const results = await Promise.all(batch.map(a => processOne(a).catch(() => false)));
                for (let j = 0; j < results.length; j++) {
                    if (results[j]) {
                        successCount++;
                    } else {
                        failedAddresses.push(batch[j]);
                        failCount++;
                    }
                }
            }

            for (let retryRound = 1; retryRound <= MAX_RETRY && failedAddresses.length > 0; retryRound++) {
                console.log(`--- 第${retryRound}轮重试，共 ${failedAddresses.length} 个失败地址 ---`);
                const stillFailed = [];
                for (const address of failedAddresses) {
                    try {
                        let shopName = '';
                        let addrName = address;
                        let geoAddress = address;
                        if (address.includes('|')) {
                            const parts = address.split('|');
                            shopName = parts[0].trim();
                            addrName = parts[1].trim();
                            geoAddress = addrName;
                        }

                        await new Promise(r => setTimeout(r, 300));

                        const response = await fetch('/geocode', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ address: geoAddress })
                        });

                        const data = await response.json();

                        if (data.success) {
                            if (shopName && addresses.some(a => a.shop_name === shopName)) {
                                successCount++;
                                continue;
                            }
                            addresses.push({
                                name: addrName,
                                shop_name: shopName,
                                full_name: data.display_name || addrName,
                                lng: data.lng,
                                lat: data.lat,
                                area: extractArea(addrName)
                            });
                            successCount++;
                            console.log(`  ✅ 重试成功: ${address}`);
                        } else {
                            stillFailed.push(address);
                        }
                    } catch (error) {
                        stillFailed.push(address);
                    }
                }
                failedAddresses = stillFailed;
            }

            failCount = failedAddresses.length;
            
            updateAddressList();
            generateMapImage();
            input.value = '';
            
            btn.textContent = '添加';
            btn.disabled = false;
            
            // 显示结果
            lastFailedAddresses = failedAddresses;
            if (successCount > 0) {
                if (successCount === 1) {
                    document.getElementById('mapInfo').textContent = '成功添加 1 个地址';
                } else {
                    const failMsg = failCount > 0 ? `，失败 ${failCount} 个` : '';
                    document.getElementById('mapInfo').textContent = `成功添加 ${successCount} 个地址${failMsg}`;
                    if (failCount > 0) {
                        showError(`失败地址: ${failedAddresses.slice(0, 3).join('; ')}${failedAddresses.length > 3 ? '...' : ''}`);
                    }
                }
            } else {
                showError('地址添加失败');
            }
        }

        // 更新地址列表
        function updateAddressList() {
            const list = document.getElementById('addressList');
            if (addresses.length === 0) {
                list.innerHTML = '<div style="text-align:center;color:#999;padding:20px;font-size:12px;">暂无地址</div>';
            } else {
                list.innerHTML = addresses.map((addr, index) => {
                    const shopLabel = addr.shop_name ? `<span style="color:#667eea;">【${addr.shop_name}】</span>` : '';
                    return `
                    <div class="address-item">
                        <div>
                            <div class="address-name">${index + 1}. ${shopLabel}${addr.name}</div>
                            <div class="address-coords">${addr.lng.toFixed(4)}, ${addr.lat.toFixed(4)}</div>
                        </div>
                        <button class="delete-btn" onclick="deleteAddress(${index})">×</button>
                    </div>
                `}).join('');
            }
            
            // 更新起点选择下拉框
            updateStartPointSelect();
            
            // 更新地图信息
            if (addresses.length > 0) {
                document.getElementById('mapInfo').textContent = `共 ${addresses.length} 个地址`;
            } else {
                document.getElementById('mapInfo').textContent = '';
            }
        }

        // 删除地址
        function deleteAddress(index) {
            if (index < 0 || index >= addresses.length) {
                console.error('Invalid index:', index);
                return;
            }
            addresses.splice(index, 1);
            updateAddressList();
            generateMapImage();
        }
  
        // 显示错误
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => { errorDiv.style.display = 'none'; }, 3000);
        }

        // 导出地址到JSON文件
        function exportAddresses() {
            if (addresses.length === 0) {
                showError('没有地址可导出');
                return;
            }
            const data = JSON.stringify(addresses, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'addresses_' + new Date().toISOString().slice(0,10) + '.json';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        // 导入地址从JSON文件
        function importAddresses(fileInput) {
            const file = fileInput.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = JSON.parse(e.target.result);
                    if (!Array.isArray(data)) {
                        showError('文件格式错误：不是地址数组');
                        return;
                    }
                    addresses = data;
                    updateAddressList();
                    generateMapImage();
                    document.getElementById('mapInfo').textContent = `成功导入 ${addresses.length} 个地址`;
                } catch (err) {
                    showError('文件解析失败');
                }
            };
            reader.readAsText(file);
            fileInput.value = '';
        }
        
        // 初始化输入框事件
        function initInputEvents() {
            // 回车键添加
            document.getElementById('addressInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    addAddress();
                }
            });
        }
        
        // 页面加载完成后初始化所有事件
        document.addEventListener('DOMContentLoaded', function() {
            getGPSLocation();
            initMapInteraction();
            setupMapHover();
            initModalEvents();
            initInputEvents();
        });
    </script>
    <!-- 侧边栏折叠按钮 - 放在body内确保始终可见 -->
    <button class="sidebar-toggle" id="sidebarToggle" onclick="toggleSidebar()" title="收起/展开">
        <span class="arrow">◀</span>
    </button>
</body>
</html>
'''

def mercator_project(lon, lat):
    R = 6371000
    x = R * math.radians(lon)
    y = R * math.radians(lat)
    return x, y

def generate_svg_map(addresses, route=None, gps_lng=None, gps_lat=None):
    margin = 60
    
    if not addresses:
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700" shape-rendering="geometricPrecision">']
        svg_parts.append('<rect width="100%" height="100%" fill="white"/>')
        svg_parts.append('<text x="500" y="350" text-anchor="middle" fill="#999" font-size="16">请添加地址，坐标将在此显示</text>')
        svg_parts.append('</svg>')
        return ''.join(svg_parts)
    
    # 过滤掉无效坐标（NaN、None等）
    valid_addresses = []
    for addr in addresses:
        try:
            lng = float(addr.get('lng', 0))
            lat = float(addr.get('lat', 0))
            if math.isnan(lng) or math.isnan(lat) or math.isinf(lng) or math.isinf(lat):
                print(f"  跳过无效坐标: {addr.get('name', '?')} ({lng}, {lat})")
                continue
            valid_addresses.append({
                'name': addr.get('name', ''),
                'lng': lng,
                'lat': lat
            })
        except Exception as e:
            print(f"  跳过解析失败: {addr} - {e}")
            continue
    
    addresses = valid_addresses
    
    if not addresses:
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" viewBox="0 0 1000 700" shape-rendering="geometricPrecision">']
        svg_parts.append('<rect width="100%" height="100%" fill="white"/>')
        svg_parts.append('<text x="500" y="350" text-anchor="middle" fill="#999" font-size="16">无有效地址数据</text>')
        svg_parts.append('</svg>')
        return ''.join(svg_parts)
    
    # 限制最大地址数量，避免SVG过大
    MAX_ADDRESSES = 200
    if len(addresses) > MAX_ADDRESSES:
        print(f"  地址数量过多({len(addresses)})，截取前{MAX_ADDRESSES}个")
        addresses = addresses[:MAX_ADDRESSES]
    
    lngs = [a['lng'] for a in addresses]
    lats = [a['lat'] for a in addresses]
    min_lng, max_lng = min(lngs), max(lngs)
    min_lat, max_lat = min(lats), max(lats)

    if gps_lng is not None and gps_lat is not None:
        center_lng = gps_lng
        center_lat = gps_lat
    else:
        center_lng = (min_lng + max_lng) / 2
        center_lat = (min_lat + max_lat) / 2

    lng_range = max(max_lng - min_lng, 0.01)
    lat_range = max(max_lat - min_lat, 0.01)

    lng_offsets = [abs(a['lng'] - center_lng) for a in addresses]
    lat_offsets = [abs(a['lat'] - center_lat) for a in addresses]
    max_lng_offset = max(lng_offsets) if lng_offsets else 0.01
    max_lat_offset = max(lat_offsets) if lat_offsets else 0.01

    base_width, base_height = 1000, 700
    base_usable_width = base_width - 2 * margin - 100
    base_usable_height = base_height - 2 * margin - 100

    base_scale_x = base_usable_width / lng_range
    base_scale_y = base_usable_height / lat_range
    base_scale = min(base_scale_x, base_scale_y)

    scale_x = (base_usable_width / 2) / max(max_lng_offset, 0.001)
    scale_y = (base_usable_height / 2) / max(max_lat_offset, 0.001)
    scale = min(scale_x, scale_y)

    if scale < base_scale:
        scale = base_scale

    temp_center_x = base_width // 2
    temp_center_y = base_height // 2
    min_cx = temp_center_x - max_lng_offset * scale
    max_cx = temp_center_x + max_lng_offset * scale
    min_cy = temp_center_y - max_lat_offset * scale
    max_cy = temp_center_y + max_lat_offset * scale

    extra_margin = 100
    width = max(base_width, max_cx + margin + extra_margin - min(0, min_cx))
    height = max(base_height, max_cy + margin + extra_margin - min(0, min_cy))
    
    # 限制最大尺寸，避免浏览器无法渲染
    MAX_WIDTH = 8000
    MAX_HEIGHT = 6000
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        print(f"  SVG尺寸过大({width}x{height})，限制为{MAX_WIDTH}x{MAX_HEIGHT}")
        # 按比例缩放
        scale_factor = min(MAX_WIDTH / width, MAX_HEIGHT / height)
        width = int(width * scale_factor)
        height = int(height * scale_factor)
        # 同时调整scale以适应新尺寸
        scale *= scale_factor

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}" shape-rendering="geometricPrecision">']
    svg_parts.append('<rect width="100%" height="100%" fill="white"/>')
    
    center_x = width // 2
    center_y = height // 2
    
    # 绘制地址坐标点 - 简化显示，只显示序号点
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#FF9F43', '#A29BFE']
    
    for i, addr in enumerate(addresses):
        color = colors[i % len(colors)]
        # 计算相对于中心的坐标
        dx = (addr['lng'] - center_lng) * scale
        dy = (addr['lat'] - center_lat) * scale
        
        cx = center_x + dx
        cy = center_y - dy
        
        # 限制精度到2位小数，避免SVG过大和浏览器解析失败
        cx_display = round(cx, 2)
        cy_display = round(cy, 2)

        # 转义XML/SVG特殊字符，防止解析失败
        import html as html_module
        raw_name = addr.get('name', '')
        short_name = raw_name[:20] if len(raw_name) > 20 else raw_name
        safe_name = html_module.escape(str(short_name), quote=True)

        svg_parts.append(f'<g class="map-point">')
        svg_parts.append(f'<text x="{cx_display}" y="{cy_display+3}" text-anchor="middle" fill="{color}" font-size="10" font-weight="bold">{i+1}</text>')
        svg_parts.append(f'<circle cx="{cx_display}" cy="{cy_display}" r="8" fill="transparent" class="hover-area" data-name="{safe_name}" data-lng="{float(addr["lng"]):.4f}" data-lat="{float(addr["lat"]):.4f}"/>')
        svg_parts.append('</g>')

        addr['_cx'] = cx_display
        addr['_cy'] = cy_display
        addr['_color'] = color

    # 绘制GPS位置标记（如果有）
    if gps_lng is not None and gps_lat is not None:
        gps_dx = (gps_lng - center_lng) * scale
        gps_dy = (gps_lat - center_lat) * scale
        gps_cx = round(center_x + gps_dx, 2)
        gps_cy = round(center_y - gps_dy, 2)

        # 绘制GPS位置 - 只显示emoji
        svg_parts.append(f'<text x="{gps_cx}" y="{gps_cy+5}" text-anchor="middle" font-size="16">📍</text>')

    if route and len(route) >= 2:
        # 绘制路线连线 - 双层线条（阴影+主线）增加立体感
        for i in range(len(route) - 1):
            idx1 = route[i]
            idx2 = route[i + 1]
            if idx1 < len(addresses) and idx2 < len(addresses):
                p1 = addresses[idx1]
                p2 = addresses[idx2]
                # 底层阴影线
                svg_parts.append(f'<line x1="{p1["_cx"]}" y1="{p1["_cy"]}" x2="{p2["_cx"]}" y2="{p2["_cy"]}" stroke="rgba(255,107,107,0.25)" stroke-width="5" stroke-linecap="round"/>')
                # 上层主线
                svg_parts.append(f'<line x1="{p1["_cx"]}" y1="{p1["_cy"]}" x2="{p2["_cx"]}" y2="{p2["_cy"]}" stroke="#FF6B6B" stroke-width="2.5" stroke-linecap="round"/>')
                # 绘制箭头
                draw_arrow(svg_parts, p1['_cx'], p1['_cy'], p2['_cx'], p2['_cy'])
        
        # 标记起点和终点
        start_idx = route[0]
        end_idx = route[-1]
        if start_idx < len(addresses):
            start = addresses[start_idx]
            svg_parts.append(f'<circle cx="{start["_cx"]}" cy="{start["_cy"]}" r="16" fill="none" stroke="#00C853" stroke-width="2.5"/>')
            svg_parts.append(f'<text x="{start["_cx"]}" y="{start["_cy"]-22}" text-anchor="middle" fill="#00C853" font-size="12" font-weight="bold">起点</text>')
        if end_idx < len(addresses) and end_idx != start_idx:
            end = addresses[end_idx]
            svg_parts.append(f'<circle cx="{end["_cx"]}" cy="{end["_cy"]}" r="16" fill="none" stroke="#FF1744" stroke-width="2.5"/>')
            svg_parts.append(f'<text x="{end["_cx"]}" y="{end["_cy"]-22}" text-anchor="middle" fill="#FF1744" font-size="12" font-weight="bold">终点</text>')
        
        # 标题
        svg_parts.append(f'<text x="{round(width/2, 2)}" y="35" text-anchor="middle" fill="#333" font-size="20" font-weight="bold">🚗 路线规划图（共{len(route)}站）</text>')

        # 图例说明
        legend_y = round(height - 35, 2)
        svg_parts.append(f'<text x="{round(width/2, 2)}" y="{legend_y}" text-anchor="middle" fill="#666" font-size="12">绿色圆圈=起点 | 红色圆圈=终点</text>')
    else:
        # 标题
        svg_parts.append(f'<text x="{round(width/2, 2)}" y="35" text-anchor="middle" fill="#333" font-size="20" font-weight="bold">📍 坐标位置分布图</text>')

        # 图例说明
        legend_y = round(height - 35, 2)
        svg_parts.append(f'<text x="{round(width/2, 2)}" y="{legend_y}" text-anchor="middle" fill="#666" font-size="12">中心点O为所有地址的平均位置 | 坐标为相对偏移量</text>')
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)

def draw_arrow(svg_parts, x1, y1, x2, y2):
    """绘制箭头"""
    import math
    
    # 计算角度
    angle = math.atan2(y2 - y1, x2 - x1)
    
    # 箭头参数
    arrow_len = 12
    arrow_angle = math.pi / 7
    
    # 箭头终点（在线段70%位置）
    arrow_x = round(x1 + (x2 - x1) * 0.70, 2)
    arrow_y = round(y1 + (y2 - y1) * 0.70, 2)
    
    # 箭头两翼
    x3 = round(arrow_x - arrow_len * math.cos(angle - arrow_angle), 2)
    y3 = round(arrow_y - arrow_len * math.sin(angle - arrow_angle), 2)
    x4 = round(arrow_x - arrow_len * math.cos(angle + arrow_angle), 2)
    y4 = round(arrow_y - arrow_len * math.sin(angle + arrow_angle), 2)
    
    # 箭头主体（填充三角形）
    svg_parts.append(f'<polygon points="{arrow_x},{arrow_y} {x3},{y3} {x4},{y4}" fill="#FF6B6B"/>')
    # 箭头边框（增加立体感）
    svg_parts.append(f'<polygon points="{arrow_x},{arrow_y} {x3},{y3} {x4},{y4}" fill="none" stroke="rgba(200,50,50,0.4)" stroke-width="0.5"/>')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/geocode', methods=['POST'])
def geocode():
    import time
    import re
    data = request.get_json()
    address = data.get('address', '').strip()

    print(f"=== GEOCODE CALLED === address={address}")

    if not address:
        return jsonify({'success': False, 'message': '地址不能为空'})
    
    # 预定义地址库（500+ 常用地址）
    address_db = {
        # 四大直辖市
        '北京': {'lng': 116.407426, 'lat': 39.90423, 'full': '北京市'},
        '天安门': {'lng': 116.397428, 'lat': 39.90923, 'full': '北京市天安门广场'},
        '故宫': {'lng': 116.397058, 'lat': 39.916649, 'full': '北京市故宫'},
        '长城': {'lng': 116.570374, 'lat': 40.430179, 'full': '北京市八达岭长城'},
        '颐和园': {'lng': 116.274286, 'lat': 39.992417, 'full': '北京市颐和园'},
        '圆明园': {'lng': 116.303783, 'lat': 40.009033, 'full': '北京市圆明园'},
        '天坛': {'lng': 116.410640, 'lat': 39.880326, 'full': '北京市天坛公园'},
        '北海公园': {'lng': 116.387917, 'lat': 39.928921, 'full': '北京市北海公园'},
        '雍和宫': {'lng': 116.417163, 'lat': 39.949537, 'full': '北京市雍和宫'},
        '鸟巢': {'lng': 116.395652, 'lat': 39.992865, 'full': '北京市国家体育场(鸟巢)'},
        '水立方': {'lng': 116.387917, 'lat': 39.992865, 'full': '北京市国家游泳中心(水立方)'},
        '北京站': {'lng': 116.427027, 'lat': 39.904721, 'full': '北京站'},
        '北京西站': {'lng': 116.321858, 'lat': 39.904594, 'full': '北京西站'},
        '北京南站': {'lng': 116.383116, 'lat': 39.865543, 'full': '北京南站'},
        '北京北站': {'lng': 116.355583, 'lat': 39.942527, 'full': '北京北站'},
        '北京东站': {'lng': 116.453426, 'lat': 39.904723, 'full': '北京东站'},
        '首都机场': {'lng': 116.608124, 'lat': 40.080353, 'full': '北京首都国际机场'},
        '大兴机场': {'lng': 116.425124, 'lat': 39.511353, 'full': '北京大兴国际机场'},
        '朝阳医院': {'lng': 116.427158, 'lat': 39.922578, 'full': '北京朝阳医院'},
        '协和医院': {'lng': 116.417840, 'lat': 39.914523, 'full': '北京协和医院'},
        '北京大学': {'lng': 116.306203, 'lat': 39.987531, 'full': '北京市北京大学'},
        '清华大学': {'lng': 116.324368, 'lat': 39.999267, 'full': '北京市清华大学'},
        '上海': {'lng': 121.473701, 'lat': 31.230416, 'full': '上海市'},
        '外滩': {'lng': 121.490317, 'lat': 31.239748, 'full': '上海市外滩'},
        '东方明珠': {'lng': 121.495721, 'lat': 31.239703, 'full': '上海市东方明珠塔'},
        '豫园': {'lng': 121.495721, 'lat': 31.227703, 'full': '上海市豫园'},
        '城隍庙': {'lng': 121.495721, 'lat': 31.227703, 'full': '上海市城隍庙'},
        '南京路': {'lng': 121.473701, 'lat': 31.239416, 'full': '上海市南京路步行街'},
        '陆家嘴': {'lng': 121.517721, 'lat': 31.239721, 'full': '上海市浦东新区陆家嘴'},
        '上海站': {'lng': 121.451721, 'lat': 31.248721, 'full': '上海站'},
        '上海虹桥站': {'lng': 121.320721, 'lat': 31.198721, 'full': '上海虹桥站'},
        '上海南站': {'lng': 121.433721, 'lat': 31.148721, 'full': '上海南站'},
        '上海东站': {'lng': 121.543721, 'lat': 31.218721, 'full': '上海东站'},
        '浦东机场': {'lng': 121.805317, 'lat': 31.144312, 'full': '上海浦东国际机场'},
        '虹桥机场': {'lng': 121.335317, 'lat': 31.198312, 'full': '上海虹桥国际机场'},
        '迪士尼': {'lng': 121.670721, 'lat': 31.152721, 'full': '上海市迪士尼度假区'},
        '天津': {'lng': 117.190182, 'lat': 39.125596, 'full': '天津市'},
        '天津站': {'lng': 117.202721, 'lat': 39.150721, 'full': '天津站'},
        '天津西站': {'lng': 117.152721, 'lat': 39.167721, 'full': '天津西站'},
        '滨海机场': {'lng': 117.342721, 'lat': 39.122721, 'full': '天津滨海国际机场'},
        '重庆': {'lng': 106.551556, 'lat': 29.563010, 'full': '重庆市'},
        '解放碑': {'lng': 106.578258, 'lat': 29.559552, 'full': '重庆市解放碑'},
        '洪崖洞': {'lng': 106.582721, 'lat': 29.562721, 'full': '重庆市洪崖洞'},
        '磁器口': {'lng': 106.452721, 'lat': 29.582721, 'full': '重庆市磁器口古镇'},
        '长江索道': {'lng': 106.522721, 'lat': 29.552721, 'full': '重庆市长江索道'},
        '重庆站': {'lng': 106.521721, 'lat': 29.530721, 'full': '重庆站'},
        '重庆北站': {'lng': 106.532721, 'lat': 29.582721, 'full': '重庆北站'},
        '重庆西站': {'lng': 106.482721, 'lat': 29.492721, 'full': '重庆西站'},
        '江北机场': {'lng': 106.652317, 'lat': 29.718312, 'full': '重庆江北国际机场'},
        
        # 省会城市 - 华东
        '杭州': {'lng': 120.155070, 'lat': 30.274082, 'full': '浙江省杭州市'},
        '西湖': {'lng': 120.155070, 'lat': 30.274082, 'full': '浙江省杭州市西湖'},
        '灵隐寺': {'lng': 120.102721, 'lat': 30.242721, 'full': '杭州市灵隐寺'},
        '宋城': {'lng': 120.012721, 'lat': 30.282721, 'full': '杭州市宋城'},
        '千岛湖': {'lng': 119.042721, 'lat': 29.602721, 'full': '杭州市淳安县千岛湖'},
        '杭州站': {'lng': 120.165721, 'lat': 30.273721, 'full': '杭州站'},
        '杭州东站': {'lng': 120.215721, 'lat': 30.291721, 'full': '杭州东站'},
        '萧山机场': {'lng': 120.435317, 'lat': 30.236312, 'full': '杭州萧山国际机场'},
        '下沙': {'lng': 120.325721, 'lat': 30.302721, 'full': '杭州市钱塘区下沙'},
        '下沙经济开发区': {'lng': 120.325721, 'lat': 30.302721, 'full': '杭州市钱塘区下沙经济开发区'},
        '白杨街道': {'lng': 120.382721, 'lat': 30.312721, 'full': '杭州市钱塘区白杨街道'},
        '8号大街': {'lng': 120.392721, 'lat': 30.315721, 'full': '杭州市钱塘区8号大街'},
        '和达创意设计园': {'lng': 120.352721, 'lat': 30.308721, 'full': '杭州市钱塘区和达创意设计园'},
        '钱塘区': {'lng': 120.382721, 'lat': 30.312721, 'full': '浙江省杭州市钱塘区'},
        '宁波': {'lng': 121.549620, 'lat': 29.868336, 'full': '浙江省宁波市'},
        '宁波站': {'lng': 121.551721, 'lat': 29.870721, 'full': '宁波站'},
        '温州': {'lng': 120.699010, 'lat': 28.000575, 'full': '浙江省温州市'},
        '义乌': {'lng': 120.081314, 'lat': 29.306330, 'full': '浙江省金华市义乌市'},
        '乌镇': {'lng': 120.482721, 'lat': 30.742721, 'full': '嘉兴市桐乡市乌镇'},
        '南京': {'lng': 118.796877, 'lat': 32.060255, 'full': '江苏省南京市'},
        '中山陵': {'lng': 118.857721, 'lat': 32.062721, 'full': '南京市中山陵'},
        '明孝陵': {'lng': 118.847721, 'lat': 32.037721, 'full': '南京市明孝陵'},
        '夫子庙': {'lng': 118.787721, 'lat': 32.027721, 'full': '南京市夫子庙'},
        '南京站': {'lng': 118.801721, 'lat': 32.087721, 'full': '南京站'},
        '南京南站': {'lng': 118.802721, 'lat': 31.972721, 'full': '南京南站'},
        '苏州': {'lng': 120.585315, 'lat': 31.298886, 'full': '江苏省苏州市'},
        '拙政园': {'lng': 120.625721, 'lat': 31.322721, 'full': '苏州市拙政园'},
        '周庄': {'lng': 120.842721, 'lat': 31.117721, 'full': '苏州市昆山市周庄'},
        '同里': {'lng': 120.722721, 'lat': 31.207721, 'full': '苏州市吴江区同里'},
        '苏州站': {'lng': 120.621721, 'lat': 31.324721, 'full': '苏州站'},
        '无锡': {'lng': 120.305455, 'lat': 31.491170, 'full': '江苏省无锡市'},
        '太湖': {'lng': 120.152721, 'lat': 31.372721, 'full': '无锡市太湖'},
        '灵山': {'lng': 120.052721, 'lat': 31.472721, 'full': '无锡市灵山胜境'},
        '无锡站': {'lng': 120.311721, 'lat': 31.494721, 'full': '无锡站'},
        '常州': {'lng': 119.973986, 'lat': 31.810616, 'full': '江苏省常州市'},
        '恐龙园': {'lng': 119.972721, 'lat': 31.812721, 'full': '常州市中华恐龙园'},
        '常州站': {'lng': 119.952721, 'lat': 31.782721, 'full': '常州站'},
        '南通': {'lng': 120.864608, 'lat': 32.016245, 'full': '江苏省南通市'},
        '南通站': {'lng': 120.852721, 'lat': 32.012721, 'full': '南通站'},
        '扬州': {'lng': 119.421002, 'lat': 32.393159, 'full': '江苏省扬州市'},
        '瘦西湖': {'lng': 119.402721, 'lat': 32.392721, 'full': '扬州市瘦西湖'},
        '扬州站': {'lng': 119.442721, 'lat': 32.452721, 'full': '扬州站'},
        '徐州': {'lng': 117.284723, 'lat': 34.205768, 'full': '江苏省徐州市'},
        '徐州站': {'lng': 117.202721, 'lat': 34.267721, 'full': '徐州站'},
        '镇江': {'lng': 119.423721, 'lat': 32.202721, 'full': '江苏省镇江市'},
        '金山寺': {'lng': 119.442721, 'lat': 32.212721, 'full': '镇江市金山寺'},
        '镇江站': {'lng': 119.452721, 'lat': 32.187721, 'full': '镇江站'},
        '泰州': {'lng': 119.922721, 'lat': 32.452721, 'full': '江苏省泰州市'},
        '盐城': {'lng': 120.152721, 'lat': 33.352721, 'full': '江苏省盐城市'},
        '淮安': {'lng': 119.022721, 'lat': 33.602721, 'full': '江苏省淮安市'},
        '连云港': {'lng': 119.172721, 'lat': 34.602721, 'full': '江苏省连云港市'},
        '宿迁': {'lng': 118.272721, 'lat': 33.962721, 'full': '江苏省宿迁市'},
        '金华': {'lng': 119.652721, 'lat': 29.107721, 'full': '浙江省金华市'},
        '金华站': {'lng': 119.672721, 'lat': 29.127721, 'full': '金华站'},
        '绍兴': {'lng': 120.572721, 'lat': 30.002721, 'full': '浙江省绍兴市'},
        '鲁迅故里': {'lng': 120.582721, 'lat': 30.002721, 'full': '绍兴市鲁迅故里'},
        '绍兴站': {'lng': 120.562721, 'lat': 30.012721, 'full': '绍兴站'},
        '湖州': {'lng': 120.092721, 'lat': 30.872721, 'full': '浙江省湖州市'},
        '嘉兴': {'lng': 120.752721, 'lat': 30.752721, 'full': '浙江省嘉兴市'},
        '台州': {'lng': 121.122721, 'lat': 28.652721, 'full': '浙江省台州市'},
        '台州站': {'lng': 121.322721, 'lat': 28.652721, 'full': '台州站'},
        '丽水': {'lng': 119.922721, 'lat': 28.452721, 'full': '浙江省丽水市'},
        '衢州': {'lng': 118.872721, 'lat': 28.952721, 'full': '浙江省衢州市'},
        '舟山': {'lng': 122.102721, 'lat': 30.002721, 'full': '浙江省舟山市'},
        '普陀山': {'lng': 122.402721, 'lat': 30.002721, 'full': '舟山市普陀山'},
        '合肥': {'lng': 117.227320, 'lat': 31.820586, 'full': '安徽省合肥市'},
        '合肥站': {'lng': 117.282721, 'lat': 31.878721, 'full': '合肥站'},
        '合肥南站': {'lng': 117.302721, 'lat': 31.672721, 'full': '合肥南站'},
        '黄山': {'lng': 118.162721, 'lat': 29.882721, 'full': '安徽省黄山市'},
        '黄山风景区': {'lng': 118.162721, 'lat': 29.882721, 'full': '黄山市黄山风景区'},
        '黄山站': {'lng': 118.272721, 'lat': 29.712721, 'full': '黄山站'},
        '芜湖': {'lng': 118.433721, 'lat': 31.353721, 'full': '安徽省芜湖市'},
        '芜湖站': {'lng': 118.382721, 'lat': 31.412721, 'full': '芜湖站'},
        '安庆': {'lng': 117.058721, 'lat': 30.543721, 'full': '安徽省安庆市'},
        '安庆站': {'lng': 117.002721, 'lat': 30.492721, 'full': '安庆站'},
        '蚌埠': {'lng': 117.352721, 'lat': 32.917721, 'full': '安徽省蚌埠市'},
        '蚌埠站': {'lng': 117.362721, 'lat': 32.952721, 'full': '蚌埠站'},
        '阜阳': {'lng': 115.812721, 'lat': 32.892721, 'full': '安徽省阜阳市'},
        '阜阳站': {'lng': 115.822721, 'lat': 32.872721, 'full': '阜阳站'},
        '马鞍山': {'lng': 118.512721, 'lat': 31.352721, 'full': '安徽省马鞍山市'},
        '滁州': {'lng': 118.322721, 'lat': 32.302721, 'full': '安徽省滁州市'},
        '六安': {'lng': 116.522721, 'lat': 31.752721, 'full': '安徽省六安市'},
        '宣城': {'lng': 118.752721, 'lat': 30.952721, 'full': '安徽省宣城市'},
        '池州': {'lng': 117.452721, 'lat': 30.652721, 'full': '安徽省池州市'},
        '亳州': {'lng': 115.782721, 'lat': 33.852721, 'full': '安徽省亳州市'},
        '宿州': {'lng': 116.972721, 'lat': 33.652721, 'full': '安徽省宿州市'},
        '福州': {'lng': 119.303147, 'lat': 26.080278, 'full': '福建省福州市'},
        '三坊七巷': {'lng': 119.312721, 'lat': 26.082721, 'full': '福州市三坊七巷'},
        '福州站': {'lng': 119.322721, 'lat': 26.085721, 'full': '福州站'},
        '福州南站': {'lng': 119.422721, 'lat': 25.978721, 'full': '福州南站'},
        '厦门': {'lng': 118.089423, 'lat': 24.479583, 'full': '福建省厦门市'},
        '鼓浪屿': {'lng': 118.372721, 'lat': 24.442721, 'full': '厦门市鼓浪屿'},
        '厦门站': {'lng': 118.112721, 'lat': 24.467721, 'full': '厦门站'},
        '厦门北站': {'lng': 118.032721, 'lat': 24.632721, 'full': '厦门北站'},
        '泉州': {'lng': 118.675721, 'lat': 24.874721, 'full': '福建省泉州市'},
        '泉州站': {'lng': 118.582721, 'lat': 24.972721, 'full': '泉州站'},
        '漳州': {'lng': 117.653721, 'lat': 24.518721, 'full': '福建省漳州市'},
        '漳州站': {'lng': 117.602721, 'lat': 24.512721, 'full': '漳州站'},
        '莆田': {'lng': 119.008721, 'lat': 25.454721, 'full': '福建省莆田市'},
        '莆田站': {'lng': 119.022721, 'lat': 25.432721, 'full': '莆田站'},
        '宁德': {'lng': 119.522721, 'lat': 26.652721, 'full': '福建省宁德市'},
        '宁德站': {'lng': 119.542721, 'lat': 26.672721, 'full': '宁德站'},
        '龙岩': {'lng': 117.022721, 'lat': 25.102721, 'full': '福建省龙岩市'},
        '龙岩站': {'lng': 117.002721, 'lat': 25.092721, 'full': '龙岩站'},
        '三明': {'lng': 117.622721, 'lat': 26.272721, 'full': '福建省三明市'},
        '南平': {'lng': 118.172721, 'lat': 26.642721, 'full': '福建省南平市'},
        
        # 华南地区
        '广州': {'lng': 113.264385, 'lat': 23.129163, 'full': '广东省广州市'},
        '珠江新城': {'lng': 113.332721, 'lat': 23.122721, 'full': '广州市珠江新城'},
        '广州塔': {'lng': 113.318921, 'lat': 23.110592, 'full': '广州市广州塔(小蛮腰)'},
        '白云山': {'lng': 113.282721, 'lat': 23.192721, 'full': '广州市白云山'},
        '长隆': {'lng': 112.972721, 'lat': 22.872721, 'full': '广州市番禺区长隆旅游度假区'},
        '广州站': {'lng': 113.242721, 'lat': 23.154721, 'full': '广州站'},
        '广州东站': {'lng': 113.332721, 'lat': 23.154721, 'full': '广州东站'},
        '广州南站': {'lng': 113.262721, 'lat': 22.989721, 'full': '广州南站'},
        '广州北站': {'lng': 113.192721, 'lat': 23.392721, 'full': '广州北站'},
        '白云机场': {'lng': 113.309312, 'lat': 23.392312, 'full': '广州白云国际机场'},
        '深圳': {'lng': 114.057868, 'lat': 22.543099, 'full': '广东省深圳市'},
        '世界之窗': {'lng': 114.122721, 'lat': 22.542721, 'full': '深圳市世界之窗'},
        '欢乐谷': {'lng': 114.022721, 'lat': 22.542721, 'full': '深圳市欢乐谷'},
        '东部华侨城': {'lng': 114.252721, 'lat': 22.642721, 'full': '深圳市东部华侨城'},
        '深圳站': {'lng': 114.112721, 'lat': 22.532721, 'full': '深圳站'},
        '深圳北站': {'lng': 114.022721, 'lat': 22.620721, 'full': '深圳北站'},
        '深圳东站': {'lng': 114.132721, 'lat': 22.652721, 'full': '深圳东站'},
        '宝安机场': {'lng': 113.814312, 'lat': 22.639312, 'full': '深圳宝安国际机场'},
        '东莞': {'lng': 113.751798, 'lat': 23.048894, 'full': '广东省东莞市'},
        '东莞站': {'lng': 113.882721, 'lat': 22.952721, 'full': '东莞站'},
        '佛山': {'lng': 113.122717, 'lat': 23.028725, 'full': '广东省佛山市'},
        '佛山站': {'lng': 113.022721, 'lat': 23.022721, 'full': '佛山站'},
        '顺德': {'lng': 113.292721, 'lat': 22.822721, 'full': '佛山市顺德区'},
        '珠海': {'lng': 113.562721, 'lat': 22.250721, 'full': '广东省珠海市'},
        '珠海站': {'lng': 113.422721, 'lat': 22.272721, 'full': '珠海站'},
        '横琴': {'lng': 113.482721, 'lat': 22.142721, 'full': '珠海市横琴新区'},
        '中山': {'lng': 113.382721, 'lat': 22.517721, 'full': '广东省中山市'},
        '中山站': {'lng': 113.302721, 'lat': 22.502721, 'full': '中山站'},
        '惠州': {'lng': 114.415721, 'lat': 23.111721, 'full': '广东省惠州市'},
        '惠州站': {'lng': 114.362721, 'lat': 23.092721, 'full': '惠州站'},
        '汕头': {'lng': 116.682721, 'lat': 23.352721, 'full': '广东省汕头市'},
        '汕头站': {'lng': 116.622721, 'lat': 23.372721, 'full': '汕头站'},
        '湛江': {'lng': 110.352721, 'lat': 21.202721, 'full': '广东省湛江市'},
        '湛江站': {'lng': 110.402721, 'lat': 21.192721, 'full': '湛江站'},
        '江门': {'lng': 113.082721, 'lat': 22.578721, 'full': '广东省江门市'},
        '江门站': {'lng': 113.082721, 'lat': 22.592721, 'full': '江门站'},
        '茂名': {'lng': 110.922721, 'lat': 21.662721, 'full': '广东省茂名市'},
        '肇庆': {'lng': 112.452721, 'lat': 23.052721, 'full': '广东省肇庆市'},
        '梅州': {'lng': 116.122721, 'lat': 24.302721, 'full': '广东省梅州市'},
        '阳江': {'lng': 111.982721, 'lat': 21.862721, 'full': '广东省阳江市'},
        '清远': {'lng': 113.022721, 'lat': 23.702721, 'full': '广东省清远市'},
        '韶关': {'lng': 113.562721, 'lat': 24.822721, 'full': '广东省韶关市'},
        '潮州': {'lng': 116.622721, 'lat': 23.652721, 'full': '广东省潮州市'},
        '揭阳': {'lng': 116.372721, 'lat': 23.552721, 'full': '广东省揭阳市'},
        '汕尾': {'lng': 115.372721, 'lat': 22.802721, 'full': '广东省汕尾市'},
        '河源': {'lng': 114.692721, 'lat': 23.752721, 'full': '广东省河源市'},
        '云浮': {'lng': 112.052721, 'lat': 22.902721, 'full': '广东省云浮市'},
        '南宁': {'lng': 108.366096, 'lat': 22.817389, 'full': '广西南宁市'},
        '青秀山': {'lng': 108.422721, 'lat': 22.782721, 'full': '南宁市青秀山'},
        '南宁站': {'lng': 108.312721, 'lat': 22.824721, 'full': '南宁站'},
        '南宁东站': {'lng': 108.472721, 'lat': 22.842721, 'full': '南宁东站'},
        '桂林': {'lng': 110.177721, 'lat': 25.274721, 'full': '广西桂林市'},
        '漓江': {'lng': 110.452721, 'lat': 25.252721, 'full': '桂林市漓江'},
        '阳朔': {'lng': 110.488721, 'lat': 24.783721, 'full': '桂林市阳朔县'},
        '桂林站': {'lng': 110.292721, 'lat': 25.279721, 'full': '桂林站'},
        '桂林北站': {'lng': 110.192721, 'lat': 25.322721, 'full': '桂林北站'},
        '柳州': {'lng': 109.428721, 'lat': 24.326721, 'full': '广西柳州市'},
        '柳州站': {'lng': 109.422721, 'lat': 24.352721, 'full': '柳州站'},
        '北海': {'lng': 109.122721, 'lat': 21.479721, 'full': '广西北海市'},
        '银滩': {'lng': 109.152721, 'lat': 21.442721, 'full': '北海市银滩'},
        '北海站': {'lng': 109.202721, 'lat': 21.552721, 'full': '北海站'},
        '百色': {'lng': 106.622721, 'lat': 23.902721, 'full': '广西百色市'},
        '玉林': {'lng': 110.172721, 'lat': 22.652721, 'full': '广西玉林市'},
        '贵港': {'lng': 109.602721, 'lat': 23.102721, 'full': '广西贵港市'},
        '钦州': {'lng': 108.652721, 'lat': 21.972721, 'full': '广西钦州市'},
        '河池': {'lng': 108.052721, 'lat': 24.702721, 'full': '广西河池市'},
        '贺州': {'lng': 111.552721, 'lat': 24.402721, 'full': '广西贺州市'},
        '来宾': {'lng': 109.222721, 'lat': 23.752721, 'full': '广西来宾市'},
        '崇左': {'lng': 107.372721, 'lat': 22.402721, 'full': '广西崇左市'},
        '防城港': {'lng': 108.352721, 'lat': 21.702721, 'full': '广西防城港市'},
        '梧州': {'lng': 111.272721, 'lat': 23.472721, 'full': '广西梧州市'},
        '海口': {'lng': 110.199890, 'lat': 20.044421, 'full': '海南省海口市'},
        '假日海滩': {'lng': 110.282721, 'lat': 20.002721, 'full': '海口市假日海滩'},
        '海口站': {'lng': 110.282721, 'lat': 20.028721, 'full': '海口站'},
        '三亚': {'lng': 109.511717, 'lat': 18.253305, 'full': '海南省三亚市'},
        '亚龙湾': {'lng': 109.652721, 'lat': 18.212721, 'full': '三亚市亚龙湾'},
        '天涯海角': {'lng': 109.522721, 'lat': 18.292721, 'full': '三亚市天涯海角'},
        '三亚站': {'lng': 109.512721, 'lat': 18.302721, 'full': '三亚站'},
        '三亚凤凰机场': {'lng': 109.412317, 'lat': 18.303312, 'full': '三亚凤凰国际机场'},
        '儋州': {'lng': 109.582721, 'lat': 19.522721, 'full': '海南省儋州市'},
        '文昌': {'lng': 110.753721, 'lat': 19.543721, 'full': '海南省文昌市'},
        '琼海': {'lng': 110.482721, 'lat': 19.252721, 'full': '海南省琼海市'},
        '万宁': {'lng': 110.382721, 'lat': 18.802721, 'full': '海南省万宁市'},
        
        # 华中地区
        '武汉': {'lng': 114.305539, 'lat': 30.593354, 'full': '湖北省武汉市'},
        '黄鹤楼': {'lng': 114.302721, 'lat': 30.552721, 'full': '武汉市黄鹤楼'},
        '户部巷': {'lng': 114.292721, 'lat': 30.552721, 'full': '武汉市户部巷'},
        '武汉站': {'lng': 114.312721, 'lat': 30.613721, 'full': '武汉站'},
        '武汉东站': {'lng': 114.352721, 'lat': 30.473721, 'full': '武汉东站'},
        '汉口站': {'lng': 114.292721, 'lat': 30.617721, 'full': '汉口站'},
        '武昌站': {'lng': 114.312721, 'lat': 30.607721, 'full': '武昌站'},
        '天河机场': {'lng': 114.222317, 'lat': 30.783312, 'full': '武汉天河国际机场'},
        '长沙': {'lng': 112.938814, 'lat': 28.228209, 'full': '湖南省长沙市'},
        '岳麓山': {'lng': 112.942721, 'lat': 28.232721, 'full': '长沙市岳麓山'},
        '橘子洲': {'lng': 112.952721, 'lat': 28.212721, 'full': '长沙市橘子洲'},
        '五一广场': {'lng': 112.972721, 'lat': 28.262721, 'full': '长沙市五一广场'},
        '长沙站': {'lng': 112.938721, 'lat': 28.194721, 'full': '长沙站'},
        '长沙南站': {'lng': 113.062721, 'lat': 28.632721, 'full': '长沙南站'},
        '长沙黄花机场': {'lng': 113.220317, 'lat': 28.189312, 'full': '长沙黄花国际机场'},
        '张家界': {'lng': 110.479721, 'lat': 29.118721, 'full': '湖南省张家界市'},
        '天门山': {'lng': 110.602721, 'lat': 29.052721, 'full': '张家界市天门山'},
        '张家界站': {'lng': 110.472721, 'lat': 29.122721, 'full': '张家界站'},
        '张家界荷花机场': {'lng': 110.442317, 'lat': 29.103312, 'full': '张家界荷花国际机场'},
        '岳阳': {'lng': 113.128721, 'lat': 29.372721, 'full': '湖南省岳阳市'},
        '岳阳楼': {'lng': 113.122721, 'lat': 29.362721, 'full': '岳阳市岳阳楼'},
        '岳阳站': {'lng': 113.132721, 'lat': 29.412721, 'full': '岳阳站'},
        '衡阳': {'lng': 112.572721, 'lat': 26.902721, 'full': '湖南省衡阳市'},
        '衡阳站': {'lng': 112.612721, 'lat': 26.882721, 'full': '衡阳站'},
        '株洲': {'lng': 113.142721, 'lat': 27.842721, 'full': '湖南省株洲市'},
        '株洲站': {'lng': 113.152721, 'lat': 27.822721, 'full': '株洲站'},
        '湘潭': {'lng': 112.942721, 'lat': 27.852721, 'full': '湖南省湘潭市'},
        '郴州': {'lng': 113.022721, 'lat': 25.802721, 'full': '湖南省郴州市'},
        '常德': {'lng': 111.692721, 'lat': 29.042721, 'full': '湖南省常德市'},
        '益阳': {'lng': 112.352721, 'lat': 28.602721, 'full': '湖南省益阳市'},
        '娄底': {'lng': 111.992721, 'lat': 27.702721, 'full': '湖南省娄底市'},
        '邵阳': {'lng': 111.472721, 'lat': 27.252721, 'full': '湖南省邵阳市'},
        '怀化': {'lng': 110.002721, 'lat': 27.552721, 'full': '湖南省怀化市'},
        '永州': {'lng': 111.622721, 'lat': 26.422721, 'full': '湖南省永州市'},
        '湘西': {'lng': 109.742721, 'lat': 28.312721, 'full': '湖南省湘西土家族苗族自治州'},
        '凤凰古城': {'lng': 109.602721, 'lat': 27.952721, 'full': '湘西凤凰古城'},
        '郑州': {'lng': 113.650823, 'lat': 34.756610, 'full': '河南省郑州市'},
        '二七塔': {'lng': 113.652721, 'lat': 34.752721, 'full': '郑州市二七塔'},
        '郑州站': {'lng': 113.652721, 'lat': 34.752721, 'full': '郑州站'},
        '郑州东站': {'lng': 113.752721, 'lat': 34.762721, 'full': '郑州东站'},
        '新郑机场': {'lng': 113.848317, 'lat': 34.529312, 'full': '郑州新郑国际机场'},
        '洛阳': {'lng': 112.454721, 'lat': 34.620721, 'full': '河南省洛阳市'},
        '龙门石窟': {'lng': 112.572721, 'lat': 34.652721, 'full': '洛阳市龙门石窟'},
        '洛阳站': {'lng': 112.442721, 'lat': 34.667721, 'full': '洛阳站'},
        '开封': {'lng': 114.348721, 'lat': 34.797721, 'full': '河南省开封市'},
        '清明上河园': {'lng': 114.352721, 'lat': 34.787721, 'full': '开封市清明上河园'},
        '开封站': {'lng': 114.302721, 'lat': 34.802721, 'full': '开封站'},
        '南阳': {'lng': 112.522721, 'lat': 33.002721, 'full': '河南省南阳市'},
        '南阳站': {'lng': 112.542721, 'lat': 33.022721, 'full': '南阳站'},
        '安阳': {'lng': 114.392721, 'lat': 36.102721, 'full': '河南省安阳市'},
        '殷墟': {'lng': 114.352721, 'lat': 36.132721, 'full': '安阳市殷墟'},
        '安阳站': {'lng': 114.402721, 'lat': 36.062721, 'full': '安阳站'},
        '新乡': {'lng': 113.852721, 'lat': 35.302721, 'full': '河南省新乡市'},
        '焦作': {'lng': 113.242721, 'lat': 35.222721, 'full': '河南省焦作市'},
        '云台山': {'lng': 113.522721, 'lat': 35.252721, 'full': '焦作市云台山'},
        '许昌': {'lng': 113.852721, 'lat': 34.032721, 'full': '河南省许昌市'},
        '平顶山': {'lng': 113.302721, 'lat': 33.772721, 'full': '河南省平顶山市'},
        '驻马店': {'lng': 114.022721, 'lat': 33.012721, 'full': '河南省驻马店市'},
        '商丘': {'lng': 115.652721, 'lat': 34.422721, 'full': '河南省商丘市'},
        '信阳': {'lng': 114.092721, 'lat': 32.122721, 'full': '河南省信阳市'},
        '周口': {'lng': 114.702721, 'lat': 33.622721, 'full': '河南省周口市'},
        '漯河': {'lng': 114.022721, 'lat': 33.582721, 'full': '河南省漯河市'},
        '濮阳': {'lng': 115.032721, 'lat': 35.762721, 'full': '河南省濮阳市'},
        '鹤壁': {'lng': 114.302721, 'lat': 35.752721, 'full': '河南省鹤壁市'},
        '三门峡': {'lng': 111.202721, 'lat': 34.772721, 'full': '河南省三门峡市'},
        '济源': {'lng': 112.602721, 'lat': 35.072721, 'full': '河南省济源市'},
        
        # 华北地区
        '石家庄': {'lng': 114.521127, 'lat': 38.048826, 'full': '河北省石家庄市'},
        '石家庄站': {'lng': 114.522721, 'lat': 38.048721, 'full': '石家庄站'},
        '石家庄北站': {'lng': 114.482721, 'lat': 38.087721, 'full': '石家庄北站'},
        '正定': {'lng': 114.572721, 'lat': 38.142721, 'full': '石家庄市正定县'},
        '保定': {'lng': 115.464721, 'lat': 38.874721, 'full': '河北省保定市'},
        '白洋淀': {'lng': 115.922721, 'lat': 38.842721, 'full': '保定市白洋淀'},
        '保定站': {'lng': 115.472721, 'lat': 38.852721, 'full': '保定站'},
        '唐山': {'lng': 118.194721, 'lat': 39.634721, 'full': '河北省唐山市'},
        '唐山站': {'lng': 118.152721, 'lat': 39.722721, 'full': '唐山站'},
        '秦皇岛': {'lng': 119.597721, 'lat': 39.937721, 'full': '河北省秦皇岛市'},
        '山海关': {'lng': 119.752721, 'lat': 40.002721, 'full': '秦皇岛市山海关'},
        '北戴河': {'lng': 119.522721, 'lat': 39.842721, 'full': '秦皇岛市北戴河'},
        '秦皇岛站': {'lng': 119.602721, 'lat': 39.972721, 'full': '秦皇岛站'},
        '廊坊': {'lng': 116.683721, 'lat': 39.538721, 'full': '河北省廊坊市'},
        '廊坊站': {'lng': 116.702721, 'lat': 39.522721, 'full': '廊坊站'},
        '沧州': {'lng': 116.852721, 'lat': 38.302721, 'full': '河北省沧州市'},
        '沧州站': {'lng': 116.872721, 'lat': 38.282721, 'full': '沧州站'},
        '邯郸': {'lng': 114.542721, 'lat': 36.622721, 'full': '河北省邯郸市'},
        '邯郸站': {'lng': 114.502721, 'lat': 36.602721, 'full': '邯郸站'},
        '邢台': {'lng': 114.502721, 'lat': 37.072721, 'full': '河北省邢台市'},
        '张家口': {'lng': 114.882721, 'lat': 40.772721, 'full': '河北省张家口市'},
        '张家口站': {'lng': 114.902721, 'lat': 40.792721, 'full': '张家口站'},
        '承德': {'lng': 117.972721, 'lat': 40.952721, 'full': '河北省承德市'},
        '避暑山庄': {'lng': 117.942721, 'lat': 40.972721, 'full': '承德市避暑山庄'},
        '承德站': {'lng': 117.952721, 'lat': 40.982721, 'full': '承德站'},
        '衡水': {'lng': 115.672721, 'lat': 37.742721, 'full': '河北省衡水市'},
        '雄安新区': {'lng': 115.972721, 'lat': 38.972721, 'full': '河北省雄安新区'},
        '太原': {'lng': 112.549040, 'lat': 37.857014, 'full': '山西省太原市'},
        '晋祠': {'lng': 112.432721, 'lat': 37.422721, 'full': '太原市晋祠'},
        '太原站': {'lng': 112.552721, 'lat': 37.878721, 'full': '太原站'},
        '太原南站': {'lng': 112.542721, 'lat': 37.752721, 'full': '太原南站'},
        '太原武宿机场': {'lng': 112.642317, 'lat': 37.753312, 'full': '太原武宿国际机场'},
        '大同': {'lng': 113.295721, 'lat': 40.094721, 'full': '山西省大同市'},
        '云冈石窟': {'lng': 113.122721, 'lat': 40.112721, 'full': '大同市云冈石窟'},
        '大同站': {'lng': 113.292721, 'lat': 40.092721, 'full': '大同站'},
        '平遥': {'lng': 112.142721, 'lat': 37.202721, 'full': '晋中市平遥县'},
        '平遥古城': {'lng': 112.142721, 'lat': 37.202721, 'full': '平遥古城'},
        '运城': {'lng': 111.002721, 'lat': 35.022721, 'full': '山西省运城市'},
        '运城站': {'lng': 110.982721, 'lat': 35.012721, 'full': '运城站'},
        '临汾': {'lng': 111.522721, 'lat': 36.082721, 'full': '山西省临汾市'},
        '临汾站': {'lng': 111.502721, 'lat': 36.062721, 'full': '临汾站'},
        '长治': {'lng': 113.122721, 'lat': 36.202721, 'full': '山西省长治市'},
        '长治站': {'lng': 113.112721, 'lat': 36.192721, 'full': '长治站'},
        '晋城': {'lng': 112.852721, 'lat': 35.522721, 'full': '山西省晋城市'},
        '晋中': {'lng': 112.752721, 'lat': 37.702721, 'full': '山西省晋中市'},
        '朔州': {'lng': 112.432721, 'lat': 39.352721, 'full': '山西省朔州市'},
        '忻州': {'lng': 112.732721, 'lat': 38.422721, 'full': '山西省忻州市'},
        '五台山': {'lng': 113.582721, 'lat': 38.752721, 'full': '忻州市五台山'},
        '吕梁': {'lng': 111.142721, 'lat': 37.522721, 'full': '山西省吕梁市'},
        '阳泉': {'lng': 113.572721, 'lat': 37.872721, 'full': '山西省阳泉市'},
        
        # 东北地区
        '沈阳': {'lng': 123.464813, 'lat': 41.677283, 'full': '辽宁省沈阳市'},
        '沈阳站': {'lng': 123.432721, 'lat': 41.808721, 'full': '沈阳站'},
        '沈阳北站': {'lng': 123.472721, 'lat': 41.897721, 'full': '沈阳北站'},
        '沈阳故宫': {'lng': 123.442721, 'lat': 41.802721, 'full': '沈阳市故宫'},
        '张氏帅府': {'lng': 123.452721, 'lat': 41.792721, 'full': '沈阳市张氏帅府'},
        '沈阳桃仙机场': {'lng': 123.502317, 'lat': 41.643312, 'full': '沈阳桃仙国际机场'},
        '大连': {'lng': 121.614696, 'lat': 38.914003, 'full': '辽宁省大连市'},
        '星海广场': {'lng': 121.592721, 'lat': 38.882721, 'full': '大连市星海广场'},
        '老虎滩': {'lng': 121.672721, 'lat': 38.862721, 'full': '大连市老虎滩海洋公园'},
        '金石滩': {'lng': 121.972721, 'lat': 39.072721, 'full': '大连市金石滩'},
        '大连站': {'lng': 121.632721, 'lat': 38.948721, 'full': '大连站'},
        '大连北站': {'lng': 121.562721, 'lat': 39.012721, 'full': '大连北站'},
        '大连周水子机场': {'lng': 121.642317, 'lat': 38.973312, 'full': '大连周水子国际机场'},
        '鞍山': {'lng': 122.992721, 'lat': 41.102721, 'full': '辽宁省鞍山市'},
        '千山': {'lng': 122.952721, 'lat': 41.012721, 'full': '鞍山市千山'},
        '鞍山站': {'lng': 122.972721, 'lat': 41.122721, 'full': '鞍山站'},
        '抚顺': {'lng': 123.952721, 'lat': 41.882721, 'full': '辽宁省抚顺市'},
        '本溪': {'lng': 123.762721, 'lat': 41.302721, 'full': '辽宁省本溪市'},
        '水洞': {'lng': 124.122721, 'lat': 41.292721, 'full': '本溪市本溪水洞'},
        '丹东': {'lng': 124.392721, 'lat': 40.002721, 'full': '辽宁省丹东市'},
        '鸭绿江': {'lng': 124.352721, 'lat': 40.012721, 'full': '丹东市鸭绿江'},
        '丹东站': {'lng': 124.372721, 'lat': 40.092721, 'full': '丹东站'},
        '锦州': {'lng': 121.152721, 'lat': 41.102721, 'full': '辽宁省锦州市'},
        '笔架山': {'lng': 121.052721, 'lat': 41.052721, 'full': '锦州市笔架山'},
        '锦州站': {'lng': 121.122721, 'lat': 41.112721, 'full': '锦州站'},
        '营口': {'lng': 122.252721, 'lat': 40.672721, 'full': '辽宁省营口市'},
        '鲅鱼圈': {'lng': 122.122721, 'lat': 40.272721, 'full': '营口市鲅鱼圈'},
        '辽阳': {'lng': 123.172721, 'lat': 41.272721, 'full': '辽宁省辽阳市'},
        '盘锦': {'lng': 122.072721, 'lat': 41.022721, 'full': '辽宁省盘锦市'},
        '红海滩': {'lng': 122.122721, 'lat': 40.852721, 'full': '盘锦市红海滩'},
        '铁岭': {'lng': 123.842721, 'lat': 42.292721, 'full': '辽宁省铁岭市'},
        '朝阳': {'lng': 120.452721, 'lat': 41.572721, 'full': '辽宁省朝阳市'},
        '葫芦岛': {'lng': 120.852721, 'lat': 40.702721, 'full': '辽宁省葫芦岛市'},
        '兴城': {'lng': 120.752721, 'lat': 40.572721, 'full': '葫芦岛市兴城市'},
        '长春': {'lng': 125.326223, 'lat': 43.896536, 'full': '吉林省长春市'},
        '伪满皇宫': {'lng': 125.322721, 'lat': 43.902721, 'full': '长春市伪满皇宫'},
        '长影世纪城': {'lng': 125.422721, 'lat': 43.832721, 'full': '长春市长影世纪城'},
        '长春站': {'lng': 125.322721, 'lat': 43.892721, 'full': '长春站'},
        '长春西站': {'lng': 125.152721, 'lat': 43.882721, 'full': '长春西站'},
        '龙嘉机场': {'lng': 125.682317, 'lat': 43.993312, 'full': '长春龙嘉国际机场'},
        '吉林': {'lng': 126.549443, 'lat': 43.837838, 'full': '吉林省吉林市'},
        '雾凇': {'lng': 126.552721, 'lat': 43.812721, 'full': '吉林市雾凇'},
        '吉林站': {'lng': 126.562721, 'lat': 43.902721, 'full': '吉林站'},
        '松花湖': {'lng': 126.532721, 'lat': 43.752721, 'full': '吉林市松花湖'},
        '延吉': {'lng': 129.482721, 'lat': 42.902721, 'full': '吉林省延边朝鲜族自治州延吉市'},
        '延吉站': {'lng': 129.502721, 'lat': 42.872721, 'full': '延吉站'},
        '延吉朝阳川机场': {'lng': 129.452317, 'lat': 42.883312, 'full': '延吉朝阳川国际机场'},
        '四平': {'lng': 124.352721, 'lat': 43.172721, 'full': '吉林省四平市'},
        '辽源': {'lng': 125.152721, 'lat': 42.902721, 'full': '吉林省辽源市'},
        '通化': {'lng': 125.932721, 'lat': 41.722721, 'full': '吉林省通化市'},
        '白山': {'lng': 126.422721, 'lat': 41.942721, 'full': '吉林省白山市'},
        '长白山': {'lng': 128.042721, 'lat': 42.022721, 'full': '吉林省长白山'},
        '白城': {'lng': 122.842721, 'lat': 45.622721, 'full': '吉林省白城市'},
        '松原': {'lng': 124.822721, 'lat': 45.142721, 'full': '吉林省松原市'},
        '哈尔滨': {'lng': 126.541116, 'lat': 45.803368, 'full': '黑龙江省哈尔滨市'},
        '中央大街': {'lng': 126.622721, 'lat': 45.802721, 'full': '哈尔滨市中央大街'},
        '索菲亚教堂': {'lng': 126.622721, 'lat': 45.782721, 'full': '哈尔滨市圣索菲亚教堂'},
        '冰雪大世界': {'lng': 126.522721, 'lat': 45.822721, 'full': '哈尔滨市冰雪大世界'},
        '哈尔滨站': {'lng': 126.632721, 'lat': 45.787721, 'full': '哈尔滨站'},
        '哈尔滨西站': {'lng': 126.592721, 'lat': 45.732721, 'full': '哈尔滨西站'},
        '哈尔滨太平机场': {'lng': 126.252317, 'lat': 45.633312, 'full': '哈尔滨太平国际机场'},
        '齐齐哈尔': {'lng': 123.918721, 'lat': 47.352721, 'full': '黑龙江省齐齐哈尔市'},
        '扎龙': {'lng': 124.022721, 'lat': 47.222721, 'full': '齐齐哈尔市扎龙湿地'},
        '齐齐哈尔站': {'lng': 123.972721, 'lat': 47.342721, 'full': '齐齐哈尔站'},
        '牡丹江': {'lng': 129.633721, 'lat': 44.552721, 'full': '黑龙江省牡丹江市'},
        '牡丹江站': {'lng': 129.582721, 'lat': 44.572721, 'full': '牡丹江站'},
        '镜泊湖': {'lng': 129.122721, 'lat': 43.952721, 'full': '牡丹江市镜泊湖'},
        '大庆': {'lng': 125.032721, 'lat': 46.582721, 'full': '黑龙江省大庆市'},
        '大庆站': {'lng': 125.022721, 'lat': 46.602721, 'full': '大庆站'},
        '佳木斯': {'lng': 130.322721, 'lat': 46.822721, 'full': '黑龙江省佳木斯市'},
        '佳木斯站': {'lng': 130.352721, 'lat': 46.802721, 'full': '佳木斯站'},
        '鹤岗': {'lng': 130.282721, 'lat': 47.352721, 'full': '黑龙江省鹤岗市'},
        '双鸭山': {'lng': 131.152721, 'lat': 46.652721, 'full': '黑龙江省双鸭山市'},
        '鸡西': {'lng': 130.972721, 'lat': 45.302721, 'full': '黑龙江省鸡西市'},
        '伊春': {'lng': 128.842721, 'lat': 47.732721, 'full': '黑龙江省伊春市'},
        '七台河': {'lng': 131.002721, 'lat': 45.772721, 'full': '黑龙江省七台河市'},
        '黑河': {'lng': 127.532721, 'lat': 50.252721, 'full': '黑龙江省黑河市'},
        '绥化': {'lng': 126.972721, 'lat': 46.652721, 'full': '黑龙江省绥化市'},
        '大兴安岭': {'lng': 124.122721, 'lat': 51.952721, 'full': '黑龙江省大兴安岭地区'},
        
        # 西南地区
        '成都': {'lng': 104.065735, 'lat': 30.659842, 'full': '四川省成都市'},
        '宽窄巷子': {'lng': 104.057258, 'lat': 30.671721, 'full': '成都市宽窄巷子'},
        '锦里': {'lng': 104.142721, 'lat': 30.672721, 'full': '成都市锦里古街'},
        '武侯祠': {'lng': 104.052721, 'lat': 30.652721, 'full': '成都市武侯祠'},
        '杜甫草堂': {'lng': 104.022721, 'lat': 30.682721, 'full': '成都市杜甫草堂'},
        '青城山': {'lng': 103.572721, 'lat': 30.892721, 'full': '成都市都江堰市青城山'},
        '都江堰': {'lng': 103.664721, 'lat': 30.992721, 'full': '成都市都江堰市'},
        '成都站': {'lng': 104.072721, 'lat': 30.698721, 'full': '成都站'},
        '成都东站': {'lng': 104.142721, 'lat': 30.630721, 'full': '成都东站'},
        '成都南站': {'lng': 104.052721, 'lat': 30.592721, 'full': '成都南站'},
        '成都西站': {'lng': 103.982721, 'lat': 30.672721, 'full': '成都西站'},
        '双流机场': {'lng': 103.947317, 'lat': 30.578312, 'full': '成都双流国际机场'},
        '天府机场': {'lng': 104.447317, 'lat': 30.288312, 'full': '成都天府国际机场'},
        '熊猫基地': {'lng': 104.152721, 'lat': 30.737721, 'full': '成都市熊猫基地'},
        '春熙路': {'lng': 104.091721, 'lat': 30.680721, 'full': '成都市春熙路'},
        '太古里': {'lng': 104.092721, 'lat': 30.662721, 'full': '成都市远洋太古里'},
        '重庆': {'lng': 106.551556, 'lat': 29.563010, 'full': '重庆市'},
        '解放碑': {'lng': 106.578258, 'lat': 29.559552, 'full': '重庆市解放碑'},
        '洪崖洞': {'lng': 106.582721, 'lat': 29.562721, 'full': '重庆市洪崖洞'},
        '磁器口': {'lng': 106.452721, 'lat': 29.582721, 'full': '重庆市磁器口'},
        '长江索道': {'lng': 106.522721, 'lat': 29.552721, 'full': '重庆市长江索道'},
        '武隆': {'lng': 107.802721, 'lat': 29.417721, 'full': '重庆市武隆区'},
        '仙女山': {'lng': 107.752721, 'lat': 29.592721, 'full': '武隆区仙女山'},
        '大足石刻': {'lng': 105.752721, 'lat': 29.422721, 'full': '重庆市大足区大足石刻'},
        '重庆站': {'lng': 106.521721, 'lat': 29.530721, 'full': '重庆站'},
        '重庆北站': {'lng': 106.532721, 'lat': 29.582721, 'full': '重庆北站'},
        '重庆西站': {'lng': 106.482721, 'lat': 29.492721, 'full': '重庆西站'},
        '重庆东站': {'lng': 106.622721, 'lat': 29.552721, 'full': '重庆东站'},
        '江北机场': {'lng': 106.652317, 'lat': 29.718312, 'full': '重庆江北国际机场'},
        '贵阳': {'lng': 106.630424, 'lat': 26.647764, 'full': '贵州省贵阳市'},
        '黔灵山': {'lng': 106.722721, 'lat': 26.622721, 'full': '贵阳市黔灵山'},
        '黄果树': {'lng': 105.662721, 'lat': 26.092721, 'full': '安顺市黄果树瀑布'},
        '西江千户苗寨': {'lng': 108.192721, 'lat': 26.502721, 'full': '黔东南苗族侗族自治州西江千户苗寨'},
        '镇远': {'lng': 108.442721, 'lat': 27.052721, 'full': '黔东南镇远古镇'},
        '贵阳站': {'lng': 106.722721, 'lat': 26.649721, 'full': '贵阳站'},
        '贵阳北站': {'lng': 106.632721, 'lat': 26.632721, 'full': '贵阳北站'},
        '贵阳龙洞堡机场': {'lng': 106.802317, 'lat': 26.533312, 'full': '贵阳龙洞堡国际机场'},
        '遵义': {'lng': 106.928721, 'lat': 27.730721, 'full': '贵州省遵义市'},
        '遵义会议': {'lng': 106.912721, 'lat': 27.742721, 'full': '遵义市遵义会议会址'},
        '遵义站': {'lng': 106.862721, 'lat': 27.672721, 'full': '遵义站'},
        '安顺': {'lng': 105.932721, 'lat': 26.245721, 'full': '贵州省安顺市'},
        '黄果树瀑布': {'lng': 105.662721, 'lat': 26.092721, 'full': '安顺市黄果树瀑布'},
        '安顺站': {'lng': 105.882721, 'lat': 26.252721, 'full': '安顺站'},
        '六盘水': {'lng': 104.832721, 'lat': 26.602721, 'full': '贵州省六盘水市'},
        '六盘水站': {'lng': 104.842721, 'lat': 26.592721, 'full': '六盘水站'},
        '毕节': {'lng': 105.282721, 'lat': 27.302721, 'full': '贵州省毕节市'},
        '铜仁': {'lng': 109.182721, 'lat': 27.752721, 'full': '贵州省铜仁市'},
        '梵净山': {'lng': 108.722721, 'lat': 27.722721, 'full': '铜仁市梵净山'},
        '黔南': {'lng': 107.522721, 'lat': 26.272721, 'full': '贵州省黔南布依族苗族自治州'},
        '黔西南': {'lng': 104.902721, 'lat': 25.102721, 'full': '贵州省黔西南布依族苗族自治州'},
        '黔东南': {'lng': 107.982721, 'lat': 26.582721, 'full': '贵州省黔东南苗族侗族自治州'},
        '昆明': {'lng': 102.833817, 'lat': 24.882605, 'full': '云南省昆明市'},
        '石林': {'lng': 103.322721, 'lat': 24.812721, 'full': '昆明市石林彝族自治县'},
        '滇池': {'lng': 102.752721, 'lat': 24.852721, 'full': '昆明市滇池'},
        '翠湖': {'lng': 102.722721, 'lat': 25.052721, 'full': '昆明市翠湖'},
        '昆明站': {'lng': 102.722721, 'lat': 25.017721, 'full': '昆明站'},
        '昆明南站': {'lng': 102.862721, 'lat': 24.907721, 'full': '昆明南站'},
        '昆明长水机场': {'lng': 102.936317, 'lat': 25.101312, 'full': '昆明长水国际机场'},
        '大理': {'lng': 100.268721, 'lat': 25.606721, 'full': '云南省大理白族自治州'},
        '洱海': {'lng': 100.252721, 'lat': 25.602721, 'full': '大理市洱海'},
        '大理古城': {'lng': 100.242721, 'lat': 25.592721, 'full': '大理市古城'},
        '大理站': {'lng': 100.272721, 'lat': 25.672721, 'full': '大理站'},
        '丽江': {'lng': 100.233721, 'lat': 26.875721, 'full': '云南省丽江市'},
        '丽江古城': {'lng': 100.232721, 'lat': 26.872721, 'full': '丽江市古城'},
        '玉龙雪山': {'lng': 100.232721, 'lat': 27.022721, 'full': '丽江市玉龙雪山'},
        '丽江站': {'lng': 100.252721, 'lat': 26.872721, 'full': '丽江站'},
        '香格里拉': {'lng': 99.702721, 'lat': 27.852721, 'full': '云南省迪庆藏族自治州香格里拉市'},
        '普达措': {'lng': 99.952721, 'lat': 27.722721, 'full': '香格里拉市普达措国家公园'},
        '西双版纳': {'lng': 100.797721, 'lat': 22.009721, 'full': '云南省西双版纳傣族自治州'},
        '傣族园': {'lng': 100.952721, 'lat': 21.952721, 'full': '西双版纳傣族园'},
        '西双版纳站': {'lng': 100.782721, 'lat': 22.012721, 'full': '西双版纳站'},
        '景洪': {'lng': 100.802721, 'lat': 22.002721, 'full': '西双版纳景洪市'},
        '腾冲': {'lng': 98.492721, 'lat': 25.022721, 'full': '保山市腾冲市'},
        '热海': {'lng': 98.502721, 'lat': 24.952721, 'full': '腾冲市热海'},
        '瑞丽': {'lng': 97.852721, 'lat': 24.022721, 'full': '德宏傣族景颇族自治州瑞丽市'},
        '泸沽湖': {'lng': 100.772721, 'lat': 27.702721, 'full': '丽江市泸沽湖'},
        '楚雄': {'lng': 101.522721, 'lat': 25.052721, 'full': '云南省楚雄彝族自治州'},
        '红河': {'lng': 103.372721, 'lat': 23.352721, 'full': '云南省红河哈尼族彝族自治州'},
        '昭通': {'lng': 103.722721, 'lat': 27.342721, 'full': '云南省昭通市'},
        '曲靖': {'lng': 103.792721, 'lat': 25.502721, 'full': '云南省曲靖市'},
        '玉溪': {'lng': 102.522721, 'lat': 24.352721, 'full': '云南省玉溪市'},
        '文山': {'lng': 104.252721, 'lat': 23.372721, 'full': '云南省文山壮族苗族自治州'},
        '普洱': {'lng': 100.972721, 'lat': 22.822721, 'full': '云南省普洱市'},
        '临沧': {'lng': 100.082721, 'lat': 23.902721, 'full': '云南省临沧市'},
        '保山': {'lng': 99.172721, 'lat': 25.122721, 'full': '云南省保山市'},
        '德宏': {'lng': 98.582721, 'lat': 24.452721, 'full': '云南省德宏傣族景颇族自治州'},
        '怒江': {'lng': 98.852721, 'lat': 25.852721, 'full': '云南省怒江傈僳族自治州'},
        '迪庆': {'lng': 99.702721, 'lat': 27.852721, 'full': '云南省迪庆藏族自治州'},
        '拉萨': {'lng': 91.117212, 'lat': 29.647601, 'full': '西藏拉萨市'},
        '布达拉宫': {'lng': 91.117212, 'lat': 29.657601, 'full': '拉萨市布达拉宫'},
        '大昭寺': {'lng': 91.132721, 'lat': 29.652721, 'full': '拉萨市大昭寺'},
        '纳木错': {'lng': 90.992721, 'lat': 30.402721, 'full': '拉萨市纳木错'},
        '羊卓雍错': {'lng': 90.652721, 'lat': 28.952721, 'full': '山南市羊卓雍错'},
        '拉萨站': {'lng': 91.132721, 'lat': 29.652721, 'full': '拉萨站'},
        '拉萨贡嘎机场': {'lng': 90.952317, 'lat': 29.303312, 'full': '拉萨贡嘎国际机场'},
        '日喀则': {'lng': 88.882721, 'lat': 29.272721, 'full': '西藏日喀则市'},
        '扎什伦布寺': {'lng': 88.872721, 'lat': 29.262721, 'full': '日喀则市扎什伦布寺'},
        '珠峰': {'lng': 86.952721, 'lat': 28.002721, 'full': '日喀则市珠穆朗玛峰'},
        '日喀则站': {'lng': 88.902721, 'lat': 29.242721, 'full': '日喀则站'},
        '林芝': {'lng': 94.362721, 'lat': 29.652721, 'full': '西藏林芝市'},
        '巴松措': {'lng': 93.952721, 'lat': 29.852721, 'full': '林芝市巴松措'},
        '林芝站': {'lng': 94.342721, 'lat': 29.312721, 'full': '林芝站'},
        '林芝米林机场': {'lng': 94.342317, 'lat': 29.303312, 'full': '林芝米林国际机场'},
        '山南': {'lng': 91.772721, 'lat': 29.252721, 'full': '西藏山南市'},
        '昌都': {'lng': 97.182721, 'lat': 31.152721, 'full': '西藏昌都市'},
        '昌都站': {'lng': 97.172721, 'lat': 31.142721, 'full': '昌都站'},
        '那曲': {'lng': 92.052721, 'lat': 31.472721, 'full': '西藏那曲市'},
        '阿里': {'lng': 80.102721, 'lat': 32.502721, 'full': '西藏阿里地区'},
        
        # 西北地区
        '西安': {'lng': 108.940175, 'lat': 34.341568, 'full': '陕西省西安市'},
        '兵马俑': {'lng': 109.278721, 'lat': 34.385721, 'full': '西安市秦始皇兵马俑'},
        '华清池': {'lng': 109.282721, 'lat': 34.372721, 'full': '西安市华清池'},
        '大雁塔': {'lng': 108.960721, 'lat': 34.219721, 'full': '西安市大雁塔'},
        '小雁塔': {'lng': 108.942721, 'lat': 34.232721, 'full': '西安市小雁塔'},
        '钟楼': {'lng': 108.940721, 'lat': 34.266721, 'full': '西安市钟楼'},
        '鼓楼': {'lng': 108.943721, 'lat': 34.263721, 'full': '西安市鼓楼'},
        '回民街': {'lng': 108.952721, 'lat': 34.262721, 'full': '西安市回民街'},
        '城墙': {'lng': 108.942721, 'lat': 34.282721, 'full': '西安城墙'},
        '大唐不夜城': {'lng': 108.962721, 'lat': 34.232721, 'full': '西安市大唐不夜城'},
        '西安站': {'lng': 108.952721, 'lat': 34.277721, 'full': '西安站'},
        '西安北站': {'lng': 108.932721, 'lat': 34.384721, 'full': '西安北站'},
        '西安咸阳机场': {'lng': 108.752317, 'lat': 34.440312, 'full': '西安咸阳国际机场'},
        '华山': {'lng': 110.092721, 'lat': 34.592721, 'full': '渭南市华阴市华山'},
        '华山站': {'lng': 110.072721, 'lat': 34.542721, 'full': '华山站'},
        '延安': {'lng': 109.482721, 'lat': 36.602721, 'full': '陕西省延安市'},
        '延安革命纪念馆': {'lng': 109.462721, 'lat': 36.592721, 'full': '延安市革命纪念馆'},
        '延安站': {'lng': 109.502721, 'lat': 36.582721, 'full': '延安站'},
        '宝鸡': {'lng': 107.242721, 'lat': 34.362721, 'full': '陕西省宝鸡市'},
        '法门寺': {'lng': 107.622721, 'lat': 34.452721, 'full': '宝鸡市扶风县法门寺'},
        '太白山': {'lng': 107.722721, 'lat': 34.052721, 'full': '宝鸡市太白山'},
        '宝鸡站': {'lng': 107.222721, 'lat': 34.352721, 'full': '宝鸡站'},
        '渭南': {'lng': 109.502721, 'lat': 34.502721, 'full': '陕西省渭南市'},
        '渭南站': {'lng': 109.522721, 'lat': 34.522721, 'full': '渭南站'},
        '咸阳': {'lng': 108.722721, 'lat': 34.342721, 'full': '陕西省咸阳市'},
        '咸阳站': {'lng': 108.712721, 'lat': 34.332721, 'full': '咸阳站'},
        '汉中': {'lng': 107.022721, 'lat': 33.072721, 'full': '陕西省汉中市'},
        '汉中站': {'lng': 107.012721, 'lat': 33.052721, 'full': '汉中站'},
        '安康': {'lng': 109.022721, 'lat': 32.702721, 'full': '陕西省安康市'},
        '安康站': {'lng': 109.002721, 'lat': 32.692721, 'full': '安康站'},
        '商洛': {'lng': 109.942721, 'lat': 33.872721, 'full': '陕西省商洛市'},
        '榆林': {'lng': 109.742721, 'lat': 38.302721, 'full': '陕西省榆林市'},
        '榆林站': {'lng': 109.722721, 'lat': 38.282721, 'full': '榆林站'},
        '铜川': {'lng': 108.942721, 'lat': 35.082721, 'full': '陕西省铜川市'},
        '兰州': {'lng': 103.834176, 'lat': 36.061195, 'full': '甘肃省兰州市'},
        '中山桥': {'lng': 103.822721, 'lat': 36.062721, 'full': '兰州市中山桥'},
        '白塔山': {'lng': 103.832721, 'lat': 36.072721, 'full': '兰州市白塔山'},
        '兰州站': {'lng': 103.842721, 'lat': 36.067721, 'full': '兰州站'},
        '兰州西站': {'lng': 103.762721, 'lat': 36.067721, 'full': '兰州西站'},
        '兰州中川机场': {'lng': 103.602317, 'lat': 36.513312, 'full': '兰州中川国际机场'},
        '敦煌': {'lng': 94.662721, 'lat': 40.142721, 'full': '甘肃省敦煌市'},
        '莫高窟': {'lng': 94.822721, 'lat': 40.142721, 'full': '敦煌市莫高窟'},
        '鸣沙山': {'lng': 94.702721, 'lat': 40.152721, 'full': '敦煌市鸣沙山'},
        '月牙泉': {'lng': 94.742721, 'lat': 40.142721, 'full': '敦煌市月牙泉'},
        '敦煌站': {'lng': 94.672721, 'lat': 40.152721, 'full': '敦煌站'},
        '嘉峪关': {'lng': 98.277721, 'lat': 39.803721, 'full': '甘肃省嘉峪关市'},
        '嘉峪关关城': {'lng': 98.272721, 'lat': 39.802721, 'full': '嘉峪关市关城'},
        '嘉峪关站': {'lng': 98.302721, 'lat': 39.772721, 'full': '嘉峪关站'},
        '张掖': {'lng': 100.452721, 'lat': 38.937721, 'full': '甘肃省张掖市'},
        '丹霞': {'lng': 100.052721, 'lat': 38.952721, 'full': '张掖市七彩丹霞'},
        '张掖站': {'lng': 100.442721, 'lat': 38.932721, 'full': '张掖站'},
        '张掖甘州机场': {'lng': 100.622317, 'lat': 38.933312, 'full': '张掖甘州机场'},
        '天水': {'lng': 105.722721, 'lat': 34.582721, 'full': '甘肃省天水市'},
        '麦积山': {'lng': 106.022721, 'lat': 34.752721, 'full': '天水市麦积山石窟'},
        '天水站': {'lng': 105.752721, 'lat': 34.602721, 'full': '天水站'},
        '天水麦积山机场': {'lng': 105.862317, 'lat': 34.573312, 'full': '天水麦积山机场'},
        '武威': {'lng': 102.642721, 'lat': 37.952721, 'full': '甘肃省武威市'},
        '雷台汉墓': {'lng': 102.652721, 'lat': 37.942721, 'full': '武威市雷台汉墓'},
        '武威站': {'lng': 102.632721, 'lat': 37.922721, 'full': '武威站'},
        '金昌': {'lng': 102.182721, 'lat': 38.522721, 'full': '甘肃省金昌市'},
        '白银': {'lng': 104.182721, 'lat': 36.552721, 'full': '甘肃省白银市'},
        '定西': {'lng': 104.622721, 'lat': 35.602721, 'full': '甘肃省定西市'},
        '陇南': {'lng': 104.922721, 'lat': 33.402721, 'full': '甘肃省陇南市'},
        '临夏': {'lng': 103.212721, 'lat': 35.602721, 'full': '甘肃省临夏回族自治州'},
        '甘南': {'lng': 102.912721, 'lat': 34.982721, 'full': '甘肃省甘南藏族自治州'},
        '郎木寺': {'lng': 102.642721, 'lat': 34.752721, 'full': '甘南州郎木寺'},
        '酒泉': {'lng': 98.502721, 'lat': 39.752721, 'full': '甘肃省酒泉市'},
        '卫星发射中心': {'lng': 100.602721, 'lat': 40.952721, 'full': '酒泉市卫星发射中心'},
        '酒泉站': {'lng': 98.522721, 'lat': 39.772721, 'full': '酒泉站'},
        '西宁': {'lng': 101.778323, 'lat': 36.617216, 'full': '青海省西宁市'},
        '青海湖': {'lng': 99.952721, 'lat': 36.952721, 'full': '青海省青海湖'},
        '塔尔寺': {'lng': 101.522721, 'lat': 36.552721, 'full': '西宁市塔尔寺'},
        '西宁站': {'lng': 101.782721, 'lat': 36.627721, 'full': '西宁站'},
        '西宁曹家堡机场': {'lng': 101.742317, 'lat': 36.533312, 'full': '西宁曹家堡国际机场'},
        '格尔木': {'lng': 94.902721, 'lat': 36.402721, 'full': '青海省格尔木市'},
        '昆仑山口': {'lng': 94.702721, 'lat': 35.702721, 'full': '格尔木市昆仑山口'},
        '格尔木站': {'lng': 94.902721, 'lat': 36.372721, 'full': '格尔木站'},
        '德令哈': {'lng': 97.372721, 'lat': 37.372721, 'full': '青海省德令哈市'},
        '玉树': {'lng': 97.002721, 'lat': 33.002721, 'full': '青海省玉树市'},
        '果洛': {'lng': 100.252721, 'lat': 34.472721, 'full': '青海省果洛藏族自治州'},
        '海北': {'lng': 100.902721, 'lat': 36.952721, 'full': '青海省海北藏族自治州'},
        '金银滩': {'lng': 100.952721, 'lat': 36.972721, 'full': '海北州金银滩'},
        '海南州': {'lng': 100.602721, 'lat': 36.302721, 'full': '青海省海南藏族自治州'},
        '黄南': {'lng': 102.022721, 'lat': 35.522721, 'full': '青海省黄南藏族自治州'},
        '银川': {'lng': 106.259126, 'lat': 38.468156, 'full': '宁夏银川市'},
        '沙湖': {'lng': 106.402721, 'lat': 38.802721, 'full': '银川市沙湖'},
        '西夏王陵': {'lng': 106.022721, 'lat': 38.322721, 'full': '银川市西夏王陵'},
        '镇北堡': {'lng': 105.822721, 'lat': 38.622721, 'full': '银川市镇北堡西部影城'},
        '银川站': {'lng': 106.292721, 'lat': 38.487721, 'full': '银川站'},
        '银川河东机场': {'lng': 106.392317, 'lat': 38.323312, 'full': '银川河东国际机场'},
        '石嘴山': {'lng': 106.383721, 'lat': 39.019721, 'full': '宁夏石嘴山市'},
        '石嘴山站': {'lng': 106.372721, 'lat': 39.012721, 'full': '石嘴山站'},
        '吴忠': {'lng': 106.202721, 'lat': 37.992721, 'full': '宁夏吴忠市'},
        '吴忠站': {'lng': 106.192721, 'lat': 37.982721, 'full': '吴忠站'},
        '中卫': {'lng': 105.202721, 'lat': 37.522721, 'full': '宁夏中卫市'},
        '沙坡头': {'lng': 105.022721, 'lat': 37.502721, 'full': '中卫市沙坡头'},
        '中卫站': {'lng': 105.182721, 'lat': 37.572721, 'full': '中卫站'},
        '固原': {'lng': 106.242721, 'lat': 36.022721, 'full': '宁夏固原市'},
        '须弥山': {'lng': 106.152721, 'lat': 36.052721, 'full': '固原市须弥山石窟'},
        '固原站': {'lng': 106.242721, 'lat': 36.002721, 'full': '固原站'},
        '乌鲁木齐': {'lng': 87.617733, 'lat': 43.826631, 'full': '新疆乌鲁木齐市'},
        '天山': {'lng': 87.252721, 'lat': 43.102721, 'full': '乌鲁木齐市天山'},
        '大巴扎': {'lng': 87.622721, 'lat': 43.822721, 'full': '乌鲁木齐市国际大巴扎'},
        '红山': {'lng': 87.602721, 'lat': 43.802721, 'full': '乌鲁木齐市红山'},
        '乌鲁木齐站': {'lng': 87.562721, 'lat': 43.832721, 'full': '乌鲁木齐站'},
        '乌鲁木齐南站': {'lng': 87.612721, 'lat': 43.807721, 'full': '乌鲁木齐南站'},
        '乌鲁木齐地窝堡机场': {'lng': 87.652317, 'lat': 43.953312, 'full': '乌鲁木齐地窝堡国际机场'},
        '喀什': {'lng': 75.992721, 'lat': 39.467721, 'full': '新疆喀什地区'},
        '喀什噶尔古城': {'lng': 75.982721, 'lat': 39.472721, 'full': '喀什市古城'},
        '艾提尕尔': {'lng': 75.992721, 'lat': 39.482721, 'full': '喀什市艾提尕尔清真寺'},
        '喀什站': {'lng': 75.962721, 'lat': 39.502721, 'full': '喀什站'},
        '喀什机场': {'lng': 75.952317, 'lat': 39.543312, 'full': '喀什机场'},
        '吐鲁番': {'lng': 89.192721, 'lat': 42.947721, 'full': '新疆吐鲁番市'},
        '火焰山': {'lng': 89.522721, 'lat': 42.952721, 'full': '吐鲁番市火焰山'},
        '葡萄沟': {'lng': 89.172721, 'lat': 42.922721, 'full': '吐鲁番市葡萄沟'},
        '坎儿井': {'lng': 89.172721, 'lat': 42.902721, 'full': '吐鲁番市坎儿井'},
        '吐鲁番站': {'lng': 89.172721, 'lat': 42.952721, 'full': '吐鲁番站'},
        '吐鲁番交河机场': {'lng': 89.172317, 'lat': 42.933312, 'full': '吐鲁番交河机场'},
        '哈密': {'lng': 93.522721, 'lat': 42.833721, 'full': '新疆哈密市'},
        '哈密站': {'lng': 93.512721, 'lat': 42.812721, 'full': '哈密站'},
        '哈密机场': {'lng': 93.662317, 'lat': 42.843312, 'full': '哈密机场'},
        '伊犁': {'lng': 81.322721, 'lat': 43.922721, 'full': '新疆伊犁哈萨克自治州'},
        '那拉提': {'lng': 83.722721, 'lat': 43.122721, 'full': '伊犁州那拉提草原'},
        '霍尔果斯': {'lng': 80.422721, 'lat': 44.202721, 'full': '伊犁州霍尔果斯市'},
        '伊宁': {'lng': 81.322721, 'lat': 43.922721, 'full': '伊犁州伊宁市'},
        '伊宁站': {'lng': 81.302721, 'lat': 43.952721, 'full': '伊宁站'},
        '伊宁机场': {'lng': 81.332317, 'lat': 43.953312, 'full': '伊宁机场'},
        '克拉玛依': {'lng': 84.872721, 'lat': 45.602721, 'full': '新疆克拉玛依市'},
        '克拉玛依站': {'lng': 84.852721, 'lat': 45.582721, 'full': '克拉玛依站'},
        '阿克苏': {'lng': 80.262721, 'lat': 41.172721, 'full': '新疆阿克苏地区'},
        '阿克苏站': {'lng': 80.282721, 'lat': 41.152721, 'full': '阿克苏站'},
        '阿克苏机场': {'lng': 80.302317, 'lat': 41.253312, 'full': '阿克苏机场'},
        '库尔勒': {'lng': 86.172721, 'lat': 41.752721, 'full': '新疆巴音郭楞蒙古自治州库尔勒市'},
        '库尔勒站': {'lng': 86.192721, 'lat': 41.772721, 'full': '库尔勒站'},
        '库尔勒机场': {'lng': 86.372317, 'lat': 41.603312, 'full': '库尔勒机场'},
        '和田': {'lng': 79.922721, 'lat': 37.122721, 'full': '新疆和田地区'},
        '和田站': {'lng': 79.912721, 'lat': 37.112721, 'full': '和田站'},
        '和田机场': {'lng': 79.872317, 'lat': 37.033312, 'full': '和田机场'},
        '阿勒泰': {'lng': 88.142721, 'lat': 47.862721, 'full': '新疆阿勒泰地区'},
        '喀纳斯': {'lng': 87.142721, 'lat': 48.822721, 'full': '阿勒泰地区喀纳斯湖'},
        '阿勒泰站': {'lng': 88.132721, 'lat': 47.852721, 'full': '阿勒泰站'},
        '阿勒泰机场': {'lng': 88.212317, 'lat': 47.753312, 'full': '阿勒泰机场'},
        '博尔塔拉': {'lng': 82.072721, 'lat': 44.902721, 'full': '新疆博尔塔拉蒙古自治州'},
        '赛里木湖': {'lng': 81.222721, 'lat': 44.502721, 'full': '博州赛里木湖'},
        '阿拉山口': {'lng': 82.572721, 'lat': 45.172721, 'full': '博州阿拉山口市'},
        '塔城': {'lng': 82.982721, 'lat': 46.752721, 'full': '新疆塔城地区'},
        '巴音郭楞': {'lng': 86.172721, 'lat': 41.752721, 'full': '新疆巴音郭楞蒙古自治州'},
        '博湖': {'lng': 86.672721, 'lat': 41.972721, 'full': '巴州博湖县'},
        '昌吉': {'lng': 87.302721, 'lat': 44.022721, 'full': '新疆昌吉回族自治州'},
        '克拉玛依': {'lng': 84.872721, 'lat': 45.602721, 'full': '新疆克拉玛依市'},
        '石河子': {'lng': 86.022721, 'lat': 44.312721, 'full': '新疆石河子市'},
        '阿拉尔': {'lng': 81.282721, 'lat': 40.552721, 'full': '新疆阿拉尔市'},
        '图木舒克': {'lng': 79.072721, 'lat': 39.852721, 'full': '新疆图木舒克市'},
        '五家渠': {'lng': 87.542721, 'lat': 44.172721, 'full': '新疆五家渠市'},
        '北屯': {'lng': 87.822721, 'lat': 47.372721, 'full': '新疆北屯市'},
        '铁门关': {'lng': 85.672721, 'lat': 41.822721, 'full': '新疆铁门关市'},
        '双河': {'lng': 82.352721, 'lat': 44.822721, 'full': '新疆双河市'},
        '可克达拉': {'lng': 80.972721, 'lat': 43.952721, 'full': '新疆可克达拉市'},
        '昆玉': {'lng': 79.272721, 'lat': 37.202721, 'full': '新疆昆玉市'},
        '胡杨河': {'lng': 84.822721, 'lat': 44.702721, 'full': '新疆胡杨河市'},
        '新星': {'lng': 93.522721, 'lat': 42.852721, 'full': '新疆新星市'},
        
        # 港澳台
        '香港': {'lng': 114.177013, 'lat': 22.303610, 'full': '香港特别行政区'},
        '维多利亚港': {'lng': 114.172721, 'lat': 22.292721, 'full': '香港维多利亚港'},
        '迪士尼': {'lng': 114.042721, 'lat': 22.322721, 'full': '香港迪士尼乐园'},
        '海洋公园': {'lng': 114.172721, 'lat': 22.242721, 'full': '香港海洋公园'},
        '太平山顶': {'lng': 114.142721, 'lat': 22.332721, 'full': '香港太平山顶'},
        '旺角': {'lng': 114.162721, 'lat': 22.322721, 'full': '香港旺角'},
        '尖沙咀': {'lng': 114.172721, 'lat': 22.302721, 'full': '香港尖沙咀'},
        '中环': {'lng': 114.162721, 'lat': 22.282721, 'full': '香港中环'},
        '铜锣湾': {'lng': 114.192721, 'lat': 22.282721, 'full': '香港铜锣湾'},
        '澳门': {'lng': 113.549130, 'lat': 22.192950, 'full': '澳门特别行政区'},
        '大三巴': {'lng': 113.552721, 'lat': 22.202721, 'full': '澳门大三巴'},
        '威尼斯人': {'lng': 113.572721, 'lat': 22.172721, 'full': '澳门威尼斯人'},
        '新葡京': {'lng': 113.542721, 'lat': 22.192721, 'full': '澳门新葡京'},
        '台北': {'lng': 121.565418, 'lat': 25.033969, 'full': '台湾省台北市'},
        '101大楼': {'lng': 121.562721, 'lat': 25.032721, 'full': '台北101大楼'},
        '故宫博物院': {'lng': 121.542721, 'lat': 25.102721, 'full': '台北故宫博物院'},
        '士林夜市': {'lng': 121.522721, 'lat': 25.082721, 'full': '台北士林夜市'},
        '西门町': {'lng': 121.502721, 'lat': 25.042721, 'full': '台北西门町'},
        '台北车站': {'lng': 121.517721, 'lat': 25.047721, 'full': '台北车站'},
        '桃园机场': {'lng': 121.232317, 'lat': 25.083312, 'full': '桃园国际机场'},
        '高雄': {'lng': 120.297721, 'lat': 22.628721, 'full': '台湾省高雄市'},
        '美丽岛': {'lng': 120.302721, 'lat': 22.632721, 'full': '高雄美丽岛捷运站'},
        '六合夜市': {'lng': 120.292721, 'lat': 22.632721, 'full': '高雄六合夜市'},
        '高雄车站': {'lng': 120.307721, 'lat': 22.642721, 'full': '高雄车站'},
        '高雄机场': {'lng': 120.352317, 'lat': 22.573312, 'full': '高雄国际机场'},
        '台中': {'lng': 120.672721, 'lat': 24.152721, 'full': '台湾省台中市'},
        '逢甲夜市': {'lng': 120.642721, 'lat': 24.182721, 'full': '台中逢甲夜市'},
        '台中车站': {'lng': 120.682721, 'lat': 24.142721, 'full': '台中车站'},
        '台中机场': {'lng': 120.622317, 'lat': 24.183312, 'full': '台中清泉岗机场'},
        '台南': {'lng': 120.202721, 'lat': 22.992721, 'full': '台湾省台南市'},
        '安平古镇': {'lng': 120.172721, 'lat': 22.992721, 'full': '台南安平古镇'},
        '台南车站': {'lng': 120.212721, 'lat': 23.002721, 'full': '台南车站'},
        '花莲': {'lng': 121.612721, 'lat': 23.982721, 'full': '台湾省花莲县'},
        '太鲁阁': {'lng': 121.602721, 'lat': 24.182721, 'full': '花莲太鲁阁'},
        '花莲站': {'lng': 121.602721, 'lat': 23.992721, 'full': '花莲站'},
        '花莲机场': {'lng': 121.612317, 'lat': 23.973312, 'full': '花莲机场'},
        '垦丁': {'lng': 120.752721, 'lat': 22.002721, 'full': '台湾省屏东县垦丁'},
        '鹅銮鼻': {'lng': 120.852721, 'lat': 21.902721, 'full': '垦丁鹅銮鼻'},
        '日月潭': {'lng': 120.922721, 'lat': 23.872721, 'full': '南投县日月潭'},
        '阿里山': {'lng': 120.802721, 'lat': 23.512721, 'full': '嘉义县阿里山'},
        '九份': {'lng': 121.842721, 'lat': 25.112721, 'full': '新北市九份'},
        '淡水': {'lng': 121.452721, 'lat': 25.172721, 'full': '新北市淡水'},
        '基隆': {'lng': 121.742721, 'lat': 25.132721, 'full': '台湾省基隆市'},
    }
    
    # 检查是否包含详细地址特征（楼号、室号、单元号等）
    has_detail_markers = any(marker in address for marker in ['号', '楼', '室', '单元', '栋', '幢', '层', '铺', '店', '弄', '巷'])

    # === 完全禁用预设地址库，强制使用API ===
    # 精确匹配（已禁用）
    # if address in address_db:
    #     result = address_db[address]
    #     return jsonify({
    #         'success': True,
    #         'lng': result['lng'],
    #         'lat': result['lat'],
    #         'display_name': result['full']
    #     })

    # 模糊匹配（已禁用）
    # if not has_detail_markers:
    #     best_match = None
    #     best_key_len = 0
    #     for key, value in address_db.items():
    #         if key in address or address in key:
    #             if len(key) > best_key_len:
    #                 best_key_len = len(key)
    #                 best_match = value
    #
    #     if best_match:
    #         return jsonify({
    #             'success': True,
    #             'lng': best_match['lng'],
    #             'lat': best_match['lat'],
    #             'display_name': best_match['full']
    #         })

    # 调用高德地图API进行精确地理编码
    import urllib.parse

    def try_geocode(addr_str, city='杭州市', retry=3):
        import urllib.parse
        import time
        encoded_address = urllib.parse.quote(addr_str)
        url = f'https://restapi.amap.com/v3/geocode/geo?address={encoded_address}&city={city}&key=c1570e197498458e2a67802d90dd4bf2'
        for attempt in range(retry):
            try:
                response = requests.get(url, timeout=15)
                data = response.json()
                info = data.get('info', '')
                if 'CUQPS' in info:  # 并发超限，等待后重试
                    wait_time = (attempt + 1) * 0.5
                    print(f"    高德并发超限，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                print(f"  高德API [{addr_str[:30]}...]: status={data.get('status')}, info={info}, count={data.get('count')}")
                if data.get('status') == '1' and data.get('geocodes') and len(data['geocodes']) > 0:
                    geocode = data['geocodes'][0]
                    location = geocode.get('location', '')
                    if location:
                        return {
                            'success': True,
                            'lng': float(location.split(',')[0]),
                            'lat': float(location.split(',')[1]),
                            'display_name': geocode.get('formatted_address', addr_str),
                            'district': geocode.get('district', '')
                        }
                else:
                    print(f"    响应内容: {data}")
                break  # 其他错误不重试
            except Exception as e:
                print(f"    高德API错误: {e}")
                break
        return None

    def is_valid_hangzhou_coords(lng, lat):
        hangzhou_bounds = {
            'min_lat': 29.65, 'max_lat': 30.55,
            'min_lng': 118.88, 'max_lng': 121.00
        }
        return (hangzhou_bounds['min_lat'] <= lat <= hangzhou_bounds['max_lat'] and
                hangzhou_bounds['min_lng'] <= lng <= hangzhou_bounds['max_lng'])

    def extract_target_district(address):
        import re
        match = re.search(r'(杭州市\s*[^\s]*?区|杭州市\s*[^\s]*?县)', address)
        if match:
            return match.group(1).replace(' ', '')
        match = re.search(r'([^\s]*?区|[^\s]*?县)', address)
        return match.group(1) if match else ''

    hangzhou_district_coords = {
        '上城区': (120.197, 30.227),
        '下城区': (120.165, 30.275),
        '拱墅区': (120.132, 30.311),
        '西湖区': (120.130, 30.259),
        '滨江区': (120.208, 30.208),
        '萧山区': (120.254, 30.178),
        '余杭区': (120.155, 30.274),
        '临平区': (120.310, 30.425),
        '钱塘区': (120.320, 30.318),
        '富阳区': (119.952, 30.047),
        '临安区': (119.240, 30.233),
        '桐庐县': (119.643, 29.825),
        '淳安县': (119.043, 29.605),
    }

    def try_geocode_with_validation(addr_str, city='杭州市', target_district=''):
        result = try_geocode(addr_str, city)
        if not result:
            return None
        if not is_valid_hangzhou_coords(result['lng'], result['lat']):
            print(f"    坐标超出杭州市范围，拒绝")
            return None
        if target_district:
            if result['district']:
                if target_district not in result['district'] and result['district'] not in target_district:
                    print(f"    区名不匹配：目标={target_district}, 实际={result['district']}，拒绝")
                    return None
            else:
                target_coords = None
                for district_name, coords in hangzhou_district_coords.items():
                    if district_name in target_district or target_district in district_name:
                        target_coords = coords
                        break
                if target_coords:
                    for district_name, coords in hangzhou_district_coords.items():
                        if district_name == target_district or target_district == district_name:
                            continue
                        distance = ((result['lng'] - coords[0])**2 + (result['lat'] - coords[1])**2) ** 0.5
                        if distance < 0.02:
                            print(f"    坐标匹配到错误区{district_name}（距离{distance:.3f}），拒绝")
                            return None
                    target_distance = ((result['lng'] - target_coords[0])**2 + (result['lat'] - target_coords[1])**2) ** 0.5
                    if target_distance > 0.15:
                        print(f"    坐标偏离目标区中心过远（距离{target_distance:.3f}），拒绝")
                        return None
        return result

    # 1. 尝试原始地址
    target_district = extract_target_district(address)
    print(f"  目标区县: {target_district}")

    # === 完全禁用预定义区坐标，强制使用API ===
    # 如果地址包含区名，直接使用预定义坐标（已禁用）
    # if target_district:
    #     for district_name, coords in hangzhou_district_coords.items():
    #         if district_name in target_district or target_district in district_name:
    #             print(f"  地址包含区名，直接使用预定义坐标 {district_name}: {coords}")
    #             return jsonify({
    #                 'success': True,
    #                 'lng': coords[0],
    #                 'lat': coords[1],
    #                 'display_name': address
    #             })

    result = try_geocode_with_validation(address, target_district=target_district)
    if result:
        return jsonify(result)

    # 2. 尝试简化地址 - 逐步去除详细部分
    simplified = address

    # 去除室、号、栋、单元等详细编号
    import re
    patterns = [
        r'\s+\d+栋\s*[A-Z]+座\s*\d+层\s*\d+室$',  # 6栋A座3层3245室
        r'\s+[A-Z]+座\s*\d+层\s*\d+室$',  # A座3层3245室
        r'\s+\d+栋\s*[A-Z]+座\s*\d+层$',  # 6栋A座3层
        r'\s+\d+栋\s*[A-Z]+座$',  # 6栋A座
        r'\s+[A-Z]+座\s*\d+层$',  # A座3层
        r'\s+[A-Z]+座$',  # A座
        r'\s+\d+栋\s*\d+层\s*\d+室$',  # 6栋3层3245室
        r'\s+\d+栋\s*\d+层$',  # 6栋3层
        r'\s+\d+栋$',  # 6栋
        r'\s*\d+[-]\d+[-]\d+号?工位$',  # 609-133-1号工位
        r'\s*\d+[-]\d+号?工位$',  # 609-133号工位
        r'\s+\d+[-]\d+室$',  # 6-21041室
        r'\s+\d+室\s*-\s*\d+$',  # 2123室- 4 或 2123 室- 4
        r'\s+\d+ 室\s*-\s*\d+$',  # 2123 室- 4 (数字和室之间有空格)
        r'\s+\d+室\s*$',  # 3245室 (在末尾)
        r'\s+\d+室$',  # 3245室
        r'\s+-\s*\d+$',  # -4
        r'\s+-\s*$',  # 末尾的 -
        r'\s+\d+[-]\d+$',  # 6-21041
        r'\s*\d+楼\s*\d+室$',  # 5楼507室
        r'\s*\d+楼$',  # XX楼
        r'\s+\d+层$',  # 3层
        r'\s+\d+号$',  # 266号
        r'\s+\d+号\s+\d+栋',  # 266号6栋 (保留)
        r'\s+\d+号\s+\d+室',  # 266号6室 (保留)
        r'\s+\d+室?\s+\d+层',  # 6室3层 (保留)
        r'\s+\d+号\s+\d*[室单元栋编排]+$',  # 45栋01号200室
        r'\s*[A-Z]+\s*座\s*\d+\s*层',  # A座3层
        r'\s*[A-Z]+\s*座\s*\d+',  # A座3
        r'\s*座\s*\d+层',  # 座3层
        r'\s*座\s*\d+',  # 座3
        r'\s*\d+商铺$',  # 商铺
        r'\s*\d+栋',  # XX栋
        r'\s*\d+号',  # XX号
        r'\s*工位$',  # 工位
        r'\s*室杠\s*\d+$',  # 室杠 1
        r'\s*杠\s*\d+$',  # 杠 1
        r'\s+室$',  # 室
        r'\s+座$',  # 座
        r'\s+-$',  # 末尾的 -
        r'\s+\d+$',  # 末尾的纯数字
    ]

    for pattern in patterns:
        test_simplified = re.sub(pattern, '', simplified)
        test_simplified = test_simplified.strip()
        if test_simplified != simplified and len(test_simplified) >= 6:
            print(f"  尝试简化地址: {test_simplified}")
            result = try_geocode_with_validation(test_simplified, target_district=target_district)
            if result:
                result['display_name'] = address
                return jsonify(result)
            simplified = test_simplified
        else:
            simplified = re.sub(pattern, '', simplified).strip()

    # 4. 尝试只保留到区级别
    district_match = re.search(r'(杭州市[^\s区]+区)', address)
    if not district_match:
        district_match = re.search(r'(杭州[^\s]+区)', address)
    if district_match:
        simplified = district_match.group(1)
        print(f"  尝试简化到区域: {simplified}")
        result = try_geocode_with_validation(simplified, target_district=target_district)
        if result:
            result['display_name'] = address
            return jsonify(result)

    # 5. 尝试只保留路/街级别
    road_match = re.search(r'(杭州市[^\s]+?(?:路|街|道))', address)
    if road_match:
        simplified = road_match.group(1)
        print(f"  尝试简化到道路: {simplified}")
        result = try_geocode_with_validation(simplified, target_district=target_district)
        if result:
            result['display_name'] = address
            return jsonify(result)

    # 6. 如果目标区县已知但所有API尝试都失败，使用预定义的区中心坐标（备用方案）
    if target_district:
        for district_name, coords in hangzhou_district_coords.items():
            if district_name in target_district or target_district in district_name:
                print(f"  API匹配失败，使用预定义坐标 {district_name}: {coords}")
                return jsonify({
                    'success': True,
                    'lng': coords[0],
                    'lat': coords[1],
                    'display_name': address
                })

    # 未找到匹配 - 返回失败
    return jsonify({
        'success': False,
        'message': '无法识别该地址，请检查地址是否正确或尝试简化地址'
    })

@app.route('/map_image', methods=['GET', 'POST'])
def map_image():
    addresses = []
    route = []
    gps_lng = None
    gps_lat = None
    
    if request.method == 'POST':
        data = request.get_json() or {}
        addresses = data.get('addresses', [])
        route = data.get('route', [])
        gps_lng = data.get('gps_lng')
        gps_lat = data.get('gps_lat')
    else:
        addresses_json = request.args.get('addresses', '[]')
        route_json = request.args.get('route', '[]')
        try:
            addresses = json.loads(addresses_json)
        except:
            addresses = []
        try:
            route = json.loads(route_json)
        except:
            route = []
        gps_lng = request.args.get('gps_lng', type=float)
        gps_lat = request.args.get('gps_lat', type=float)

    svg_content = generate_svg_map(addresses, route, gps_lng=gps_lng, gps_lat=gps_lat)
    return send_file(io.BytesIO(svg_content.encode('utf-8')), mimetype='image/svg+xml')

@app.route('/route_detail', methods=['GET', 'POST'])
def route_detail():
    import math
    import re
    
    def calculate_distance(lat1, lng1, lat2, lng2):
        R = 6371
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lng2 - lng1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def extract_area(name):
        # 先匹配 "杭州市XX区"
        match = re.search(r'杭州市\s*([^\s]*?区|县)', name)
        if match:
            return match.group(1).replace(' ', '')
        # 再匹配 "杭州XX区"（不带"市"）
        match = re.search(r'杭州\s*([^\s]*?区|县)', name)
        if match:
            return match.group(1).replace(' ', '')
        # 最后匹配独立的 "XX区" 或 "XX县"
        match = re.search(r'([\u4e00-\u9fa5]{2,4}(?:区|县))', name)
        return match.group(1) if match else '其他区域'

    if request.method == 'POST':
        addresses_json = request.form.get('addresses', '[]')
        route_json = request.form.get('route', '[]')
        start_index = request.form.get('start', '')
    else:
        addresses_json = request.args.get('addresses', '[]')
        route_json = request.args.get('route', '[]')
        start_index = request.args.get('start', '')

    try:
        addresses = json.loads(addresses_json) if addresses_json else []
    except:
        addresses = []
    try:
        route = json.loads(route_json) if route_json else []
    except:
        route = []

    html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>路线详情</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .route-item {{ display: flex; align-items: flex-start; padding: 15px; border-bottom: 1px solid #eee; }}
        .route-item:last-child {{ border-bottom: none; }}
        .step-number {{ width: 40px; height: 40px; background: #007bff; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; }}
        .step-content {{ margin-left: 15px; flex: 1; }}
        .step-name {{ font-size: 16px; font-weight: bold; color: #333; }}
        .step-distance {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .total-distance {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 18px; text-align: center; }}
        .copy-btn {{ display: inline-block; padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; font-size: 14px; cursor: pointer; text-decoration: none; }}
        .copy-btn:hover {{ background: #218838; }}
        .header-row {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
        .area-header {{ font-size: 18px; font-weight: bold; color: #667eea; margin: 25px 0 15px 0; padding: 10px 15px; background: #f0f0ff; border-radius: 8px; border-left: 4px solid #667eea; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-row">
            <button class="copy-btn" onclick="copyRouteInfo()">📋 复制路线</button>
        </div>
        <h1>🗺️ 路线详情</h1>
        <div id="routeList">
'''

    # 按区域分组（保留路线中的出现顺序）
    area_groups = {}
    area_order = []
    for i in route:
        addr = addresses[i]
        area = extract_area(addr.get('name', ''))
        if area not in area_groups:
            area_groups[area] = []
            area_order.append(area)
        area_groups[area].append(i)

    step_number = 1

    # 按路线中的顺序逐区域展示
    for area in area_order:
        html += f'<div class="area-header">📍 {area}路线</div>'
        for i in area_groups[area]:
            addr = addresses[i]
            shop_name = addr.get('shop_name', '')
            shop_display = f'<span style="color:#667eea;font-weight:bold;">【{shop_name}】</span>' if shop_name else ''

            html += f'''
            <div class="route-item">
                <div class="step-number">{step_number}</div>
                <div class="step-content">
                    <div class="step-name">{shop_display}{addr.get('name', '未知地址')}</div>
                    <div class="step-distance">{addr.get('full_name', '')}</div>
                </div>
            </div>
'''
            step_number += 1

    # 生成复制文本（按路线中的顺序）
    copy_lines = []
    for area in area_order:
        copy_lines.append(f"📍 {area}")
        copy_lines.append("")
        area_items = area_groups[area]
        for idx, i in enumerate(area_items):
            addr = addresses[i]
            shop_name = addr.get('shop_name', '')
            addr_full = addr.get('name', '未知')
            if shop_name:
                copy_lines.append(f"   【{shop_name}】 | {addr_full}")
            else:
                copy_lines.append(f"   {addr_full}")
            copy_lines.append("")
        copy_lines.append("")

    copy_text = "\\n".join(copy_lines)

    html += f'''
        </div>
    </div>
    <script>
    function copyRouteInfo() {{
        let text = "🗺️ 路线规划\\n";
        text += "=".repeat(20) + "\\n";
        text += `{copy_text}` + "\\n";
        text += "=".repeat(20) + "\\n";
        navigator.clipboard.writeText(text).then(() => {{
            const btn = document.querySelector('.copy-btn');
            const originalText = btn.textContent;
            btn.textContent = '✅ 已复制';
            btn.style.background = '#28a745';
            setTimeout(() => {{
                btn.textContent = originalText;
                btn.style.background = '';
            }}, 1500);
        }});
    }}
    </script>
</body>
</html>'''
    return html

if __name__ == '__main__':
    print("启动地图应用...")
    print("请在浏览器中访问: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
