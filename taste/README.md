# 算法 Taste：可迁移设计卡

[返回首页](../README.md) · [全部论文精读](../index/papers.md) · [13 类主题路线](../index/topics.md)

> 这里每天只收一项真正值得迁移的设计：它可以是网络模块、主干网络、表示方式、训练单元或系统结构，但必须有明确瓶颈、可描述的接口、公开证据和失败边界。它不是又一份论文清单，也不把整篇论文包装成“即插即用”。

共 **2** 张设计卡；最近更新：**2026-08-02**。

## 怎么读一张卡

1. 先判断它解决的瓶颈是否也存在于你的任务；
2. 再检查输入、输出、shape、坐标系、梯度和算力接口；
3. 最后看消融能支持到哪一层，并设计一个能推翻迁移假设的最小实验。

## 全部设计卡

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
