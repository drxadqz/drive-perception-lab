# 自动驾驶感知方向与覆盖

[返回首页](../README.md) · [全部论文](papers.md) · [开放问题](open_questions.md)

本页由 `index/taxonomy.json` 与 `index/papers.csv` 联合生成。前者定义稳定的
感知分类，后者保存论文记录；每天只新增一条论文记录，覆盖表、分类列表、
大模型交叉索引和模态索引会一起更新。

分类遵循“一篇论文一个主方向，多种正交标签”的原则。BEV、时序、Camera、
鲁棒性和 VLM 可以同时出现在同一篇论文中，但主方向只由论文真正解决的主要
问题和核心指标决定，避免同一篇论文在主目录里重复多次。

## 如何使用

1. 先看覆盖总表，找到已有锚点或尚未覆盖的方向；
2. 从主方向进入一篇精读，再用模态和细标签做横向比较；
3. 大模型论文单独有交叉入口，但纯规划、纯控制或只有语言包装而没有感知
   贡献的论文不计入核心感知覆盖；
4. 阅读实验边界与源码审计，记录强 baseline 和缺失对照；
5. 只有同一问题获得多篇独立论文支持，才加入
   [开放问题](open_questions.md)。

“尚未被本仓库收录”不等于“学界尚未解决”，正式选题仍需要单独的新颖性
检索和碰撞审查。

<!-- AUTO:TOPICS:START -->
## 全方向覆盖总表

> 这里列出完整分类，而不是只显示已经读过的热门方向。“0 篇”表示本仓库尚未覆盖，不代表学界没有相关工作。

| 编号 | 自动驾驶感知主方向 | 已精读 | 最近更新 | 覆盖状态 |
|---|---|---:|---|---|
| P01 | [目标与交通参与者感知](#p01-object-actor-perception) | 0 | — | 待覆盖 |
| P02 | [稠密场景语义与几何](#p02-dense-scene-geometry) | 0 | — | 待覆盖 |
| P03 | [BEV 与统一场景表示](#p03-bev-unified-representation) | 0 | — | 待覆盖 |
| P04 | [Occupancy 与 4D 场景理解](#p04-occupancy-4d) | 1 | 2026-07-24 | 已有锚点 |
| P05 | [时序与预测性感知](#p05-temporal-predictive-perception) | 0 | — | 待覆盖 |
| P06 | [传感器与多模态融合](#p06-sensors-multimodal-fusion) | 0 | — | 待覆盖 |
| P07 | [道路结构、HD Map 与定位](#p07-road-map-localization) | 0 | — | 待覆盖 |
| P08 | [协同感知](#p08-cooperative-perception) | 0 | — | 待覆盖 |
| P09 | [鲁棒、开放世界与可信感知](#p09-robust-open-trustworthy) | 0 | — | 待覆盖 |
| P10 | [数据中心学习与基础预训练](#p10-data-learning-foundation) | 0 | — | 待覆盖 |
| P11 | [大视觉模型、VLM、LLM 与 VLA](#p11-vfm-vlm-llm-vla) | 1 | 2026-07-25 | 已有锚点 |
| P12 | [世界模型与生成式 3D/4D 建模](#p12-world-models-generative-4d) | 0 | — | 待覆盖 |
| P13 | [数据生成、仿真、评测与部署](#p13-data-generation-evaluation-deployment) | 0 | — | 待覆盖 |

## 按 13 个主方向精读

每篇论文只有一个主方向，避免在目录中重复；传感器、任务、表示、可靠性和大模型关系通过后面的交叉索引补充。

<a id="p01-object-actor-perception"></a>
### P01 · 目标与交通参与者感知（0）

**范围：** 2D/3D 检测、属性与姿态、多目标跟踪、全景跟踪，以及以离散目标、实例或轨迹为核心的感知。

**阅读时追问：** 模型能否稳定发现、定位并持续识别真正影响驾驶决策的交通参与者？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p02-dense-scene-geometry"></a>
### P02 · 稠密场景语义与几何（0）

**范围：** 语义、实例与全景分割，深度、立体、光流、场景流、自由空间、路面、路缘和静态三维重建。

**阅读时追问：** 像素、点、表面和流场是否足够准确地描述可通行空间与细粒度几何？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p03-bev-unified-representation"></a>
### P03 · BEV 与统一场景表示（0）

**范围：** 相机、LiDAR 或雷达到 BEV 的视角变换，稀疏查询、统一多任务 BEV，以及向量或图式场景表示。

**阅读时追问：** 统一表示保留了哪些三维信息，又在哪里因压缩、遮挡或坐标变换而失真？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p04-occupancy-4d"></a>
### P04 · Occupancy 与 4D 场景理解（1）

**范围：** 几何或语义 Occupancy、场景补全、实例 Occupancy、Occupancy Flow、时序 Occupancy 与未来 4D Occupancy。

**阅读时追问：** 体素或场表示能否同时覆盖可见、遮挡和动态区域，并在时间上保持可信？

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

<a id="p05-temporal-predictive-perception"></a>
### P05 · 时序与预测性感知（0）

**范围：** 多帧融合、流式记忆、4D 检测、检测—跟踪—预测联合建模、运动估计和未来环境状态预测。

**阅读时追问：** 历史信息何时真正改善当前与未来感知，何时会积累陈旧或错误状态？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p06-sensors-multimodal-fusion"></a>
### P06 · 传感器与多模态融合（0）

**范围：** Camera、LiDAR、Radar、Event、Thermal 等传感器建模，跨模态对齐、标定、异步融合与缺失模态。

**阅读时追问：** 不同传感器的信息是否互补，并能否在标定误差、时延和故障下安全退化？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p07-road-map-localization"></a>
### P07 · 道路结构、HD Map 与定位（0）

**范围：** 车道、道路边界、交通灯与标志、拓扑关系、在线矢量地图、地图更新、定位、里程计与 SLAM。

**阅读时追问：** 系统能否从实时观测恢复可行驶拓扑，并识别地图过期或定位漂移？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p08-cooperative-perception"></a>
### P08 · 协同感知（0）

**范围：** V2V、V2I、V2X 的原始、特征或目标级共享，协同 BEV、Occupancy 与地图，以及时延、带宽和异构性。

**阅读时追问：** 额外视角在通信受限、不同步甚至不可信时，是否仍带来可验证的感知增益？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p09-robust-open-trustworthy"></a>
### P09 · 鲁棒、开放世界与可信感知（0）

**范围：** 恶劣天气、自然扰动、传感器故障、域偏移、OOD、开放集或开放词汇、长尾、不确定性、校准与失效诊断。

**阅读时追问：** 模型能否知道自己何时可能错，并在未知、退化和长尾场景中给出可用风险信号？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p10-data-learning-foundation"></a>
### P10 · 数据中心学习与基础预训练（0）

**范围：** 自监督、半监督、弱监督、预训练、跨模态蒸馏、自动标注、主动学习、持续或联邦学习与数据筛选。

**阅读时追问：** 怎样利用未标注、多域和长尾数据获得真正可迁移的驾驶表征，而不是只扩大训练集？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p11-vfm-vlm-llm-vla"></a>
### P11 · 大视觉模型、VLM、LLM 与 VLA（1）

**范围：** VFM 驱动感知、开放词汇 Grounding、驾驶 VQA 与场景推理、LLM 教师或数据引擎，以及有明确感知贡献的 VLA 接口。

**阅读时追问：** 语言与基础模型是否真正增强三维视觉理解，还是只在感知错误之上生成流畅解释？

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

<a id="p12-world-models-generative-4d"></a>
### P12 · 世界模型与生成式 3D/4D 建模（0）

**范围：** Image、Video、BEV、Occupancy 或 LiDAR 世界模型，动作条件动力学、多步未来、反事实与闭环 Rollout。

**阅读时追问：** 生成的未来是否在几何、物理和行为上可用于预测与决策，而不只是视觉逼真？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

<a id="p13-data-generation-evaluation-deployment"></a>
### P13 · 数据生成、仿真、评测与部署（0）

**范围：** 合成数据、NeRF/3DGS 传感器仿真、场景生成与挖掘、Benchmark、指标协议、闭环测试、实时部署和安全验证。

**阅读时追问：** 数据、指标、仿真与系统约束是否测到了真实能力，并能否复现和部署？

- 尚无完成精读；每日选文会优先检查这一覆盖缺口。

## 与大模型结合的感知论文

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

## 按输入模态浏览

### Monocular Camera（0）

- 尚无完成精读。

### Stereo Camera（0）

- 尚无完成精读。

### Surround Camera（2）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)
- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Occupancy 与 4D 场景理解 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### LiDAR（0）

- 尚无完成精读。

### Radar（0）

- 尚无完成精读。

### Event Camera（0）

- 尚无完成精读。

### Thermal（0）

- 尚无完成精读。

### GNSS/IMU（0）

- 尚无完成精读。

### V2X（0）

- 尚无完成精读。

### Language（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### Map（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### Simulation（0）

- 尚无完成精读。

### Vehicle State（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

<details>
<summary><strong>展开细任务与方法标签</strong></summary>

### 3D Grounding（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### 3D Occupancy（1）

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Occupancy 与 4D 场景理解 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### Counterfactual Reasoning（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### Data Generation（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### LLM（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### Occupancy Flow（1）

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Occupancy 与 4D 场景理解 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### Open-loop Evaluation（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### Planning Interface（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

### Streaming Perception（1）

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Occupancy 与 4D 场景理解 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### Temporal Memory（1）

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Occupancy 与 4D 场景理解 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### Uncertainty（1）

- 2026-07-24 · [Occupancy Learning with Spatiotemporal Memory](../notes/2026/2026-07-24-st-occ.md) — ICCV 2025 · 正式录用 · Occupancy 与 4D 场景理解 · Surround Camera · [论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Leng_Occupancy_Learning_with_Spatiotemporal_Memory_ICCV_2025_paper.pdf) · [代码](https://github.com/matthew-leng/ST-Occ/tree/1633f62e2e6677a5fa474905977acfeca4e7819e)

### VLM（1）

- 2026-07-25 · [OmniDrive: A Holistic Vision-Language Dataset for Autonomous Driving with Counterfactual Reasoning](../notes/2026/2026-07-25-omnidrive.md) — CVPR 2025 · 正式录用 · 大视觉模型、VLM、LLM 与 VLA · Surround Camera + Language + Map + Vehicle State · [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [代码](https://github.com/NVlabs/OmniDrive/tree/ced207333cb18b69a232cbb9f82bf52089227f12)

</details>
<!-- AUTO:TOPICS:END -->
