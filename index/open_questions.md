# 公开研究缺口雷达

[返回首页](../README.md) · [全部论文](papers.md) · [主题路线](topics.md)

这里记录的是由已读论文或源码暴露出的**待验证问题**，不是本仓库对“原创性”的
宣称。一个问题只有在获得明确证据回链后才能加入；在系统检索相邻工作之前，
“本仓库尚未读到答案”绝不等于“学界尚无答案”。

## Q001 — 长时序记忆在传感器恢复后会不会继续保留错误？

- **状态**：Active；目前只有一篇锚点论文，需要更多独立证据。
- **证据来源**：[ST-Occ 精读](../notes/2026/2026-07-24-st-occ.md)。
- **已知事实**：ST-Occ 展示了长历史对 Occupancy 的收益，但论文没有报告
  camera blackout、freeze、时序错位或故障恢复阶段的压力测试。
- **仍不知道**：长记忆带来的稳定性，是否会在异常输入消失后转化为持续误差。
- **下一次更新条件**：读到第二篇包含“时序状态 + 传感器故障/恢复”实验的论文，
  或完成一个能区分瞬时误差与恢复后误差的公开复现实验。
- **检索边界**：sensor failure、temporal memory contamination、post-fault
  recovery、streaming perception robustness。

## Q002 — 较低的时间波动是否真的意味着预测更正确？

- **状态**：Active。
- **证据来源**：[ST-Occ 的实验与指标审查](../notes/2026/2026-07-24-st-occ.md)。
- **已知事实**：ST-Occ 的 mSTCV 改善支持“预测更稳定”，但该指标的实现使用
  GT static mask 和 GT flicker correction。
- **仍不知道**：一个稳定但持续错误的模型，是否也会得到更好的时间一致性分数。
- **下一次更新条件**：找到同时报告 temporal consistency、逐帧正确性和
  错误恢复的评测工作。
- **检索边界**：temporal consistency metrics、flicker、calibration、
  persistent error、correctness-aware evaluation。

## Q003 — 训练时与测试时的运动信息差异会怎样影响长期状态？

- **状态**：Active。
- **证据来源**：[ST-Occ 源码审计](../notes/2026/2026-07-24-st-occ.md)。
- **已知事实**：该实现训练时可以使用 GT flow，测试时则把前一帧预测 flow
  保存到后续时序路径；论文没有单独隔离两者差异。
- **仍不知道**：运动估计误差会只影响当前帧，还是会通过后续采样路径累积。
- **下一次更新条件**：找到或运行明确比较 GT / predicted / no-flow 的长期实验。
- **检索边界**：occupancy flow、motion-conditioned memory、exposure bias、
  recurrent sampling error。

## Q004 — 流式感知模型的“完整状态”应该如何定义和复现？

- **状态**：Active。
- **证据来源**：[ST-Occ 源码中的 persistent-state 审计](../notes/2026/2026-07-24-st-occ.md)。
- **已知事实**：真实推理状态包含 feature、validity/count、class distribution、
  uncertainty、flow、scene metadata 和 frame counter，并非只有论文图中的单个
  memory tensor。
- **仍不知道**：现有流式 benchmark 是否足以检查 reset、snapshot、restore、
  batch-slot 隔离和跨设备确定性。
- **下一次更新条件**：读到提供显式状态接口或 state lifecycle 测试的流式感知工作。
- **检索边界**：streaming state、stateful inference、snapshot/restore、
  sequence isolation、deterministic evaluation。

## 已关闭问题

被既有工作充分覆盖、被实验否定或不再值得投入的问题移到这里，并保留终止证据
与日期；不直接删除。
