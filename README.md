# 🚲 CityBike-Sim: Urban Operator (共享单车运营模拟器)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**CityBike-Sim** 是一款基于真实城市地理数据的硬核模拟经营游戏。你将扮演一家共享单车初创公司的区域运营总监，在真实的城市路网中进行战略布局。告别传统的网格化虚拟地图，你的每一个决策都将基于真实的道路拓扑、海拔高程和城市形态。

## 🎯 核心玩法 (Core Gameplay)

*   **🗺️ 真实城市场景解析**
    *   **拒绝纯平网格：** 游戏直接导入真实的开源地图数据（如 OpenStreetMap），自动生成包含高程变化的复杂路网结构。
    *   **因地制宜：** 挑战不同的城市形态！无论是如兰州般受限于地形的"线性城市"带来的极度潮汐现象，还是巨型平原城市的无限扩张，都需要完全不同的运营策略。
*   **📍 战略级点位规划**
    *   **圈地运动：** 划定你的首发"运营区"，并随着资金积累逐步扩张。
    *   **禁停与推荐：** 在核心商圈、地铁站口设立"推荐停放点（P点）"以规范潮汐车流，或避开市政设置的"禁停区"以免缴纳高额罚款。
*   **🚚 硬核的车队调度与再平衡 (Rebalancing)**
    *   **潮汐现象博弈：** 面对早晚高峰"旱的旱死，涝的涝死"的局面，你需要雇佣并规划调度员的排班与路线。
    *   **运力匹配：** 派遣三轮车穿梭于小巷进行微调，或使用大型厢式货车在主干道进行跨区大批量"捞车"。
*   **🌤️ 动态外部环境**
    *   引入动态天气系统（暴雨、台风将导致订单暴跌）和特殊事件（大型演唱会散场带来的瞬时局部高并发需求）。

## 📊 极致的数据可视化 (Data Visualization)

本项目的核心乐趣在于**看着混沌的城市交通在你的治理下变得井然有序**。游戏内置工业级的数据面板，为你提供极致的"成就感"：

*   **🔥 实时供需热力图 (Heatmaps)：** 
    地图底层实时渲染区域内的寻车热度与车辆淤积预警。红色代表极度缺车，深紫色代表车辆严重超负荷停放。
*   **✨ 轨迹流线动画 (OD Flow Lines)：** 
    加速时间，观看成百上千条发光的流线在城市路网中穿梭。每完成一次成功的骑行，都会在地图上留下一道流星般的轨迹。
*   **📈 沉浸式财务与效率大屏：**
    *   **周转率仪表盘：** 实时追踪每辆单车的日均骑行次数（Turnover Rate）。
    *   **调度效率图表：** 散点图分析调度员行驶里程与干预成功率的 ROI（投资回报率）。
    *   **沉没地图：** 可视化展示丢失、损坏车辆在城市中的最后定位（电子坟场）。

## 🛠️ 技术栈构想 (Tech Stack)

*(欢迎在 [Issue 中参与讨论](https://github.com/kcccn/sharedBikes/issues))！*

*   **前端与可视化：** React / Vue3 + Deck.gl / Mapbox GL JS (处理大规模 WebGL 地理数据渲染)
*   **后端与模拟引擎：** Python (FastAPI) / Go + PostGIS (处理复杂空间查询)
*   **寻路与调度算法：** 结合 A* 算法与遗传算法（GA）优化调度卡车的多目标路径规划。

## ✅ Phase 0: 项目骨架（已完成）

分层架构、领域模型定义、API 端点、模拟引擎核心均已搭建完成。

📖 [架构文档](docs/architecture.md)

## 🚀 路线图 (Roadmap)

每个 Phase 都有对应的 Issue 追踪进度，欢迎参与讨论！

### Phase 1: 基础设施 — 真实地图解析与静态车辆投放
| 任务 | 状态 | 说明 |
|------|------|------|
| [#21 RFC: 方案设计](https://github.com/kcccn/sharedBikes/issues/21) | 🆕 讨论中 | 选型 osmnx vs osmium，确定技术路线 |
| [#23 OSM 路网解析](https://github.com/kcccn/sharedBikes/issues/23) | 📋 待开始 | OSM 数据 → City.Node/Edge 转换 |
| [#25 站点自动放置](https://github.com/kcccn/sharedBikes/issues/25) | 📋 待开始 | 在路网上自动生成 Station |
| [#34 城市配置系统](https://github.com/kcccn/sharedBikes/issues/34) | 📋 待开始 | YAML 配置 + 多城市支持 |
| [#27 MapService 集成](https://github.com/kcccn/sharedBikes/issues/27) | 📋 待开始 | 解析器+布站+缓存的完整管线 |
| [#36 集成测试 & 演示](https://github.com/kcccn/sharedBikes/issues/36) | 📋 待开始 | E2E 验证与演示脚本 |

### Phase 2: 动态城市
*引入基于时间的 NPC 需求生成机制（通勤潮汐模拟）—— 待 Phase 1 完成后分解*

### Phase 3: 调度博弈
*加入调度员派遣与财务结算系统 —— 待 Phase 2 完成后分解*

### Phase 4: 视觉盛宴
*接入 Deck.gl，完成热力图与 OD 轨迹流的高帧率渲染 —— 待 Phase 3 完成后分解*

## 🤝 参与贡献 (Contributing)

无论你是 GIS 专家、前端数据可视化狂魔，还是对城市规划与交通算法感兴趣的极客，这里都欢迎你的加入！请查看 [Issues](https://github.com/kcccn/sharedBikes/issues) 页面，从 Phase 1 的讨论开始参与吧。
