# 主题阅读路线

[返回首页](../README.md) · [全部论文](papers.md) · [开放问题](open_questions.md)

这里提供“按问题阅读”的入口。日期索引适合保持每日节奏，主题路线更适合做
文献综述、确定 baseline 和寻找真正尚未解决的问题。

## 推荐路线

| 路线 | 建议阅读顺序 | 阅读时始终追问 |
|---|---|---|
| 3D / 4D 感知与 Occupancy | 单帧几何 → 时序融合 → 流式记忆 → 未来 Occupancy | 精度提升来自哪里？状态如何更新？长历史何时变成负担？ |
| 多传感器鲁棒性 | 标准融合 → 缺失模态 → 传感器故障 → 故障后恢复 | 扰动真实吗？是否测量恢复阶段？融合模块会不会保留错误？ |
| 开放世界与异常 | 闭集检测 → OOD → 开放词汇 → 风险与校准 | “没见过”如何定义？检测分数是否经过校准？长尾是否被平均指标掩盖？ |
| Driving VLM / VLA | 视觉 grounding → 语言推理 → 规划 → 闭环动作 | 语言解释是否忠实？推理是否影响动作？幻觉怎样进入安全指标？ |
| 驾驶世界模型 | 表征预测 → 视频/Occupancy 生成 → 可控 rollout → 规划 | 视觉逼真是否等于物理正确？预测是否真的帮助规划？ |
| 可靠性与评测 | 标准 benchmark → 分层指标 → 压力测试 → 统计与复现 | 指标测到的是正确性还是稳定性？结论跨 seed、场景和域吗？ |

## 如何使用

1. 先从下方标签索引进入一篇“锚点论文”；
2. 阅读其 3 分钟结论，确认是否与当前问题有关；
3. 阅读实验边界与源码审计，记录强 baseline 和缺失对照；
4. 只有当同一问题获得多篇独立论文支持，才加入
   [开放问题](open_questions.md)；
5. “尚未被本仓库收录”不等于“学界尚未解决”，仍需单独做新颖性检索。

## 当前标签索引

<!-- AUTO:TOPICS:START -->
### 3D Occupancy (1)

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### Autonomous Driving (1)

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### Temporal Memory (1)

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)
<!-- AUTO:TOPICS:END -->
