# DrivePerceptionLab

> **自动驾驶感知论文精读与可迁移算法设计卡。** 每天产出两份可以真正学懂、可以回查
> 证据的研究资产：一篇自动驾驶感知深度精读，
> 一张跨领域可迁移的算法 Taste 设计卡。精读系统覆盖 13 个感知主方向；设计卡只收
> 有明确瓶颈、接口、受控证据和失败边界的模块、主干网络或训练单元。

[▶ 今天的论文精读](#-今日论文精读) · [🧩 今天的算法 Taste](#-今日算法-taste) ·
[🗺 13 类学习路线](index/topics.md) · [📚 全部精读](index/papers.md) ·
[💡 全部设计卡](taste/README.md)

<!-- AUTO:STATS:START -->
**7 篇精读** · **7 篇正式录用** · **7 篇关键源码已审** · **2 张算法 Taste 卡** · **覆盖 7/13 个感知主方向** · 最近更新：**2026-08-02**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ 今日论文精读

### [V2X-ViT: Vehicle-to-Everything Cooperative Perception with Vision Transformer](notes/2026/2026-08-02-v2x-vit.md)

**ECCV 2022**

> V2X-ViT 用时空校正、类型化跨节点注意力和多尺度空间注意力融合车路特征；但主证据仅来自仿真，固定源码的 ego、噪声与压缩行为和论文并不完全一致。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://www.ecva.net/papers/eccv_2022/papers_ECCV/html/4589_ECCV_2022_paper.php) · **协同感知** · LiDAR + V2X + Vehicle State · Cooperative Perception · Feature-level Fusion · Heterogeneous Attention · Pose Error · Communication Latency · Transformer · Simulation · 3D Object Detection · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136990106.pdf) · [官方代码 @ f0e6c13f](https://github.com/DerrickXuNu/v2x-vit/tree/f0e6c13f41e916548b2d8aba61e42a18ce980416)
<!-- AUTO:LATEST:END -->

<!-- AUTO:TASTE:START -->
## 🧩 今日算法 Taste

### [Heterogeneous Multi-Agent Self-Attention (HMSA)](taste/2026/2026-08-02-hmsa.md)

> 让节点类型决定 Q/K/V、让有向边类型决定注意力与消息变换，在同坐标格内显式建模异构来源关系。

**来自：** [V2X-ViT: Vehicle-to-Everything Cooperative Perception with Vision Transformer](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136990106.pdf) · [正式录用](https://www.ecva.net/papers/eccv_2022/papers_ECCV/html/4589_ECCV_2022_paper.php) · **Type-Conditioned Relational Attention**

**可迁移到：** Multi-Sensor BEV · Cooperative Occupancy · Temporal Memory · Multi-Robot Fusion

**先记边界：** 它依赖可靠坐标对齐与正确类型，节点对计算随 M² 增长；二值角色无法表示同类传感器质量差异，也没有真实 V2X 证据。

[看原理图、接口合同、适用场景与反证实验 →](taste/2026/2026-08-02-hmsa.md) · [固定实现 @ f0e6c13f](https://github.com/DerrickXuNu/v2x-vit/tree/f0e6c13f41e916548b2d8aba61e42a18ce980416)
<!-- AUTO:TASTE:END -->

## 怎么开始

- **想系统学一篇论文：** 从[全部精读](index/papers.md)或
  [13 类学习路线](index/topics.md)进入，沿“原图 → 公式 → 结果 → 固定源码 → 证据边界”读完；
- **想提高算法 taste、寻找可迁移 idea：** 打开[算法 Taste](taste/README.md)，先判断
  瓶颈是否同构，再核对接口、消融、失败条件和最小反证实验；
- **想继续追研究问题：** 查看[开放问题](index/open_questions.md)，这里只累计真正具有
  跨论文价值、仍可被实验区分的问题。

## 最近完成

<!-- AUTO:RECENT:START -->
- **2026-08-02 · ECCV 2022** — [V2X-ViT: Vehicle-to-Everything Cooperative Perception with Vision Transformer](notes/2026/2026-08-02-v2x-vit.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-07-29 · ICLR 2023** — [MapTR: Structured Modeling and Learning for Online Vectorized HD Map Construction](notes/2026/2026-07-29-maptr.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-07-28 · CoRL 2022** — [SurroundDepth: Entangling Surrounding Views for Self-Supervised Multi-Camera Depth Estimation](notes/2026/2026-07-28-surrounddepth.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
<!-- AUTO:RECENT:END -->

## 推荐下一篇或下一张设计卡

欢迎推荐已经公开的论文或官方实现。请先看[贡献说明](CONTRIBUTING.md)，再
[提交公开建议](https://github.com/drxadqz/drive-perception-lab/issues/new?template=content-suggestion.yml)。
不要在公开 Issue 中披露未投稿想法、私有实验或尚未公开的项目细节。

<details>
<summary><strong>证据标签与阅读说明</strong></summary>

- **[论文]**：论文正文、补充材料或官方 proceedings 直接支持；
- **[源码]**：固定 commit 的官方仓库直接支持；
- **[判断]**：基于论文与源码的分析，不冒充作者结论；
- **[未核验]**：尚未运行 checkpoint、联系作者或完成独立复现。

摘要、术语、实验、结论翻译以及图表、公式、源码链接和公开内容边界见
[阅读与维护说明](docs/reading-guide.md)。

</details>

<details>
<summary><strong>选文与公开范围</strong></summary>

仓库区分正式录用、预印本、源码已审和结果已复现，完整标准见
[选文规则](SELECTION_POLICY.md)。公开内容只包含可以由论文或源码回查的事实、
一般性分析和研究问题；未投稿方案的完整机制、私有结果和实验配方不公开。

</details>
