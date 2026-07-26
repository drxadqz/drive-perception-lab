# 自动驾驶感知全方向论文精读

> 每天完成一篇高质量精读，系统覆盖自动驾驶感知的全部主方向，并纳入
> VFM、VLM、LLM、VLA、世界模型与感知的真实交叉。每篇都把原文图、
> 标准公式、关键实验和固定版本源码放在同一条学习路径里。每篇先解释首次
> 出现的专业术语并完整翻译摘要，再进入五段教学路线；公开的实验配置与流程、
> 结论、局限和展望都保留原文位置并作专业中文翻译。方法部分以
> “backbone 与基线 → 原瓶颈 → 完整信息流 → 逐模块设计动机、训练信号、
> 消融证据和固定源码”为主线，不只罗列网络名。
>
> 块级公式采用紧裁的 2× 深浅色 PNG，行内变量保持标准数学排版，并保留
> 纯文字读法与可复制 TeX 源；兼容 GitHub 网页和 iPad/iPhone App。

<!-- AUTO:STATS:START -->
**4 篇精读** · **4 篇正式录用** · **4 篇关键源码已审** · **覆盖 4/13 个感知主方向** · 最近更新：**2026-07-27**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ [开始今天的精读：BEVFormer: Learning Bird’s-Eye-View Representation from Multi-Camera Images via Spatiotemporal Transformers（ECCV 2022）](notes/2026/2026-07-27-bevformer.md)

> BEVFormer 用标定约束的空间交叉注意力和递归历史 BEV 把六路相机变成统一时空 BEV；但固定公开提交只闭环检测、未发布地图分割，且时序状态与标定误差的长序列耦合未验证。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://www.ecva.net/papers/eccv_2022/papers_ECCV/html/694_ECCV_2022_paper.php) · **BEV 与统一场景表示** · Surround Camera + Vehicle State · Bird's-Eye View · 3D Object Detection · Map Segmentation · Spatial Cross-Attention · Temporal Memory · Deformable Attention · Multi-Task Perception · Camera Calibration · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136690001.pdf) · [官方代码 @ 66b65f3a](https://github.com/fundamentalvision/BEVFormer/tree/66b65f3a1f58caf0507cb2a971b9c0e7f842376c)
<!-- AUTO:LATEST:END -->

## 想读其他内容

- [查看全部精读](index/papers.md)：按日期打开每一篇完整笔记；
- [按 13 个感知主方向学习](index/topics.md)：先看每个方向的一句话简介，再查看完整分类、当前覆盖缺口、
  大模型交叉索引和输入模态索引；
- [查看研究缺口](index/open_questions.md)：跨论文累计、仍待验证的问题。

## 最近完成

<!-- AUTO:RECENT:START -->
- **2026-07-27 · ECCV 2022** — [BEVFormer: Learning Bird’s-Eye-View Representation from Multi-Camera Images via Spatiotemporal Transformers](notes/2026/2026-07-27-bevformer.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-07-26 · CVPR 2023** — [VoxelNeXt: Fully Sparse VoxelNet for 3D Object Detection and Tracking](notes/2026/2026-07-26-voxelnext.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-07-25 · CVPR 2025** — [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](notes/2026/2026-07-25-omnidrive.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
<!-- AUTO:RECENT:END -->

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
