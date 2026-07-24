# 全部论文精读

[返回首页](../README.md) · [主题路线](topics.md) · [开放问题](open_questions.md)

> 本页由 `index/papers.csv` 自动生成。请不要手工编辑；运行
> `python scripts/rebuild_index.py` 更新。

共 **1** 篇，其中 **1** 篇已由权威来源核验为正式录用。
“代码已审”不等于“结果已复现”。

| 日期 | 论文 | Venue / 状态 | 主题 | 一句话结论 | 证据状态 |
|---|---|---|---|---|---|
| 2026-07-24 | **Occupancy Learning with Spatiotemporal Memory**<br>[精读](../notes/2026/2026-07-24-st-occ.md) · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e) | ICCV 2025<br>正式录用 | 3D Occupancy<br>Temporal Memory<br>Autonomous Driving | ST-Occ 用场景坐标中的持久 3D 记忆提升 Occupancy 精度与时间一致性，但证据仍局限于单一数据域，且源码中的状态更新比论文示意更复杂。 | 论文、补充材料与官方源码已审<br>官方源码已核到固定 commit<br>**Checkpoint 未运行** |

## 状态解释

- **正式录用**：已通过 proceedings、OpenReview decision 或出版社页面核验；
- **预印本**：尚无权威录用来源，不能据此称为顶会论文；
- **代码已审**：阅读了固定 commit 的关键实现；
- **Checkpoint not run**：论文数字尚未被本仓库独立验证。
