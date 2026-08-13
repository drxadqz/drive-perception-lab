# 算法 Taste：可迁移设计卡

[返回首页](../README.md) · [全部论文精读](../index/papers.md) · [13 类主题路线](../index/topics.md)

> 这里每天只收一项真正值得迁移的设计：它可以是网络模块、主干网络、表示方式、训练单元或系统结构，但必须有明确瓶颈、可描述的接口、公开证据和失败边界。它不是又一份论文清单，也不把整篇论文包装成“即插即用”。

共 **10** 张设计卡；最近更新：**2026-08-14**。

## 怎么读一张卡

1. 先判断它解决的瓶颈是否也存在于你的任务；
2. 再检查输入、输出、shape、坐标系、梯度和算力接口；
3. 最后看消融能支持到哪一层，并设计一个能推翻迁移假设的最小实验。

## 全部设计卡

### 2026-08-14 · [Virtual Camera Canonicalization Preprocessor](2026/2026-08-14-virtual-camera-projection.md)

**Geometry-First Input Canonicalization** · 来自 [UniDrive: Towards Universal Driving Perception Across Camera Configurations](https://proceedings.iclr.cc/paper_files/paper/2025/file/41badd36e935f8a80175e95d8bc6192e-Paper-Conference.pdf) · ICLR 2025

> 已知几何 nuisance 时先统一输入合同再复用下游网络；迁移时必须显式携带覆盖 mask 并与 camera-aware conditioning 匹配比较。

**可迁移到：** Cross-Rig BEV · Map Perception · Multi-Camera Occupancy · Calibration-Robust Detection

**主要边界：** 代理表面、错误标定、缺 FOV、遮挡冲突和重采样开销会失效；原文没有核心投影实现或单组件消融。

### 2026-08-13 · [Probabilistic Union Geometry Readout](2026/2026-08-13-probabilistic-union-geometry-readout.md)

**Bounded Probabilistic Set Aggregation** · 来自 [GaussianFormer-2: Probabilistic Gaussian Superposition for Efficient 3D Occupancy Prediction](https://openaccess.thecvf.com/content/CVPR2025/papers/Huang_GaussianFormer-2_Probabilistic_Gaussian_Superposition_for_Efficient_3D_Occupancy_Prediction_CVPR_2025_paper.pdf) · CVPR 2025

> 多个局部原语表达同一存在事件时用有界并集聚合几何并独立归一化语义；先匹配预算测试校准和相关重复。

**可迁移到：** Sparse Occupancy · Gaussian Scene Completion · Multi-Sensor Existence Fusion · Map-Free Free-Space Estimation

**主要边界：** 局部值不似概率或原语高度相关时会过度自信并饱和梯度；完整读出消融不能把全部增益归给单一 noisy-OR。

### 2026-08-08 · [Alpha-Weighted Median LiDAR Range Readout](2026/2026-08-08-alpha-weighted-median-range.md)

**Occlusion-Aware Quantile Readout** · 来自 [SplatAD: Real-Time Lidar and Camera Rendering with 3D Gaussian Splatting for Autonomous Driving](https://openaccess.thecvf.com/content/CVPR2025/papers/Hess_SplatAD_Real-Time_Lidar_and_Camera_Rendering_with_3D_Gaussian_Splatting_CVPR_2025_paper.pdf) · CVPR 2025

> 累计遮挡过半即选择真实排序表面，避免期望距离把前后表面平均到空气中；先以纯读出 A/B 试验核验再改训练。

**可迁移到：** Neural Sensor Simulation · Occupancy Ray Rendering · Neural Surface Reconstruction · LiDAR World Models

**主要边界：** alpha 未校准、薄目标或累计 opacity 不过半时会选错或 fallback；证据仅是 30 段日志平均，未验证下游感知。

### 2026-08-07 · [Dynamic-Prior Latent Replacement](2026/2026-08-07-dynamic-prior-latent-replacement.md)

**History Injection in Latent Diffusion** · 来自 [Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability](https://proceedings.neurips.cc/paper_files/paper/2024/file/a6a066fb44f2fe0d36cf740c873b8890-Paper-Conference.pdf) · NeurIPS 2024

> 把少量历史状态写成不可再预测的干净槽位并只监督未来；迁移关键是明确 read/write/reset 与训练—推理历史身份。

**可迁移到：** Streaming BEV · Occupancy Forecasting · Video World Models · Temporal Query Memory

**主要边界：** 历史错位或 scene reset 泄漏会把错误硬写成事实；Table 3 只控制 prior 数量并未证明 replacement 优于 concat/attention。

### 2026-08-06 · [Two-Stage CLIP Detection-Head Alignment](2026/2026-08-06-two-stage-clip-head-alignment.md)

**Staged Foundation-Model Adaptation** · 来自 [Benchmarking and Improving Bird’s Eye View Perception Robustness in Autonomous Driving](https://arxiv.org/pdf/2405.17426) · IEEE TPAMI 2025

> 先冻结 CLIP 让随机检测头学会读取预训练表示，再解冻联合微调；迁移关键是分阶段钉死梯度所有权与匹配总训练预算。

**可迁移到：** Robust BEV Detection · Multi-Modal BEV · Open-World Perception · Domain-Shift Adaptation

**主要边界：** 固定源码未公开两阶段 trainer/checkpoint；若训练见过 benchmark corruption、backbone 缺三维几何或匹配预算后增益消失，该策略不成立。

### 2026-08-05 · [Image-Guided Query Initialization](2026/2026-08-05-image-guided-query-initialization.md)

**Cross-Modal Proposal Prior** · 来自 [TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) · CVPR 2022

> 让辅助模态只预测同坐标候选热力图并以 stop-gradient 参与 top-K，主 query 内容仍来自可靠模态，便于隔离错误与回滚。

**可迁移到：** Sparse-BEV Query Detection · Radar-Camera Fusion · Cooperative BEV · Open-World Proposal Recall

**主要边界：** 等权 prior 依赖固定视图和分数标度；Table 7 只有 0.8-1.6 mAP 边际且时延明显增加，未验证真实缺模态或跨 rig。

### 2026-08-04 · [Depth-Aware Ray Sampling](2026/2026-08-04-depth-aware-ray-sampling.md)

**Geometry-Guided Supervision Sampling** · 来自 [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.pdf) · CVPR 2024

> 在固定昂贵预算下优先采样可同时获得观测与稀缺几何真值的位置，并保留探索配额约束辅助传感器选择偏差。

**可迁移到：** Camera Self-Supervised Pre-training · BEV Feature Learning · Multi-Modal Representation Learning · Neural Rendering

**主要边界：** LiDAR 稀疏、失配或存在系统性盲区时会欠采样关键语义；模块证据只有 nuScenes 单次小幅消融。

### 2026-08-03 · [Motion-Aware Layer Normalization (MLN)](2026/2026-08-03-motion-aware-layer-normalization.md)

**Motion-Conditioned Normalization** · 来自 [Exploring Object-Centric Temporal Modeling for Efficient Multi-View 3D Object Detection](https://openaccess.thecvf.com/content/ICCV2023/papers/Wang_Exploring_Object-Centric_Temporal_Modeling_for_Efficient_Multi-View_3D_Object_Detection_ICCV_2023_paper.pdf) · ICCV 2023

> 先做无仿射层归一化，再由姿态、时间和速度生成恒等初始化的逐通道缩放与偏移，以软条件化代替脆弱的显式运动补偿。

**可迁移到：** Temporal BEV · Object Query Memory · Multi-Modal Tracking · Cooperative Perception

**主要边界：** 证据主要来自 ego pose；时间和速度仅额外贡献约 0.4 点，运动元数据噪声、陈旧记忆或非仿射变化都会让条件化失效。

### 2026-08-02 · [Heterogeneous Multi-Agent Self-Attention (HMSA)](2026/2026-08-02-hmsa.md)

**Type-Conditioned Relational Attention** · 来自 [V2X-ViT: Vehicle-to-Everything Cooperative Perception with Vision Transformer](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136990106.pdf) · ECCV 2022

> 让节点类型决定 Q/K/V、让有向边类型决定注意力与消息变换，在同坐标格内显式建模异构来源关系。

**可迁移到：** Multi-Sensor BEV · Cooperative Occupancy · Temporal Memory · Multi-Robot Fusion

**主要边界：** 它依赖可靠坐标对齐与正确类型，节点对计算随 M² 增长；二值角色无法表示同类传感器质量差异，也没有真实 V2X 证据。

### 2026-07-29 · [Multi-Scale Deformable Attention](2026/2026-07-29-multi-scale-deformable-attention.md)

**Sparse Attention** · 来自 [Deformable DETR: Deformable Transformers for End-to-End Object Detection](https://arxiv.org/pdf/2010.04159) · ICLR 2021

> 把每个 query 的算力集中到参考点附近少量可学习采样位置，在多尺度特征上以稀疏取证替代全图扫描。

**可迁移到：** BEV Query · Temporal Memory · Multi-Modal Fusion · Sparse 3D Query

**主要边界：** 它依赖有意义的参考点、坐标归一化和定制采样算子；训练更快不等于推理更快，也不能保证不漏掉参考点之外的证据。

## 收录边界

- 优先正式录用论文、作者官方代码和可定位的受控比较；
- 预印本必须显式标注，不用整模型主结果冒充单模块证据；
- “可迁移”表示接口和设计逻辑值得测试，不表示零改动即可提升；
- 未投稿方案、私有结果和可直接抢先实现的核心配方不进入公开卡片。
