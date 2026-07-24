# 自动驾驶顶会、顶刊与前沿论文精读

> 每天早上 **08:00（Asia/Shanghai）** 精读一篇高质量论文，并把论文证据、
> 官方源码证据、局限与尚未解决的问题整理成一份可核查的中文笔记。

<!-- AUTO:STATS:START -->
**1 篇精读** · **1 篇正式录用** · **1 篇关键源码已审** · 最近更新：**2026-07-24**
<!-- AUTO:STATS:END -->

[最新精读](#最新精读) ·
[全部论文](index/papers.md) ·
[主题路线](index/topics.md) ·
[开放问题](index/open_questions.md) ·
[选文规则](SELECTION_POLICY.md)

## 最新精读

<!-- AUTO:LATEST:START -->
### 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](notes/2026/2026-07-24-st-occ.md)

`ICCV 2025` · `正式录用` · `选文 9.8/10`

> **3 分钟结论：** ST-Occ 用场景坐标中的持久 3D 记忆提升 Occupancy 精度与时间一致性，但证据仍局限于单一数据域，且源码中的状态更新比论文示意更复杂。

| 核验项 | 当前状态 |
|---|---|
| 论文身份 | 正式录用；[官方 proceedings](https://openaccess.thecvf.com/content/ICCV2025/html/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.html) |
| 阅读深度 | 论文、补充材料与官方源码已审 |
| 独立复现 | **Checkpoint 未运行** |
| 主题 | `3D Occupancy` · `Temporal Memory` · `Autonomous Driving` |

[开始分层精读](notes/2026/2026-07-24-st-occ.md) · [论文 PDF](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [官方代码 @ 1633f62e](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)
<!-- AUTO:LATEST:END -->

## 第一次打开，从这里开始

| 你有多少时间 | 建议入口 | 你会得到什么 |
|---|---|---|
| 3 分钟 | [最新精读](#最新精读) | 论文解决什么、证据够不够、最大局限是什么 |
| 10 分钟 | 打开今日笔记的“10 分钟理解” | 方法数据流、关键结果和实验边界 |
| 30 分钟以上 | 打开今日笔记的“30 分钟深读” | 固定 commit 的源码调用链、实现差异和复现风险 |
| 想系统选题 | [主题路线](index/topics.md) → [开放问题](index/open_questions.md) | 从单篇事实走向跨论文、仍待验证的问题 |

## 怎么读一篇笔记

每份笔记都采用同一套分层结构，避免一打开就是几百行技术细节：

1. **3 分钟速读**：一句话结论、论文贡献、最强证据、最大疑点；
2. **10 分钟理解**：问题设定、方法数据流、核心实验和真正成立的结论；
3. **30 分钟深读**：源码入口、关键类/函数、持久状态、复现路径和开放问题。

笔记中的判断按证据来源标记：

| 标签 | 含义 |
|---|---|
| **[论文]** | 论文正文、补充材料或官方 proceedings 可以直接支持 |
| **[源码]** | 固定 commit 的官方仓库可以直接支持 |
| **[判断]** | 基于前两类证据的分析，不冒充作者结论 |
| **[未核验]** | 尚未运行 checkpoint、联系作者或完成独立复现 |

## 最近精读

<!-- AUTO:RECENT:START -->
| 日期 | 论文 | Venue | 主题 | 验证状态 |
|---|---|---|---|---|
| 2026-07-24 | [Occupancy Learning with Spatiotemporal Memory](notes/2026/2026-07-24-st-occ.md) | ICCV 2025 | 3D Occupancy<br>Temporal Memory<br>Autonomous Driving | 官方源码已核到固定 commit；**Checkpoint 未运行** |
<!-- AUTO:RECENT:END -->

完整、可按日期浏览的表格见 [全部论文索引](index/papers.md)。

## 研究地图

仓库不局限于单一方法，长期覆盖六条相互关联的路线：

| 路线 | 主要问题 | 重点阅读内容 |
|---|---|---|
| 3D / 4D 感知与 Occupancy | 如何构建几何一致、时序稳定的环境表征？ | Occupancy、BEV、时序记忆、流式感知 |
| 多传感器鲁棒性 | 传感器缺失、冻结、错位或恢复后，系统会怎样失效？ | 故障建模、融合、校准、不确定性 |
| 开放世界与异常 | 模型如何发现训练分布之外的对象、场景和风险？ | OOD、开放词汇、异常检测、风险估计 |
| Driving VLM / VLA | 语言与视觉推理能否可靠地连接感知、规划和动作？ | grounding、reasoning、幻觉、安全评测 |
| 驾驶世界模型 | 生成或预测的未来是否物理一致、可控且对规划有用？ | 生成、预测、规划、闭环评测 |
| 可靠性与评测 | 指标是否真的衡量正确性、恢复能力与部署风险？ | benchmark、因果对照、复现、统计 |

每条路线的推荐顺序和当前收录论文见 [主题阅读路线](index/topics.md)。

## 这个仓库与普通论文列表的区别

- **不只收藏链接**：每篇都必须读论文、补充材料和官方代码；
- **不把 arXiv 当录用证明**：顶会身份由 CVF、OpenReview、PMLR 等权威来源核验；
- **不只复述摘要**：明确区分作者证据、源码事实、个人判断和未核验事项；
- **固定源码版本**：关键实现链接到精读时的 commit，而不是会漂移的默认分支；
- **持续形成研究地图**：跨论文问题会进入开放问题索引，但不会把猜想写成已证实的新颖性；
- **公开仓库有边界**：未投稿方法名、完整算法配方、精确目标阈值和私有实验计划不公开。

<details>
<summary><strong>目录与自动更新方式</strong></summary>

```text
notes/YYYY/               每日分层精读笔记
index/papers.csv          机器可读的唯一论文索引
index/papers.md           自动生成的全部论文表
index/topics.md           主题路线与自动标签索引
index/open_questions.md   公开安全的跨论文开放问题
templates/paper_note.md   每日笔记模板
scripts/rebuild_index.py  重建首页和索引，并执行一致性检查
docs/                     仓库设计与使用说明
```

新增笔记后运行：

```bash
python scripts/rebuild_index.py
python scripts/rebuild_index.py --check
```

每日自动任务也必须执行同一脚本，因此首页、论文总表和主题索引会随新笔记一起更新。

</details>

<details>
<summary><strong>设计参考</strong></summary>

首页与索引的信息架构参考了多个高 Star 论文阅读/导航仓库，但没有照搬它们的
超长资源列表。对照记录与采用理由见
[高 Star 同类仓库设计对照](docs/repository-design-benchmarks.md)。

</details>

## 公开范围

这里记录的是**可以公开复核的文献研究**。论文事实、源码事实、一般性局限和
尚待验证的研究问题可以公开；尚未投稿的核心机制、完整实验配方、私有结果与
优先权敏感内容应保留在私有研究项目中。
