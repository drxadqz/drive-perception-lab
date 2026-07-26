# 全部论文精读

[返回首页](../README.md) · [主题路线](topics.md) · [开放问题](open_questions.md)

> 本页由 `index/papers.csv` 自动生成。请不要手工编辑；运行
> `python scripts/rebuild_index.py` 更新。

共 **4** 篇，其中 **4** 篇已由权威来源核验为正式录用。
每篇按“图 → 公式 → 结果 → 源码 → 结论”组织；“代码已审”不等于“结果已复现”。

## 2026-07-27 · [BEVFormer: Learning Bird’s-Eye-View Representation from Multi-Camera Images via Spatiotemporal Transformers](../notes/2026/2026-07-27-bevformer.md)

`ECCV 2022` · `正式录用` · **BEV 与统一场景表示** · Surround Camera + Vehicle State · Bird's-Eye View · 3D Object Detection · Map Segmentation · Spatial Cross-Attention · Temporal Memory · Deformable Attention · Multi-Task Perception · Camera Calibration

> BEVFormer 用标定约束的空间交叉注意力和递归历史 BEV 把六路相机变成统一时空 BEV；但固定公开提交只闭环检测、未发布地图分割，且时序状态与标定误差的长序列耦合未验证。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-07-27-bevformer.md) · [论文原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136690001.pdf) · [固定版本源码](https://github.com/fundamentalvision/BEVFormer/tree/66b65f3a1f58caf0507cb2a971b9c0e7f842376c)

## 2026-07-26 · [VoxelNeXt: Fully Sparse VoxelNet for 3D Object Detection and Tracking](../notes/2026/2026-07-26-voxelnext.md)

`CVPR 2023` · `正式录用` · **目标与交通参与者感知** · LiDAR · 3D Object Detection · 3D Multi-Object Tracking · Sparse Convolution · Voxel Representation · Efficient Inference · Post-processing

> VoxelNeXt 证明非中心稀疏体素也能直接回归三维框并改善速度—精度折中；但官方默认配置仍使用 NMS、未启用剪枝，跟踪关联代码也未发布。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-07-26-voxelnext.md) · [论文原文](https://openaccess.thecvf.com/content/CVPR2023/papers/Chen_VoxelNeXt_Fully_Sparse_VoxelNet_for_3D_Object_Detection_and_Tracking_CVPR_2023_paper.pdf) · [固定版本源码](https://github.com/JIA-Lab-research/VoxelNeXt/tree/b5b7d393cd1d0ecbbaeaca365b453b488791035d)

## 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md)

`CVPR 2025` · `正式录用` · **大视觉模型、VLM、LLM 与 VLA** · Surround Camera + Language + Map + Vehicle State · VLM · LLM · 3D Grounding · Counterfactual Reasoning · Planning Interface · Open-loop Evaluation · Data Generation

> OmniDrive 用轨迹反事实把 3D 场景、语言推理和规划监督连起来；但更好的开放环指标仍可能来自 ego-status 捷径，且反事实没有模拟其他交通参与者的响应。

论文与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-07-25-omnidrive.md) · [论文原文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [固定版本源码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

## 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md)

`ICCV 2025` · `正式录用` · **Occupancy 与 4D 场景理解** · Surround Camera · 3D Occupancy · Temporal Memory · Streaming Perception · Occupancy Flow · Uncertainty

> ST-Occ 用场景坐标中的持久 3D 记忆提升 Occupancy 精度与时间一致性，但证据仍局限于单一数据域，且源码中的状态更新比论文示意更复杂。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-07-24-st-occ.md) · [论文原文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [固定版本源码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

## 状态解释

- **正式录用**：已通过 proceedings、OpenReview decision 或出版社页面核验；
- **预印本**：尚无权威录用来源，不能据此称为顶会论文；
- **代码已审**：阅读了固定 commit 的关键实现；
- **Checkpoint not run**：论文数字尚未被本仓库独立验证。
