# DrivePerceptionLab

> **自动驾驶感知论文精读与可迁移算法设计卡。** 每天产出两份可以真正学懂、可以回查
> 证据的研究资产：一篇自动驾驶感知深度精读，
> 一张跨领域可迁移的算法 Taste 设计卡。精读系统覆盖 13 个感知主方向；设计卡只收
> 有明确瓶颈、接口、受控证据和失败边界的模块、主干网络或训练单元。

[▶ 今天的论文精读](#-今日论文精读) · [🧩 今天的算法 Taste](#-今日算法-taste) ·
[🏁 SOTA 协议雷达](sota/README.md) · [🔭 跨领域迁移雷达](transfer/README.md) ·
[🗺 13 类学习路线](index/topics.md) · [📚 全部精读](index/papers.md) ·
[💡 全部设计卡](taste/README.md) · [🎯 为什么选它](docs/daily-selection-and-gap-audit.md)

<!-- AUTO:STATS:START -->
**14 篇精读** · **14 篇正式录用** · **14 篇关键源码已审** · **9 张算法 Taste 卡** · **覆盖 13/13 个感知主方向** · 最近更新：**2026-08-13**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ 今日论文精读

### [GaussianFormer-2: Probabilistic Gaussian Superposition for Efficient 3D Occupancy Prediction](notes/2026/2026-08-13-gaussianformer-2.md)

**CVPR 2025**

> 概率并集与归一化语义混合让稀疏高斯读出有界且显著提分；但独立性、概率校准、初始化配方与时序稳定仍未验证。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_GaussianFormer-2_Probabilistic_Gaussian_Superposition_for_Efficient_3D_Occupancy_Prediction_CVPR_2025_paper.html) · **Occupancy 与 4D 场景理解** · Surround Camera + Monocular Camera · 3D Semantic Occupancy · 3D Gaussian Representation · Probabilistic Modeling · Sparse Representation · Gaussian Mixture · Distribution-Based Initialization · Efficient Inference · Camera Calibration · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://openaccess.thecvf.com/content/CVPR2025/papers/Huang_GaussianFormer-2_Probabilistic_Gaussian_Superposition_for_Efficient_3D_Occupancy_Prediction_CVPR_2025_paper.pdf) · [官方代码 @ b7e22bfc](https://github.com/huang-yh/GaussianFormer/tree/b7e22bfc04cd6360cdee74be5af7fdace102f0a3)
<!-- AUTO:LATEST:END -->

<!-- AUTO:TASTE:START -->
## 🧩 今日算法 Taste

### [Probabilistic Union Geometry Readout](taste/2026/2026-08-13-probabilistic-union-geometry-readout.md)

> 多个局部原语表达同一存在事件时用有界并集聚合几何并独立归一化语义；先匹配预算测试校准和相关重复。

**来自：** [GaussianFormer-2: Probabilistic Gaussian Superposition for Efficient 3D Occupancy Prediction](https://openaccess.thecvf.com/content/CVPR2025/papers/Huang_GaussianFormer-2_Probabilistic_Gaussian_Superposition_for_Efficient_3D_Occupancy_Prediction_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_GaussianFormer-2_Probabilistic_Gaussian_Superposition_for_Efficient_3D_Occupancy_Prediction_CVPR_2025_paper.html) · **Bounded Probabilistic Set Aggregation**

**可迁移到：** Sparse Occupancy · Gaussian Scene Completion · Multi-Sensor Existence Fusion · Map-Free Free-Space Estimation

**先记边界：** 局部值不似概率或原语高度相关时会过度自信并饱和梯度；完整读出消融不能把全部增益归给单一 noisy-OR。

[看原理图、接口合同、适用场景与反证实验 →](taste/2026/2026-08-13-probabilistic-union-geometry-readout.md) · [固定实现 @ b7e22bfc](https://github.com/huang-yh/GaussianFormer/tree/b7e22bfc04cd6360cdee74be5af7fdace102f0a3)
<!-- AUTO:TASTE:END -->

## 三种读法

- **5 分钟判断值不值得深读：** 先看摘要后的“为什么今天值得读”、问题背景、
  前置论文路线、第一张方法图和证据边界；
- **30 分钟真正理解：** 沿“原图 → 公式画面 → 变量身份与变化 → 小数字例子
  → 结果与消融”读到数据集怎样分、实验怎样跑，以及证据支持什么、没有支持
  什么；公式中的“领域惯用”只表示概念角色常见，不表示所有论文强制用同一字母；
- **研究级核验：** 再进固定版本源码、论文—源码差异、复现账本与
  [相邻工作核查](docs/daily-selection-and-gap-audit.md#3-下一步是否已经做过的强制检索)。

想按问题系统学习，从[13 类学习路线](index/topics.md)进入；想寻找可迁移接口，
打开[算法 Taste](taste/README.md)；想继续追可证伪的问题，查看
[开放问题雷达](index/open_questions.md)。要核对当前指标量级与严格比较协议，查看
[SOTA 与指标雷达](sota/README.md)；要寻找其他计算机领域尚值得受控验证的窄迁移
接口，并同时看到已经发生的检索碰撞，查看[跨领域迁移雷达](transfer/README.md)。

## 每日怎么选

先看近 24 个月及当前/前两个会议年份的正式顶会内容，再看仍影响今天研究判断的
关键经典；同时综合 13 类覆盖、后续采用、受控证据、官方源码、作者/团队研究
脉络与可验证的创新空间。MIT 等顶尖团队会进入优先候选池，但机构名望、引用和
热度都不能替代方法质量。每篇新笔记公开同轮候选对照；每个准备突出显示的
“下一步”都先检索最接近已有工作，有限检索结论绝不写成“学界无人做过”。

[查看完整选文评分与缺口核查协议 →](docs/daily-selection-and-gap-audit.md)

## 最近完成

<!-- AUTO:RECENT:START -->
- **2026-08-13 · CVPR 2025** — [GaussianFormer-2: Probabilistic Gaussian Superposition for Efficient 3D Occupancy Prediction](notes/2026/2026-08-13-gaussianformer-2.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-08 · CVPR 2025** — [SplatAD: Real-Time Lidar and Camera Rendering with 3D Gaussian Splatting for Autonomous Driving](notes/2026/2026-08-08-splatad.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-07 · NeurIPS 2024** — [Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability](notes/2026/2026-08-07-vista.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
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
