# 🚲 CityBike-Sim

都市共享单车模拟与可视化平台。

*   **🗺️ 真实城市场景解析**：直接导入 OpenStreetMap 真实地图数据，自动生成含高程变化的复杂路网。
*   **📍 战略级点位规划**：划定运营区、推荐停放点（P 点）、禁停区。
*   **🚚 硬核的车队调度与再平衡**：潮汐现象博弈、运力匹配。
*   **🌤️ 动态外部环境**：天气系统、特殊事件（演唱会散场等高并发需求）。
*   **📊 极致的数据可视化**：实时供需热力图、OD 轨迹流、运力覆盖。

---

## ✅ Phase 0: 项目骨架（已完成）

分层架构、领域模型定义、API 端点、模拟引擎核心均已搭建完成。

📖 [架构文档](docs/architecture.md)

## 🚀 路线图 (Roadmap)

每个 Phase 都有对应的 Issue 追踪进度，欢迎参与讨论！

### Phase 1: 基础设施 — 真实地图解析与静态车辆投放
| 任务 | 状态 | PR / 说明 |
|------|------|-----------|
| [#21 RFC: 方案设计](https://github.com/kcccn/sharedBikes/issues/21) | 🆕 讨论中 | 选型 osmnx vs osmium，确定技术路线 |
| [#23 OSM 路网解析](https://github.com/kcccn/sharedBikes/issues/23) | ✅ 已实现 | OSM 数据 → City.Node/Edge 转换管线 |
| [#25 站点自动放置](https://github.com/kcccn/sharedBikes/issues/25) | ✅ 已实现 | 基于路网节点度的贪心站点生成算法 |
| [#34 城市配置系统](https://github.com/kcccn/sharedBikes/issues/34) | ✅ 已实现 | TOML 配置 + CityLoader + 多城市支持 |
| [#27 MapService 集成](https://github.com/kcccn/sharedBikes/issues/27) | ✅ 已实现 | 配置→解析→布站→缓存的完整管线 |
| [#36 集成测试 & 演示](https://github.com/kcccn/sharedBikes/issues/36) | ✅ 已实现 | E2E 验证与演示脚本 |

### Phase 2: 动态城市
*引入基于时间的 NPC 需求生成机制（通勤潮汐模拟）—— 待 Phase 1 完成后分解*

### Phase 3: 调度博弈
*加入调度员派遣与财务结算系统 —— 待 Phase 2 完成后分解*

### Phase 4: 视觉盛宴
*接入 Deck.gl，完成热力图与 OD 轨迹流的高帧率渲染 —— 待 Phase 3 完成后分解*

## 🤝 参与贡献 (Contributing)

请查看 [Issues](https://github.com/kcccn/sharedBikes/issues) 页面，从 Phase 1 的讨论开始参与吧。
