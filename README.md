# DrivePerceptionLab

> **自动驾驶感知论文精读与可迁移算法设计卡。** 每天产出两份可以真正学懂、可以回查
> 证据的研究资产：一篇自动驾驶感知深度精读，
> 一张跨领域可迁移的算法 Taste 设计卡。精读系统覆盖 13 个感知主方向；设计卡只收
> 有明确瓶颈、接口、受控证据和失败边界的模块、主干网络或训练单元。

[▶ 今天的论文精读](#-今日论文精读) · [🧩 今天的算法 Taste](#-今日算法-taste) ·
[🗺 13 类学习路线](index/topics.md) · [📚 全部精读](index/papers.md) ·
[💡 全部设计卡](taste/README.md)

<!-- AUTO:STATS:START -->
**5 篇精读** · **5 篇正式录用** · **5 篇关键源码已审** · **1 张算法 Taste 卡** · **覆盖 5/13 个感知主方向** · 最近更新：**2026-07-29**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ 今日论文精读

### [SurroundDepth: Entangling Surrounding Views for Self-Supervised Multi-Camera Depth Estimation](notes/2026/2026-07-28-surrounddepth.md)

**CoRL 2022**

> SurroundDepth 用跨视图注意力、SfM 尺度预训练和统一位姿把六路图像变成米制深度；但固定源码缺论文所述视角编码，多视图一致性无理论保证，结果也未覆盖标定漂移。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://proceedings.mlr.press/v205/wei23a.html) · **稠密场景语义与几何** · Surround Camera · Multi-Camera Depth Estimation · Self-Supervised Learning · Cross-View Transformer · Structure-from-Motion · Scale-Aware Depth · Camera Calibration · Ego-Motion · Multi-View Consistency · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://proceedings.mlr.press/v205/wei23a/wei23a.pdf) · [官方代码 @ 22dfecfe](https://github.com/weiyithu/SurroundDepth/tree/22dfecfe8fca62a38d0f682ff7bf65b41aba3cac)
<!-- AUTO:LATEST:END -->

<!-- AUTO:TASTE:START -->
## 🧩 今日算法 Taste

### [Multi-Scale Deformable Attention](taste/2026/2026-07-29-multi-scale-deformable-attention.md)

> 把每个 query 的算力集中到参考点附近少量可学习采样位置，在多尺度特征上以稀疏取证替代全图扫描。

**来自：** [Deformable DETR: Deformable Transformers for End-to-End Object Detection](https://arxiv.org/pdf/2010.04159) · [正式录用](https://openreview.net/forum?id=gZ9hCDWe6ke) · **Sparse Attention**

**可迁移到：** BEV Query · Temporal Memory · Multi-Modal Fusion · Sparse 3D Query

**先记边界：** 它依赖有意义的参考点、坐标归一化和定制采样算子；训练更快不等于推理更快，也不能保证不漏掉参考点之外的证据。

[看原理图、接口合同、适用场景与反证实验 →](taste/2026/2026-07-29-multi-scale-deformable-attention.md) · [固定实现 @ 11169a60](https://github.com/fundamentalvision/Deformable-DETR/tree/11169a60c33333af00a4849f1808023eba96a931)
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
- **2026-07-28 · CoRL 2022** — [SurroundDepth: Entangling Surrounding Views for Self-Supervised Multi-Camera Depth Estimation](notes/2026/2026-07-28-surrounddepth.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-07-27 · ECCV 2022** — [BEVFormer: Learning Bird’s-Eye-View Representation from Multi-Camera Images via Spatiotemporal Transformers](notes/2026/2026-07-27-bevformer.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-07-26 · CVPR 2023** — [VoxelNeXt: Fully Sparse VoxelNet for 3D Object Detection and Tracking](notes/2026/2026-07-26-voxelnext.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
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
