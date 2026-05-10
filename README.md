# 🚲 CityBike-Sim

都市共享单车模拟与可视化平台。

*   **🗺️ 真实城市场景解析**：直接导入 OpenStreetMap 真实地图数据，自动生成含高程变化的复杂路网。
*   **📍 战略级点位规划**：划定运营区、推荐停放点（P 点）、禁停区。
*   **🚚 硬核的车队调度与再平衡**：潮汐现象博弈、运力匹配。
*   **🌤️ 动态外部环境**：天气系统、特殊事件（演唱会散场等高并发需求）。
*   **📊 极致的数据可视化**：实时供需热力图、OD 轨迹流、运力覆盖。

---

## ✅ 项目状态

分层架构、领域模型、模拟引擎核心已搭建完成。Phase 1–5 全部实现，**Demo 已可运行**。

📖 [架构文档](docs/architecture.md) · 🗺️ [路线图看板](https://github.com/kcccn/sharedBikes/issues/78)

## 🚀 路线图

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 1 | 真实地图数据接入 (OSM + 布站 + 配置) | ✅ 完成 |
| Phase 2 | 经济系统：Ledger-First 架构 | ✅ 完成 |
| Phase 3 | 调度系统集成（调度分析→执行→记账） | ✅ 完成 |
| Phase 4 | API 接线 + NPC 需求引擎 | ✅ 完成 |
| Phase 4.5 | EventBus 发布/订阅层 | ✅ 完成 |
| Phase 5 | Web 前端 MVP：Leaflet 地图 + WebSocket 实时推送 | ✅ 完成 |
| Phase 6 | 成就引擎 · 多人排行榜 · 热力图 | 🚧 进行中 |

### 快速启动 Demo

```bash
cd backend
uvicorn app.main:app --reload
# 浏览器打开 http://localhost:8000 查看 Leaflet 实时地图
```

### Phase 6 当前任务

| 任务 | 说明 |
|------|------|
| AchievementEngine | 纯后端成就判定引擎（里程碑/连击/积分），零 UI 依赖 |
| Leaderboard | 异步排行榜 API，基于 Ledger 数据聚合 |
| Heatmap | 站点级 demand_factor 着色，网格级 → 后续版本 |

详见 [#120](https://github.com/kcccn/sharedBikes/issues/120)

## 🤝 参与贡献

查看 [Issues](https://github.com/kcccn/sharedBikes/issues) 页面，或关注 [#78 路线图看板](https://github.com/kcccn/sharedBikes/issues/78) 了解当前进度。
