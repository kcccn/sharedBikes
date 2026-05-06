# Contributing to CityBike-Sim

感谢你对 CityBike-Sim 的关注！🎉 无论你是 GIS 专家、前端可视化狂魔，还是城市交通算法极客，这里都有你发光的位置。

## 项目架构概览

```
src/citybike/
├── core/         # 模拟引擎核心（时钟、类型、事件循环）
├── city/         # 城市地理模块（路网解析、运营区、禁停区）
├── fleet/        # 车队管理（单车生命周期、P 点）
├── demand/       # 需求模拟（通勤潮汐、天气、事件）
├── dispatch/     # 调度再平衡（失衡检测、路径规划）
└── api/          # FastAPI REST 接口（数据供给前端）
```

## 开发流程

1. **Fork** 本仓库并克隆到本地。
2. 创建特性分支：`git checkout -b feature/你的功能描述`。
3. 安装开发依赖：`pip install -e ".[dev]"`。
4. 编写代码并确保测试通过：`pytest`。
5. 提交 Pull Request 并关联对应 Issue。

## 代码规范

- Python 版本：3.11+
- 类型注解：所有函数必须包含完整类型签名 (`mypy --strict`)
- 格式化：遵循 [PEP 8](https://peps.python.org/pep-0008/)（ruff 检查）
- 提交信息：遵循 [Conventional Commits](https://www.conventionalcommits.org/)

## 路线图

| Phase | 内容 | 状态 |
|-------|------|------|
| 1 | 基础设施 — 地图解析与静态投放 | 🔨 进行中 |
| 2 | 动态城市 — NPC 需求生成与潮汐模拟 | 📋 规划中 |
| 3 | 调度博弈 — 调度员派遣与财务结算 | 📋 规划中 |
| 4 | 视觉盛宴 — Deck.gl 热力图与 OD 流线 | 📋 规划中 |
