# 自动驾驶感知 SOTA 与指标雷达

> **快照日期：2026-08-06。** 当前收录 19 个协议卡，其中 8 个来自官方动态榜单。这里的 SOTA 只表示列明协议内的可比较前沿，不是把不同传感器、数据划分、外部数据或指标混成总排名。

[返回首页](../README.md) · [查看机器索引](../index/sota.csv) · [查看方法与日更规则](../docs/research-radar-methodology.md)

## 先学会读这张雷达

- **官方榜单快照：** 榜单在快照日公开的提交结果；它不自动证明论文已正式录用，也不表示本仓库独立复现。
- **论文自报前沿：** 数字来自正式论文中的指定对照；跨论文配置不同，不能直接接在官方榜单后声称更强。
- **协议锚点：** 用来理解当前常用数据集与指标，不冒充全任务第一。
- **无单一总榜：** 该方向同时含多种任务或评测轴；强行给一个冠军会误导，因此保留评价菜单和代表性入口。
- **指标不是什么：** NDS、mAP、mIoU、PQ、AMOTA 或时延各自只回答一部分问题；离线分数更高不等于每类都改善，更不等于闭环安全。

## 13 个主方向

### P01 · 目标与交通参与者感知

#### RoPETR · Camera-only 3D object detection

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2025

**严格协议：** nuScenes Detection · nuScenes v1.0 · test · Surround Camera · camera only; no external data; no HD map; official test server

**主指标：** NDS（越高越好）= **70.8641 %**

**同时报告：** mAP=64.7840%

**第一次看这个指标：** NDS 把检测 mAP 与位置、尺度、方向、速度和属性误差合成一分；总分上涨不等于每个类别和误差项都改善。

**核验：** Official detection JSON was filtered on 2026-08-05 for camera-only submissions without external data or map use.

**边界：** Dynamic leaderboard submission; arXiv identity is not an acceptance decision and this repository did not reproduce the score.

**入口：** [论文](https://arxiv.org/abs/2504.12643) · [官方榜单](https://nuscenes.org/object-detection)

#### SEGT-TTA · LiDAR-only 3D object detection

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2024

**严格协议：** nuScenes Detection · nuScenes v1.0 · test · LiDAR · LiDAR only; no external data; no HD map; official test server

**主指标：** NDS（越高越好）= **74.5338 %**

**同时报告：** mAP=71.2400%

**第一次看这个指标：** NDS 把检测 mAP 与位置、尺度、方向、速度和属性误差合成一分；总分上涨不等于每个类别和误差项都改善。

**核验：** Official detection JSON was filtered on 2026-08-05 for LiDAR-only submissions without external data or map use.

**边界：** Test-time augmentation and compute are part of this submitted protocol; do not compare it with camera-only or real-time rows.

**入口：** [论文](https://arxiv.org/abs/2412.09658) · [官方榜单](https://nuscenes.org/object-detection)

#### NEMOT · Multi-object tracking

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2025

**严格协议：** nuScenes Tracking · nuScenes v1.0 · test · Surround Camera + LiDAR · camera plus LiDAR; no external data; no HD map; official test server

**主指标：** AMOTA（越高越好）= **77.9020 %**

**同时报告：** AMOTP=0.4361 m

**第一次看这个指标：** AMOTA 汇总多个召回水平下的跟踪表现；它不单独说明身份切换、每类稳定性或安全后果。

**核验：** Official tracking JSON was filtered on 2026-08-05 for camera-plus-LiDAR submissions without external data or map use.

**边界：** AMOTA aggregates recall thresholds; it does not show per-class identity stability or closed-loop safety and the score was not reproduced here.

**入口：** [论文](https://arxiv.org/abs/2506.18124) · [官方榜单](https://nuscenes.org/tracking)

### P02 · 稠密场景语义与几何

#### IAL · 3D panoptic segmentation

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2025

**严格协议：** nuScenes Panoptic · nuScenes v1.0 · test · LiDAR · LiDAR only; no external data; official panoptic test server

**主指标：** PQ（越高越好）= **82.0343 %**

**第一次看这个指标：** PQ 同时受实例识别与分割质量影响；一个总分不能告诉你错误主要来自漏检还是轮廓不准。

**核验：** Official panoptic JSON was filtered on 2026-08-05 for LiDAR-only submissions without external data.

**边界：** PQ combines segmentation quality and recognition quality; it is not pixel or point accuracy and this repository did not reproduce it.

**入口：** [论文](https://arxiv.org/abs/2505.18956) · [官方榜单](https://nuscenes.org/panoptic)

#### Point Transformer V3 · LiDAR semantic segmentation

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2023

**严格协议：** nuScenes-lidarseg · nuScenes v1.0 · test · LiDAR · LiDAR only; no external data; official lidarseg test server

**主指标：** mIoU（越高越好）= **82.9871 %**

**第一次看这个指标：** mIoU 先算每一类预测区域与真值区域的交并比再做类别平均，不等于所有点或体素的总体正确率。

**核验：** Official lidarseg JSON was filtered on 2026-08-05 for LiDAR-only submissions without external data.

**边界：** mIoU averages classes rather than all points; the leaderboard row does not establish robustness to weather or sensor degradation.

**入口：** [论文](https://arxiv.org/abs/2312.10035) · [官方榜单](https://nuscenes.org/lidar-segmentation)

### P03 · BEV 与统一场景表示

#### BEVFormer as a representation anchor · Unified BEV representation across detection and map tasks

**证据身份：** 无单一总榜 · Accepted · ECCV 2022 · 2022

**严格协议：** nuScenes multi-task protocols · nuScenes v1.0 · val/test · Surround Camera + Vehicle State · task-specific heads; detector and map protocols differ; backbone and temporal settings must be matched

**主指标：** task-specific NDS / mAP / mIoU（不适用单一方向）= **不设单一排名值**

**第一次看这个指标：** 这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。

**核验：** Official ECCV paper anchors a widely used spatiotemporal BEV representation; current methods evaluate different downstream heads and data regimes.

**边界：** 无单一可比 SOTA：BEV is a representation family rather than one task; detection NDS and map mAP cannot be merged into one ranking.

**入口：** [论文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136690001.pdf) · [正式录用](https://www.ecva.net/papers/eccv_2022/papers_ECCV/html/694_ECCV_2022_paper.php) · [代码](https://github.com/fundamentalvision/BEVFormer)

### P04 · Occupancy 与 4D 场景理解

#### OccMamba · Semantic occupancy prediction

**证据身份：** 论文自报前沿 · Accepted · CVPR 2025 · 2025

**严格协议：** OpenOccupancy · OpenOccupancy protocol · validation · Surround Camera + LiDAR · paper Table protocol against Co-Occ; exact backbone and supervision must remain matched

**主指标：** mIoU gain over Co-Occ（越高越好）= **4.3 points**

**同时报告：** IoU gain over Co-Occ=5.1 points

**第一次看这个指标：** mIoU 先算每一类预测区域与真值区域的交并比再做类别平均，不等于所有点或体素的总体正确率。

**核验：** Official CVF abstract reports the controlled OpenOccupancy gain and claims leading results on three occupancy benchmarks.

**边界：** This is a paper-reported delta rather than a live official leaderboard lead; it cannot be compared with Occ3D camera-only mIoU.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Li_OccMamba_Semantic_Occupancy_Prediction_with_State_Space_Models_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Li_OccMamba_Semantic_Occupancy_Prediction_with_State_Space_Models_CVPR_2025_paper.html) · [代码](https://github.com/USTCLH/OccMamba)

### P05 · 时序与预测性感知

#### 4DFormer · 4D panoptic tracking

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2023

**严格协议：** nuScenes Panoptic · nuScenes v1.0 · test · LiDAR · LiDAR only; no external data; official panoptic tracking test server

**主指标：** PAT（越高越好）= **79.4143 %**

**同时报告：** PQ=77.9897%;TQ=80.8920%

**第一次看这个指标：** PAT 同时看全景分割与跨帧关联；它的总分不能替代逐类 PQ、跟踪质量或错误传播分析。

**核验：** Official panoptic JSON was queried on 2026-08-05 and the PAT row was preserved with its PQ and TQ components.

**边界：** PAT combines segmentation and temporal association; it does not reveal each class or error type and was not reproduced here.

**入口：** [论文](https://arxiv.org/abs/2311.01520) · [官方榜单](https://nuscenes.org/panoptic)

#### CASPFormer · Motion prediction

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2024

**严格协议：** nuScenes Prediction · nuScenes v1.0 · test · Map + Vehicle State · official prediction test server; submitted model protocol; metric definitions follow nuScenes

**主指标：** MinADE_5（越低越好）= **1.1479 m**

**同时报告：** MissRateTopK_2_5=0.4783;OffRoadRate=0.0108

**第一次看这个指标：** MinADE 从多条候选轨迹中取最接近真值的一条；它不保证概率校准，也不保证与其他交通参与者交互合理。

**核验：** Official prediction JSON was queried on 2026-08-05 and the displayed companion metrics were preserved.

**边界：** Minimum ADE can reward one good hypothesis among several; it does not by itself establish calibrated probabilities or interactive safety.

**入口：** [论文](https://arxiv.org/abs/2409.17790) · [官方榜单](https://nuscenes.org/prediction)

### P06 · 传感器与多模态融合

#### SparseLIF-e · Camera-LiDAR 3D object detection

**证据身份：** 官方榜单快照 · LeaderboardSubmission · nuScenes leaderboard · 2024

**严格协议：** nuScenes Detection · nuScenes v1.0 · test · Surround Camera + LiDAR · camera plus LiDAR; no external data; no HD map; official test server

**主指标：** NDS（越高越好）= **77.6901 %**

**同时报告：** mAP=75.9384%

**第一次看这个指标：** NDS 把检测 mAP 与位置、尺度、方向、速度和属性误差合成一分；总分上涨不等于每个类别和误差项都改善。

**核验：** Official detection JSON was filtered on 2026-08-05 for camera-plus-LiDAR submissions without external data or map use.

**边界：** This is a dynamic leaderboard submission and not a latency-matched comparison; sensor availability and fusion compute are part of the protocol.

**入口：** [论文](https://arxiv.org/abs/2403.07284) · [官方榜单](https://nuscenes.org/object-detection)

#### RaCFormer · Radar-camera 3D object detection

**证据身份：** 论文自报前沿 · Accepted · CVPR 2025 · 2025

**严格协议：** nuScenes Detection · nuScenes v1.0 · test · Surround Camera + Radar · radar plus camera; paper test protocol; compare only with matched radar-camera inputs

**主指标：** NDS（越高越好）= **70.2 %**

**同时报告：** mAP=64.9%

**第一次看这个指标：** NDS 把检测 mAP 与位置、尺度、方向、速度和属性误差合成一分；总分上涨不等于每个类别和误差项都改善。

**核验：** Official CVF abstract reports 64.9 mAP and 70.2 NDS on nuScenes and identifies the comparison as radar-camera fusion.

**边界：** Paper-reported radar-camera frontier; it is not comparable to camera-LiDAR or LiDAR-only leaderboard rows and was not reproduced here.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Chu_RaCFormer_Towards_High-Quality_3D_Object_Detection_via_Query-based_Radar-Camera_Fusion_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Chu_RaCFormer_Towards_High-Quality_3D_Object_Detection_via_Query-based_Radar-Camera_Fusion_CVPR_2025_paper.html)

### P07 · 道路结构、HD Map 与定位

#### InteractionMap as a recent map anchor · Online vectorized HD map construction

**证据身份：** 无单一总榜 · Accepted · CVPR 2025 · 2025

**严格协议：** nuScenes and Argoverse 2 map protocols · current public versions · validation · Surround Camera + Map · dataset-specific vector classes and Chamfer/topology thresholds; backbone and training schedule must match

**主指标：** map mAP / topology metrics（不适用单一方向）= **不设单一排名值**

**第一次看这个指标：** 这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。

**核验：** Official CVF paper reports leading nuScenes and Argoverse 2 results under its stated configurations.

**边界：** 无单一可比 SOTA：map classes and matching thresholds differ; Chamfer mAP does not establish topology correctness or localization reliability.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wu_InteractionMap_Improving_Online_Vectorized_HDMap_Construction_with_Interaction_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Wu_InteractionMap_Improving_Online_Vectorized_HDMap_Construction_with_Interaction_CVPR_2025_paper.html)

### P08 · 协同感知

#### RCP-Bench as a robustness anchor · Camera-based collaborative perception under corruption

**证据身份：** 无单一总榜 · Accepted · CVPR 2025 · 2025

**严格协议：** RCP-Bench · RCP-Bench public protocol · test · Surround Camera + V2X · corruption type and severity; bandwidth; pose error; latency; matched collaborative backbone

**主指标：** AP under corruption / RCE / bandwidth（不适用单一方向）= **不设单一排名值**

**第一次看这个指标：** 这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。

**核验：** Official CVF paper supplies a multi-axis benchmark rather than one universally dominant method.

**边界：** 无单一可比 SOTA：communication cost and clean/corrupted AP form a Pareto surface; one AP number hides bandwidth and failure robustness.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Du_RCP-Bench_Benchmarking_Robustness_for_Collaborative_Perception_Under_Diverse_Corruptions_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Du_RCP-Bench_Benchmarking_Robustness_for_Collaborative_Perception_Under_Diverse_Corruptions_CVPR_2025_paper.html)

### P09 · 鲁棒、开放世界与可信感知

#### CLIP head alignment with corruption augmentation · Corruption robustness of camera BEV 3D detection

**证据身份：** 协议锚点 · Accepted · IEEE TPAMI 2025 · 2025

**严格协议：** RoboBEV / nuScenes-C · nuScenes validation-derived eight-corruption protocol · validation · Surround Camera · BEVDet task framework; CLIP image backbone; head alignment; corruption augmentation; eight corruption types and three severities; self-normalized mRR

**主指标：** mRR（越高越好）= **84.32 %**

**同时报告：** clean NDS 0.3667

**第一次看这个指标：** 该数字只回答列明协议中的一个问题，不能脱离数据、输入和评测设置外推为闭环安全。

**核验：** Table 10 paper-reported value verified 2026-08-06; fixed repository does not expose the CLIP training recipe or checkpoint.

**边界：** Benchmark corruption was used for training so 84.32 is a paper-protocol anchor not evidence of unseen-corruption SOTA; mRR is not absolute reliability or closed-loop safety.

**入口：** [论文](https://arxiv.org/pdf/2405.17426) · [正式录用](https://ieeexplore.ieee.org/document/10857618) · [代码](https://github.com/worldbench/RoboBEV/tree/3a32edaba9434dc27791bd25a1168951d091bd89)

#### MoME as a sensor-failure anchor · Sensor-failure robust LiDAR-camera detection

**证据身份：** 无单一总榜 · Accepted · CVPR 2025 · 2025

**严格协议：** nuScenes-R · nuScenes-R public protocol · validation · Surround Camera + LiDAR · failure scenario and severity must match; clean and corrupted performance reported separately

**主指标：** scenario-wise NDS / mAP degradation（不适用单一方向）= **不设单一排名值**

**第一次看这个指标：** 这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。

**核验：** Official CVF abstract identifies state-of-the-art nuScenes-R results across several failure scenarios.

**边界：** 无单一可比 SOTA：weather corruption sensor dropout open-set calibration and uncertainty are different protocols; robustness gain is not a safety guarantee.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Park_Resilient_Sensor_Fusion_Under_Adverse_Sensor_Failures_via_Multi-Modal_Expert_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Park_Resilient_Sensor_Fusion_Under_Adverse_Sensor_Failures_via_Multi-Modal_Expert_CVPR_2025_paper.html)

### P10 · 数据中心学习与基础预训练

#### VisionPAD · Vision-centric autonomous-driving pre-training

**证据身份：** 协议锚点 · Accepted · CVPR 2025 · 2025

**严格协议：** nuScenes 3D Detection · nuScenes v1.0 · validation · Surround Camera + LiDAR · UVTR downstream detector; camera-plus-LiDAR pre-training; CBGS and training schedule as reported

**主指标：** NDS（越高越好）= **50.4 %**

**同时报告：** mAP=43.1%

**第一次看这个指标：** NDS 把检测 mAP 与位置、尺度、方向、速度和属性误差合成一分；总分上涨不等于每个类别和误差项都改善。

**核验：** Official CVF Table 1 reports this UVTR transfer configuration and its no-pretraining baselines.

**边界：** This is a downstream pre-training anchor rather than the current overall nuScenes detection SOTA; architecture and pre-training modality are part of the protocol.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhang_VisionPAD_A_Vision-Centric_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_VisionPAD_A_Vision-Centric_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2025_paper.html)

### P11 · 大视觉模型、VLM、LLM 与 VLA

#### OmniDrive as a perception-reasoning anchor · Driving scene understanding and counterfactual VQA

**证据身份：** 无单一总榜 · Accepted · CVPR 2025 · 2025

**严格协议：** OmniDrive benchmark · OmniDrive public release · test · Surround Camera + Language · question type; answer scoring; visual encoder; language model and prompt protocol must match

**主指标：** VQA / grounding / planning metrics（不适用单一方向）= **不设单一排名值**

**第一次看这个指标：** 这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。

**核验：** Official CVF paper introduces a multi-task dataset and evaluates perception reasoning and counterfactual questions.

**边界：** 无单一可比 SOTA：free-form answer quality grounding accuracy and trajectory metrics are not interchangeable; fluent language can mask visual errors.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Wang_OmniDrive_A_Holistic_Vision-Language_Dataset_for_Autonomous_Driving_with_Counterfactual_CVPR_2025_paper.html)

### P12 · 世界模型与生成式 3D/4D 建模

#### UniScene as a unified generation anchor · Occupancy-conditioned video and LiDAR generation

**证据身份：** 无单一总榜 · Accepted · CVPR 2025 · 2025

**严格协议：** UniScene public protocol · nuScenes-derived training/evaluation · test · Surround Camera + LiDAR + Simulation · generated modality; conditioning; horizon; resolution; perceptual and geometric metrics must match

**主指标：** FID / FVD / geometry and downstream utility（不适用单一方向）= **不设单一排名值**

**第一次看这个指标：** 这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。

**核验：** Official CVF paper evaluates semantic occupancy video and LiDAR generation in one framework.

**边界：** 无单一可比 SOTA：visual realism geometric consistency controllability and downstream utility are separate axes; lower FID is not physical correctness.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Li_UniScene_Unified_Occupancy-centric_Driving_Scene_Generation_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Li_UniScene_Unified_Occupancy-centric_Driving_Scene_Generation_CVPR_2025_paper.html)

### P13 · 数据生成、仿真、评测与部署

#### EfficientOCF · Vision-based occupancy forecasting efficiency

**证据身份：** 协议锚点 · Accepted · CVPR 2025 · 2025

**严格协议：** nuScenes occupancy forecasting · paper protocol · test · Surround Camera · single-GPU latency with the paper implementation; horizon and occupancy resolution fixed

**主指标：** single-GPU latency（越低越好）= **82.33 ms**

**同时报告：** C-IoU introduced for forecasting consistency

**第一次看这个指标：** 时延只在指定硬件、软件、精度和输入规模下成立；它不是跨设备不变的模型属性。

**核验：** Official CVF abstract reports 82.33 ms latency on one GPU alongside paper-claimed leading forecasting results.

**边界：** Hardware software precision horizon and resolution determine latency; 82.33 ms is not a device-independent deployment guarantee.

**入口：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Xu_Spatiotemporal_Decoupling_for_Efficient_Vision-Based_Occupancy_Forecasting_CVPR_2025_paper.pdf) · [正式录用](https://openaccess.thecvf.com/content/CVPR2025/html/Xu_Spatiotemporal_Decoupling_for_Efficient_Vision-Based_Occupancy_Forecasting_CVPR_2025_paper.html)

## 日更原则

每天先刷新可机器读取的官方榜单，再核对近期正式论文。若协议、榜单或论文身份无法从官方入口确认，只保留旧快照并标注受阻，不用聚合站数字覆盖官方证据。每次更新与当日精读、Taste 共用分支、PR 和公开验收。
