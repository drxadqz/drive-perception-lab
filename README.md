# DrivePerceptionLab

> **自动驾驶感知论文精读与可迁移算法设计卡。** 每天产出两份可以真正学懂、可以回查
> 证据的研究资产：一篇自动驾驶感知深度精读，
> 一张跨领域可迁移的算法 Taste 设计卡。精读系统覆盖 13 个感知主方向；设计卡只收
> 有明确瓶颈、接口、受控证据和失败边界的模块、主干网络或训练单元。

[▶ 今天的论文精读](#-今日论文精读) · [🧩 今天的算法 Taste](#-今日算法-taste) ·
[🗺 13 类学习路线](index/topics.md) · [📚 全部精读](index/papers.md) ·
[💡 全部设计卡](taste/README.md)

<!-- AUTO:STATS:START -->
**9 篇精读** · **9 篇正式录用** · **9 篇关键源码已审** · **4 张算法 Taste 卡** · **覆盖 9/13 个感知主方向** · 最近更新：**2026-08-04**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ 今日论文精读

### [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](notes/2026/2026-08-04-unipad.md)

**CVPR 2024**

> UniPAD 用掩码体积渲染把相机与 LiDAR 编码器预训练到统一三维空间；低数据增益显著，但相机预训练仍依赖 LiDAR 深度，固定源码采样含 RGB-only 回退且证据只覆盖 nuScenes。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://openaccess.thecvf.com/content/CVPR2024/html/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.html) · **数据中心学习与基础预训练** · Surround Camera + LiDAR · Self-Supervised Learning · Pre-training · Differentiable Rendering · Volumetric Representation · Depth-Aware Sampling · 3D Object Detection · 3D Semantic Segmentation · Multi-Modal Learning · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.pdf) · [官方代码 @ 3d24add1](https://github.com/Nightmare-n/UniPAD/tree/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52)
<!-- AUTO:LATEST:END -->

<!-- AUTO:TASTE:START -->
## 🧩 今日算法 Taste

### [Depth-Aware Ray Sampling](taste/2026/2026-08-04-depth-aware-ray-sampling.md)

> 在固定昂贵预算下优先采样可同时获得观测与稀缺几何真值的位置，并保留探索配额约束辅助传感器选择偏差。

**来自：** [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2024/html/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.html) · **Geometry-Guided Supervision Sampling**

**可迁移到：** Camera Self-Supervised Pre-training · BEV Feature Learning · Multi-Modal Representation Learning · Neural Rendering

**先记边界：** LiDAR 稀疏、失配或存在系统性盲区时会欠采样关键语义；模块证据只有 nuScenes 单次小幅消融。

[看原理图、接口合同、适用场景与反证实验 →](taste/2026/2026-08-04-depth-aware-ray-sampling.md) · [固定实现 @ 3d24add1](https://github.com/Nightmare-n/UniPAD/tree/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52)
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
- **2026-08-04 · CVPR 2024** — [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](notes/2026/2026-08-04-unipad.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-03 · ICCV 2023** — [Exploring Object-Centric Temporal Modeling for Efficient Multi-View 3D Object Detection](notes/2026/2026-08-03-streampetr.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-02 · ECCV 2022** — [V2X-ViT: Vehicle-to-Everything Cooperative Perception with Vision Transformer](notes/2026/2026-08-02-v2x-vit.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
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
