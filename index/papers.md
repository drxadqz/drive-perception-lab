# 全部论文精读

[返回首页](../README.md) · [主题路线](topics.md) · [开放问题](open_questions.md)

> 本页由 `index/papers.csv` 自动生成。请不要手工编辑；运行
> `python scripts/rebuild_index.py` 更新。

共 **15** 篇，其中 **15** 篇已由权威来源核验为正式录用。
每篇按“图 → 公式 → 结果 → 源码 → 结论”组织；“代码已审”不等于“结果已复现”。

## 2026-08-14 · [UniDrive: Towards Universal Driving Perception Across Camera Configurations](../notes/2026/2026-08-14-unidrive.md)

`ICLR 2025` · `正式录用` · **BEV 与统一场景表示** · Surround Camera + Simulation · Camera Configuration · Virtual Camera · 3D Object Detection · BEV · Geometric Projection · Camera Calibration · Cross-Rig Generalization · CARLA Benchmark

> 虚拟相机预处理显著收窄模拟跨 rig 检测退化；但真实数据、效率、统计重复及核心投影/CMA-ES 官方实现均缺。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-14-unidrive.md) · [论文原文](https://proceedings.iclr.cc/paper_files/paper/2025/file/41badd36e935f8a80175e95d8bc6192e-Paper-Conference.pdf) · [固定版本源码](https://github.com/ywyeli/UniDrive/tree/c73f887d792fbab27d8275e85839e959b4c24f3c)

## 2026-08-13 · [GaussianFormer-2: Probabilistic Gaussian Superposition for Efficient 3D Occupancy Prediction](../notes/2026/2026-08-13-gaussianformer-2.md)

`CVPR 2025` · `正式录用` · **Occupancy 与 4D 场景理解** · Surround Camera + Monocular Camera · 3D Semantic Occupancy · 3D Gaussian Representation · Probabilistic Modeling · Sparse Representation · Gaussian Mixture · Distribution-Based Initialization · Efficient Inference · Camera Calibration

> 概率并集与归一化语义混合让稀疏高斯读出有界且显著提分；但独立性、概率校准、初始化配方与时序稳定仍未验证。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-13-gaussianformer-2.md) · [论文原文](https://openaccess.thecvf.com/content/CVPR2025/papers/Huang_GaussianFormer-2_Probabilistic_Gaussian_Superposition_for_Efficient_3D_Occupancy_Prediction_CVPR_2025_paper.pdf) · [固定版本源码](https://github.com/huang-yh/GaussianFormer/tree/b7e22bfc04cd6360cdee74be5af7fdace102f0a3)

## 2026-08-08 · [SplatAD: Real-Time Lidar and Camera Rendering with 3D Gaussian Splatting for Autonomous Driving](../notes/2026/2026-08-08-splatad.md)

`CVPR 2025` · `正式录用` · **数据生成、仿真、评测与部署** · Surround Camera + LiDAR + Simulation + Vehicle State · Neural Sensor Simulation · 3D Gaussian Splatting · Camera Rendering · LiDAR Rendering · Novel View Synthesis · Rolling Shutter · Dynamic Scene Modeling · Efficient Rendering

> SplatAD 以传感器专用 3DGS 联合渲染相机与 LiDAR；中位距离显著改善点云，但仅验证 30 段日志，源码依赖未完全固定且未证明下游安全。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-08-splatad.md) · [论文原文](https://openaccess.thecvf.com/content/CVPR2025/papers/Hess_SplatAD_Real-Time_Lidar_and_Camera_Rendering_with_3D_Gaussian_Splatting_CVPR_2025_paper.pdf) · [固定版本源码](https://github.com/georghess/neurad-studio/tree/c24765e3c37164db187119a224f3b9b83914f4bb)

## 2026-08-07 · [Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability](../notes/2026/2026-08-07-vista.md)

`NeurIPS 2024` · `正式录用` · **世界模型与生成式 3D/4D 建模** · Monocular Camera + Vehicle State · World Model · Video Diffusion · Future Prediction · Action Conditioning · Autoregressive Rollout · Uncertainty · Reward Modeling · Foundation Model

> Vista 以三帧 latent 替换和统一动作适配生成高保真未来；FID/FVD 强，但训练读真值历史、推理读生成历史，方差奖励也未获闭环安全校准。

论文、附录与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-07-vista.md) · [论文原文](https://proceedings.neurips.cc/paper_files/paper/2024/file/a6a066fb44f2fe0d36cf740c873b8890-Paper-Conference.pdf) · [固定版本源码](https://github.com/OpenDriveLab/Vista/tree/cc9821b4253ca7987c32757613d2fc2448fa9f5d)

## 2026-08-06 · [Benchmarking and Improving Bird’s Eye View Perception Robustness in Autonomous Driving](../notes/2026/2026-08-06-robobev.md)

`IEEE TPAMI 2025` · `正式录用` · **鲁棒、开放世界与可信感知** · Surround Camera + LiDAR · BEV · Out-of-Distribution Robustness · Natural Corruptions · Sensor Failure · 3D Object Detection · Map Segmentation · Depth Estimation · Semantic Occupancy

> RoboBEV 用四任务腐蚀/失效协议和 mCE/mRR 分离绝对性能与保持率；两阶段 CLIP head alignment 有受控增益，但真实联合退化、训练配方与校准告警仍缺。

论文、作者版 PDF 与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-06-robobev.md) · [论文原文](https://arxiv.org/pdf/2405.17426) · [固定版本源码](https://github.com/worldbench/RoboBEV/tree/3a32edaba9434dc27791bd25a1168951d091bd89)

## 2026-08-05 · [TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers](../notes/2026/2026-08-05-transfusion.md)

`CVPR 2022` · `正式录用` · **传感器与多模态融合** · Surround Camera + LiDAR · LiDAR-Camera Fusion · 3D Object Detection · Soft Association · Transformer Decoder · Object Query · Sensor Misalignment · Missing Camera · Multi-Modal Robustness

> TransFusion 先保留 LiDAR 初始检测，再用局部软注意力增量融合图像；合成丢图与平移下退化较慢，但固定源码冻结两端骨干、checkpoint 不公开且分数合成不同于论文文字。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-05-transfusion.md) · [论文原文](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) · [固定版本源码](https://github.com/XuyangBai/TransFusion/tree/73c596f7bd3460c17cbcc58dd9bcc5a0896774a8)

## 2026-08-04 · [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](../notes/2026/2026-08-04-unipad.md)

`CVPR 2024` · `正式录用` · **数据中心学习与基础预训练** · Surround Camera + LiDAR · Self-Supervised Learning · Pre-training · Differentiable Rendering · Volumetric Representation · Depth-Aware Sampling · 3D Object Detection · 3D Semantic Segmentation · Multi-Modal Learning

> UniPAD 用掩码体积渲染把相机与 LiDAR 编码器预训练到统一三维空间；低数据增益显著，但相机预训练仍依赖 LiDAR 深度，固定源码采样含 RGB-only 回退且证据只覆盖 nuScenes。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-04-unipad.md) · [论文原文](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.pdf) · [固定版本源码](https://github.com/Nightmare-n/UniPAD/tree/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52)

## 2026-08-03 · [Exploring Object-Centric Temporal Modeling for Efficient Multi-View 3D Object Detection](../notes/2026/2026-08-03-streampetr.md)

`ICCV 2023` · `正式录用` · **时序与预测性感知** · Surround Camera + Vehicle State · Temporal Modeling · Streaming Perception · 3D Object Detection · Object Query · Memory Queue · Motion-Aware Normalization · Transformer · 3D Tracking

> StreamPETR 把 top-K 对象查询作为跨帧隐状态并用运动条件归一化后进入混合注意力；但记忆写回完全 detach，论文主结果配置与默认流式训练配方不同，远距假阳性仍明显。

论文与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-03-streampetr.md) · [论文原文](https://openaccess.thecvf.com/content/ICCV2023/papers/Wang_Exploring_Object-Centric_Temporal_Modeling_for_Efficient_Multi-View_3D_Object_Detection_ICCV_2023_paper.pdf) · [固定版本源码](https://github.com/exiawsh/StreamPETR/tree/95f64702306ccdb7a78889578b2a55b5deb35b2a)

## 2026-08-02 · [V2X-ViT: Vehicle-to-Everything Cooperative Perception with Vision Transformer](../notes/2026/2026-08-02-v2x-vit.md)

`ECCV 2022` · `正式录用` · **协同感知** · LiDAR + V2X + Vehicle State · Cooperative Perception · Feature-level Fusion · Heterogeneous Attention · Pose Error · Communication Latency · Transformer · Simulation · 3D Object Detection

> V2X-ViT 用时空校正、类型化跨节点注意力和多尺度空间注意力融合车路特征；但主证据仅来自仿真，固定源码的 ego、噪声与压缩行为和论文并不完全一致。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-08-02-v2x-vit.md) · [论文原文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136990106.pdf) · [固定版本源码](https://github.com/DerrickXuNu/v2x-vit/tree/f0e6c13f41e916548b2d8aba61e42a18ce980416)

## 2026-07-29 · [MapTR: Structured Modeling and Learning for Online Vectorized HD Map Construction](../notes/2026/2026-07-29-maptr.md)

`ICLR 2023` · `正式录用` · **道路结构、HD Map 与定位** · Surround Camera + Vehicle State · Online HD Map · Vectorized Map · Bird's-Eye View · Transformer · Hierarchical Matching · Permutation Equivariance · Camera Calibration · Efficient Inference

> MapTR 以排列等价目标和两级匹配并行输出矢量地图，固定顺序消融提升 5.9 mAP；但默认源码未枚举论文定义的反向多边形顺序，且评测不覆盖拓扑。

论文、附录与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-07-29-maptr.md) · [论文原文](https://openreview.net/pdf?id=k7p_YAO7yE) · [固定版本源码](https://github.com/hustvl/MapTR/tree/a6872d8d9670bde17b4b01560f1221f88b443d55)

## 2026-07-28 · [SurroundDepth: Entangling Surrounding Views for Self-Supervised Multi-Camera Depth Estimation](../notes/2026/2026-07-28-surrounddepth.md)

`CoRL 2022` · `正式录用` · **稠密场景语义与几何** · Surround Camera · Multi-Camera Depth Estimation · Self-Supervised Learning · Cross-View Transformer · Structure-from-Motion · Scale-Aware Depth · Camera Calibration · Ego-Motion · Multi-View Consistency

> SurroundDepth 用跨视图注意力、SfM 尺度预训练和统一位姿把六路图像变成米制深度；但固定源码缺论文所述视角编码，多视图一致性无理论保证，结果也未覆盖标定漂移。

论文、补充材料与官方源码已审；官方源码已核到固定 commit；**Checkpoint 未运行**

[▶ 开始精读](../notes/2026/2026-07-28-surrounddepth.md) · [论文原文](https://proceedings.mlr.press/v205/wei23a/wei23a.pdf) · [固定版本源码](https://github.com/weiyithu/SurroundDepth/tree/22dfecfe8fca62a38d0f682ff7bf65b41aba3cac)

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
