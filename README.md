# DrivePerceptionLab

> **自动驾驶感知论文精读与可迁移算法设计卡。** 每天产出两份可以真正学懂、可以回查
> 证据的研究资产：一篇自动驾驶感知深度精读，
> 一张跨领域可迁移的算法 Taste 设计卡。精读系统覆盖 13 个感知主方向；设计卡只收
> 有明确瓶颈、接口、受控证据和失败边界的模块、主干网络或训练单元。

[▶ 今天的论文精读](#-今日论文精读) · [🧩 今天的算法 Taste](#-今日算法-taste) ·
[🗺 13 类学习路线](index/topics.md) · [📚 全部精读](index/papers.md) ·
[💡 全部设计卡](taste/README.md)

<!-- AUTO:STATS:START -->
**10 篇精读** · **10 篇正式录用** · **10 篇关键源码已审** · **5 张算法 Taste 卡** · **覆盖 10/13 个感知主方向** · 最近更新：**2026-08-05**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ 今日论文精读

### [TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers](notes/2026/2026-08-05-transfusion.md)

**CVPR 2022**

> TransFusion 先保留 LiDAR 初始检测，再用局部软注意力增量融合图像；合成丢图与平移下退化较慢，但固定源码冻结两端骨干、checkpoint 不公开且分数合成不同于论文文字。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://openaccess.thecvf.com/content/CVPR2022/html/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.html) · **传感器与多模态融合** · Surround Camera + LiDAR · LiDAR-Camera Fusion · 3D Object Detection · Soft Association · Transformer Decoder · Object Query · Sensor Misalignment · Missing Camera · Multi-Modal Robustness · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) · [官方代码 @ 73c596f7](https://github.com/XuyangBai/TransFusion/tree/73c596f7bd3460c17cbcc58dd9bcc5a0896774a8)
<!-- AUTO:LATEST:END -->

<!-- AUTO:TASTE:START -->
## 🧩 今日算法 Taste

### [Image-Guided Query Initialization](taste/2026/2026-08-05-image-guided-query-initialization.md)

> 让辅助模态只预测同坐标候选热力图并以 stop-gradient 参与 top-K，主 query 内容仍来自可靠模态，便于隔离错误与回滚。

**来自：** [TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2022/html/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.html) · **Cross-Modal Proposal Prior**

**可迁移到：** Sparse-BEV Query Detection · Radar-Camera Fusion · Cooperative BEV · Open-World Proposal Recall

**先记边界：** 等权 prior 依赖固定视图和分数标度；Table 7 只有 0.8-1.6 mAP 边际且时延明显增加，未验证真实缺模态或跨 rig。

[看原理图、接口合同、适用场景与反证实验 →](taste/2026/2026-08-05-image-guided-query-initialization.md) · [固定实现 @ 73c596f7](https://github.com/XuyangBai/TransFusion/tree/73c596f7bd3460c17cbcc58dd9bcc5a0896774a8)
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
- **2026-08-05 · CVPR 2022** — [TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers](notes/2026/2026-08-05-transfusion.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-04 · CVPR 2024** — [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](notes/2026/2026-08-04-unipad.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-03 · ICCV 2023** — [Exploring Object-Centric Temporal Modeling for Efficient Multi-View 3D Object Detection](notes/2026/2026-08-03-streampetr.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
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
