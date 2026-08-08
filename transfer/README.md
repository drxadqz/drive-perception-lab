# 跨领域强算法迁移雷达

> **检索快照：2026-08-08。** 当前重点保留 3 个可做受控验证的窄迁移假设，并公开 6 个已覆盖或部分覆盖的碰撞项。“可迁移”只表示瓶颈和接口值得测试，不表示零改动必然提升，更不表示已达到自动驾驶 SOTA。

[返回首页](../README.md) · [查看机器索引](../index/transfer.csv) · [查看检索与评分方法](../docs/research-radar-methodology.md)

## 怎么读

每个候选先把主张拆成问题、机制、洞见与场景，再用问题词、机制词、同义/邻域词检索。最接近论文必须回到官方 proceedings、作者项目或 arXiv 原文；帖子、Awesome List 和榜单聚合页只用于召回。只有结论为“本次检索未找到直接覆盖”的候选可以高亮，而且 30 天内必须重查。

## 值得做受控验证

### EoMT encoder-only mask transformer → 相机三维语义 Occupancy

**检索结论：** [本次检索未找到直接覆盖] · Level 3 - medium overlap · 优先级 8.6/10 · 下次复核 2026-09-04

**30 秒画面：** 把传统分割系统想成“主干先看图，专用解码器再画区域”。EoMT 发现，足够强的 ViT 主干可以一边理解图像、一边更新区域查询，不一定需要后面那套复杂解码器。迁移问题是：把二维图块换成三维体素后，这种简化还能否保住行人、路杆等细小结构。

**源领域与证据：** 2D semantic and panoptic segmentation；官方 CVF 论文报告：纯 ViT 编码器达到相近的前沿分割精度，ViT-L 预测速度最高为对照的四倍。

**迁移接口：** 保留图像到三维表示的投影与最终 Occupancy head，只把专用三维解码器替换为共享编码器；体素或三平面 token 与 mask query 在编码器层内交替更新。

**适配假设：** [判断] 检验“移除专用 decoder + 联合更新 token/query”能否在降时延的同时保住细杆、行人和远处边界；这不是泛泛地把 mask query 搬到 3D。

**三路检索式：**

- 问题词：encoder-only mask transformer 3D occupancy autonomous driving
- 机制词：plain transformer segmentation queries BEV semantic occupancy
- 同义/邻域词：EoMT point cloud 3D segmentation

**检索来源：** CVF proceedings checked 2026-08-05 · arXiv checked 2026-08-05 · Semantic Scholar checked 2026-08-05 · Crossref checked 2026-08-05 · official GitHub checked 2026-08-05

**最接近工作：**

- [OccFormer](https://openaccess.thecvf.com/content/ICCV2023/html/Zhang_OccFormer_Dual-path_Transformer_for_Vision-based_3D_Semantic_Occupancy_Prediction_ICCV_2023_paper.html)
- [TPVFormer](https://openaccess.thecvf.com/content/CVPR2023/html/Huang_Tri-Perspective_View_for_Vision-Based_3D_Semantic_Occupancy_Prediction_CVPR_2023_paper.html)
- [COTR](https://openaccess.thecvf.com/content/CVPR2024/html/Ma_COTR_Compact_Occupancy_TRansformer_for_Vision-based_3D_Occupancy_Prediction_CVPR_2024_paper.html)

**最小接入实验：** 在同一个 Occ3D validation 配置中只替换 decoder，严格匹配 backbone、预训练、分辨率、训练步数和监督；三次随机种子同时报告 mIoU、细小类别 IoU、时延和峰值显存。

**回滚基线：** 使用相同 backbone checkpoint、保留原专用 decoder 的公开 Occupancy 基线。

**什么会推翻它：** 恢复原 decoder 后若精度—效率 Pareto 不劣，或新方法的细小类别 IoU 超过预设容差下降，就推翻该迁移假设。

**最大失效条件：** 三维 token 数量可能吃掉二维 EoMT 的速度优势；联合更新还可能过早合并细小或被遮挡结构。

**公开边界：** 截至日期，在列明范围内本次未找到直接覆盖：只指在共享编码器内联合更新 3D occupancy tokens 与 mask queries 并移除专用 decoder 的窄组合；已有 3D mask-query 与 occupancy Transformer 工作不属于空白。

**源论文与代码：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Kerssies_Your_ViT_is_Secretly_an_Image_Segmentation_Model_CVPR_2025_paper.pdf) · [正式入口](https://openaccess.thecvf.com/content/CVPR2025/html/Kerssies_Your_ViT_is_Secretly_an_Image_Segmentation_Model_CVPR_2025_paper.html) · [官方代码 @ 7bd19ddd](https://github.com/tue-mps/eomt/tree/7bd19ddd621c5c6adedcd260458a34783cd4a45f) · 许可证 MIT。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### D-FINE fine-grained distribution refinement → query 驱动的三维目标检测

**检索结论：** [本次检索未找到直接覆盖] · Level 3 - medium overlap · 优先级 8.3/10 · 下次复核 2026-09-04

**30 秒画面：** 普通检测头像一次报出“车中心在 12.4 米”。D-FINE 先保留多个位置区间的概率，再逐层把范围收紧。三维迁移最难的不是照搬 bins，而是让中心、尺寸、速度和首尾相接的偏航角一起细化而不互相矛盾。

**源领域与证据：** Real-time 2D object detection；官方 ICLR 论文报告 D-FINE-L/X 在 T4 上分别以 124/78 FPS 达到 54.0/55.8 COCO AP；Objects365 预训练后为 57.1/59.3 AP。

**迁移接口：** 保留 3D detector 的 backbone、matcher 与 query decoder，只把中心、尺寸、偏航角和速度的连续更新改为逐层概率分布细化；偏航角使用循环 bins 或圆周分布。

**适配假设：** [判断] 检验粗到细分布与跨 decoder 层定位自蒸馏能否改善难例定位，同时不破坏偏航角周期性和不确定性校准。

**三路检索式：**

- 问题词：D-FINE 3D object detection autonomous driving
- 机制词：fine-grained distribution refinement 3D bounding box detection
- 同义/邻域词：distribution refinement 3D object detection DETR

**检索来源：** OpenReview decision and paper checked 2026-08-05 · CVF proceedings checked 2026-08-05 · arXiv checked 2026-08-05 · Semantic Scholar checked 2026-08-05 · official GitHub checked 2026-08-05

**最接近工作：**

- [RACE-6D](https://openaccess.thecvf.com/content/CVPR2026F/html/Ha_RACE-6D_Real-time_Accurate_Coarse-to-finE_Object_6D_Pose_Transformer_CVPRF_2026_paper.html)
- [FocalFormer3D](https://openaccess.thecvf.com/content/ICCV2023/html/Chen_FocalFormer3D_Focusing_on_Hard_Instance_for_3D_Object_Detection_ICCV_2023_paper.html)
- [MonoDETR](https://openaccess.thecvf.com/content/ICCV2023/html/Zhang_MonoDETR_Depth-guided_Transformer_for_Monocular_3D_Object_Detection_ICCV_2023_paper.html)

**最小接入实验：** 在一个公开 nuScenes validation detector 上只改 box refinement head；分别消融中心、尺寸、偏航角和速度分布，三次种子报告 NDS、mAP、mAOE、mATE、校准、时延和显存。

**回滚基线：** 相同检测器、相同 loss 权重与训练预算下的原连续回归 head。

**什么会推翻它：** 匹配算力和 decoder 深度后增益消失，或 mAOE、校准、细小目标召回超过预设容差变差，即拒绝该适配。

**最大失效条件：** 三维参数彼此耦合，独立 bins 可能生成不一致 box；偏航角首尾相接，普通线性离散会制造假距离，稠密分布还会增大显存。

**公开边界：** 截至日期，在列明范围内本次未找到直接覆盖：只指把 D-FINE 式逐层分布细化与自蒸馏用于自动驾驶 3D center size yaw velocity；RACE-6D 已覆盖分布式深度细化，故不能声称把该机制迁到所有 3D 任务都是新方向。

**源论文与代码：** [论文](https://openreview.net/pdf?id=MFZjrTFE7h) · [正式入口](https://openreview.net/forum?id=MFZjrTFE7h) · [官方代码 @ 7fe2f888](https://github.com/Peterande/D-FINE/tree/7fe2f8889f0b7b817f20c315b40fc15a4fb64ae6) · 许可证 Apache-2.0。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### xLSTM matrix memory → 流式 BEV 或 object-query 感知记忆

**检索结论：** [本次检索未找到直接覆盖] · Level 3 - medium overlap · 优先级 8.0/10 · 下次复核 2026-09-04

**30 秒画面：** 流式感知像值班员把上一帧地图交给下一帧；一张旧 BEV 容易把多个目标和遮挡线索挤在同一份记忆里。xLSTM 的矩阵记忆可能保存更多关系，但必须先把每段场景的读取、写回、重置和梯度截断规则钉死，否则会串场。

**源领域与证据：** Sequence modeling；官方 NeurIPS 论文提出指数门控、标量记忆与矩阵记忆；mLSTM 训练时可并行，并在论文长序列协议中与 Transformer、状态空间模型形成有利比较。

**迁移接口：** 在 ego-motion 对齐后的 BEV 或 object queries 之后插入 mLSTM，作为真正影响预测的状态；空间 encoder 与 heads 不变，并明确每个 scene slot 的读、写、reset、detach。

**适配假设：** [判断] 检验矩阵记忆能否比单张 previous-BEV 同时保存更多运动与遮挡模式，而且不会引入 train/test 状态泄漏。

**三路检索式：**

- 问题词：xLSTM autonomous driving perception BEV occupancy tracking
- 机制词：extended LSTM 3D object detection autonomous driving
- 同义/邻域词：xLSTM temporal point cloud 3D perception

**检索来源：** NeurIPS proceedings checked 2026-08-05 · ICLR proceedings checked 2026-08-05 · arXiv checked 2026-08-05 · Semantic Scholar checked 2026-08-05 · Google Research publication page checked 2026-08-05

**最接近工作：**

- [Sparse LSTM temporal 3D detection](https://research.google/pubs/an-lstm-approach-to-temporal-3d-object-detection-in-lidar-point-clouds/)
- [X-TRACK](https://arxiv.org/abs/2511.00266)
- [Vision-LSTM](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3b6eaef68473fe46bc4197a6b4460042-Abstract-Conference.html)

**最小接入实验：** 只替换一个流式 nuScenes detector 的时序记忆；按相同状态字节数比较 previous-BEV、ConvGRU 与 mLSTM，三次种子并加入场景乱序、reset 和 corruption 检查。

**回滚基线：** 空间 encoder 完全相同、使用原 previous-BEV 或门控循环记忆的公开流式模型。

**什么会推翻它：** 匹配状态容量后 NDS、跟踪稳定性或遮挡恢复没有改善，或串场污染和时延超预算，就推翻假设。

**最大失效条件：** 矩阵状态可能昂贵或数值不稳；scene slot、reset 或 detach 规则稍有错误，就会把上一段场景悄悄带入下一段预测。

**公开边界：** 截至日期，在列明范围内本次未找到直接覆盖：只指带严格 read write reset detach 审计的 xLSTM matrix memory 用于流式 BEV 或 object-query 感知；传统 LSTM 3D 检测与 xLSTM 轨迹预测已经存在。

**源论文与代码：** [论文](https://proceedings.neurips.cc/paper_files/paper/2024/file/c2ce2f2701c10a2b2f2ea0bfa43cfaa3-Paper-Conference.pdf) · [正式入口](https://proceedings.neurips.cc/paper_files/paper/2024/hash/c2ce2f2701c10a2b2f2ea0bfa43cfaa3-Abstract-Conference.html) · [官方代码 @ f539ba80](https://github.com/NX-AI/xlstm/tree/f539ba80770ba2b9acd5bf4c1e0f0d4827494184) · 许可证 Apache-2.0。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

## 碰撞与已覆盖：为什么没有把它包装成机会

### Diffusion Forcing → 动作条件驾驶世界模型

**检索结论：** [已覆盖] · Level 1 - direct mechanism coverage · 优先级 3.5/10 · 下次复核 2026-09-04

**30 秒画面：** 它让序列中每个时间位置带不同噪声，连接逐步预测与整段去噪；Orbis 2 已把这一训练方式用于驾驶世界模型，所以该迁移已发生。

**源领域与证据：** Generative sequence modeling；官方 NeurIPS 论文让序列各 token 使用独立噪声等级，并在灵活时域生成、规划和决策协议中评估。

**迁移接口：** 对长时驾驶 rollout 的不同时间位置使用独立噪声计划，连接因果逐步预测与整段去噪。

**适配假设：** [判断] 公开驾驶世界模型 Orbis 2 已明确使用 Diffusion Forcing 预训练，所以该迁移不再是开放机会。

**三路检索式：**

- 问题词：Diffusion Forcing autonomous driving world model
- 机制词：per-token diffusion noise driving video rollout
- 同义/邻域词：full-sequence diffusion BEV occupancy forecasting

**检索来源：** NeurIPS proceedings checked 2026-08-05 · arXiv checked 2026-08-05 · official Orbis 2 project checked 2026-08-05 · CVF proceedings checked 2026-08-05

**最接近工作：**

- [Orbis 2](https://lmb-freiburg.github.io/orbis2.github.io/)
- [Diffusion Forcing source paper](https://proceedings.neurips.cc/paper_files/paper/2024/hash/2aee1c4159e48407d68fe16ae8e6e49e-Abstract-Conference.html)

**最小接入实验：** 把 Orbis 2 当作直接 prior，先复现它对 Diffusion Forcing 的受控贡献，再讨论不同机制。

**回滚基线：** 相同数据和算力下的自回归或标准视频扩散驾驶世界模型。

**什么会推翻它：** 新主张必须隔离出 Orbis 2 尚未包含的机制；只换 backbone 或数据集不能通过。

**最大失效条件：** 长 rollout 可以变得更好看，却仍在几何、动作一致性和稀有事件校准上错误。

**公开边界：** Orbis 2 publicly states Diffusion Forcing pre-training in a driving world model so this mechanism is recorded as covered rather than advertised as unused.

**源论文与代码：** [论文](https://proceedings.neurips.cc/paper_files/paper/2024/file/2aee1c4159e48407d68fe16ae8e6e49e-Paper-Conference.pdf) · [正式入口](https://proceedings.neurips.cc/paper_files/paper/2024/hash/2aee1c4159e48407d68fe16ae8e6e49e-Abstract-Conference.html) · [官方代码 @ 475e0bca](https://github.com/buoyancy99/diffusion-forcing/tree/475e0bcab87545e48b24b39fb46a81fe59d80594) · 许可证 MIT。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### FeatUp → 高分辨率 BEV 特征提升

**检索结论：** [已覆盖] · Level 1 - direct task coverage · 优先级 4.0/10 · 下次复核 2026-09-04

**30 秒画面：** 它想把基础模型的低分辨率特征放大得更细，但 JAFAR 已经在驾驶 BEV 分割里直接比较了 FeatUp。因此这不是未使用机会，只能作为已有对照。

**源领域与证据：** Foundation-feature upsampling；FeatUp 学习把低分辨率基础模型特征提升到更密的网格，并在其公开 dense-task 协议中报告收益。

**迁移接口：** 在视角提升或 BEV 融合之前细化基础视觉特征，同时保持基础 encoder 不变。

**适配假设：** [判断] 这个接口看似合适，但 JAFAR 已在自动驾驶 BEV 分割中直接评估 FeatUp，并提出更强的任务适配方案。

**三路检索式：**

- 问题词：foundation feature upsampling autonomous driving BEV
- 机制词：FeatUp BEV segmentation multi-view driving
- 同义/邻域词：high resolution DINO features bird eye view

**检索来源：** ICLR proceedings checked 2026-08-05 · OpenReview checked 2026-08-05 · official JAFAR project checked 2026-08-05 · CVF proceedings checked 2026-08-05

**最接近工作：**

- [JAFAR](https://valeoai.github.io/publications/jafar/)
- [MET3R](https://openaccess.thecvf.com/content/CVPR2025/html/Asim_MET3R_Measuring_Multi-View_Consistency_in_Generated_Images_CVPR_2025_paper.html)

**最小接入实验：** 提出任何新版本前，先复现 JAFAR 中低分辨率、FeatUp 与 JAFAR 的匹配 BEV 分割对照。

**回滚基线：** 不做学习式特征上采样的低分辨率公开 BEV backbone。

**什么会推翻它：** 若精确剩余差异不能在相同分辨率和算力下超过已发表的 FeatUp/JAFAR 对照，就不存在可保留机会。

**最大失效条件：** 特征看起来更锐利不等于公制几何更准，而且稠密高分辨率特征会显著增加显存。

**公开边界：** Direct BEV evaluation exists in JAFAR so FeatUp is retained only as a collision record and is not highlighted as an unused transfer.

**源论文与代码：** [论文](https://openreview.net/pdf?id=GkJiNn2QDF) · [正式入口](https://proceedings.iclr.cc/paper_files/paper/2024/hash/c5601d99ed028448f29d1dae2e4a926d-Abstract-Conference.html) · [官方代码 @ 6b5a6c0e](https://github.com/mhamilton723/FeatUp/tree/6b5a6c0e91f75e69194807128dcbc39c3084a30d) · 许可证 MIT。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### FLYP → BEV 感知中的 CLIP 鲁棒适配

**检索结论：** [已覆盖] · Level 1 - direct target coverage · 优先级 3.8/10 · 下次复核 2026-09-05

**30 秒画面：** FLYP 在下游继续使用图文对比目标，以减少普通分类微调造成的分布外遗忘；但 RoboBEV 已把 CLIP 鲁棒适配直接用于 BEV，两阶段 head alignment 也已有受控结果，所以 FLYP 是源领域对照，不是未被发现的迁移空白。

**源领域与证据：** Vision-language model robust fine-tuning；官方 CVPR 论文在其源协议中报告：七个分布偏移数据集平均比标准微调高 4.2% OOD，三个 few-shot benchmark 最高提高 4.6%；这些数字不证明 BEV 迁移。

**迁移接口：** 保留 CLIP 图文对比训练目标来适配图像 backbone 与 BEV 任务接口，并与直接端到端、先 head alignment 和 WiSE-FT 匹配比较。

**适配假设：** [判断] 宽泛迁移已被 RoboBEV 与通用鲁棒微调工作覆盖；FLYP 只用于检验保持预训练目标是否优于阶段性接口对齐。

**三路检索式：**

- 问题词：CLIP fine-tuning loses OOD robustness in BEV perception
- 机制词：contrastive fine-tuning frozen backbone head alignment robust adaptation
- 同义/邻域词：foundation vision encoder staged adaptation autonomous driving corruption

**检索来源：** CVF proceedings checked 2026-08-06 · OpenReview and arXiv checked 2026-08-06 · OpenAlex and Semantic Scholar style indexes checked 2026-08-06 · official RoboBEV FLYP and WiSE-FT repositories checked 2026-08-06

**最接近工作：**

- [RoboBEV](https://ieeexplore.ieee.org/document/10857618)
- [FLYP](https://openaccess.thecvf.com/content/CVPR2023/html/Goyal_Finetune_Like_You_Pretrain_Improved_Finetuning_of_Zero-Shot_Vision_Models_CVPR_2023_paper.html)
- [GRACE](https://openaccess.thecvf.com/content/CVPR2026/html/Chopra_The_Geometry_of_Robustness_Optimizing_Loss_Landscape_Curvature_and_Feature_CVPR_2026_paper.html)
- [WiSE-FT](https://openaccess.thecvf.com/content/CVPR2022/html/Wortsman_Robust_Fine-Tuning_of_Zero-Shot_Models_CVPR_2022_paper.html)

**最小接入实验：** 先复现 RoboBEV 的直接微调和 head-alignment 行，再固定 CLIP、数据、总步数和推理成本加入 FLYP；报告未见腐蚀 NDS、校准、长尾类和三次种子。

**回滚基线：** 同一 BEV detector 的原 backbone、直接 CLIP 端到端、RoboBEV 两阶段 head alignment 与 WiSE-FT。

**什么会推翻它：** 若 FLYP 不能在匹配条件下改善未见腐蚀的绝对 NDS、校准或长尾类，它只保留为负对照，不构成迁移机会。

**最大失效条件：** 类别文本提示未必编码公制三维几何；额外文本分支可能增加训练成本，却不改善 BEV 定位。

**公开边界：** RoboBEV already transfers robust CLIP adaptation to BEV and generic robust fine-tuning is mature; this record is a collision and rollback baseline not a highlighted opportunity.

**源论文与代码：** [论文](https://openaccess.thecvf.com/content/CVPR2023/papers/Goyal_Finetune_Like_You_Pretrain_Improved_Finetuning_of_Zero-Shot_Vision_Models_CVPR_2023_paper.pdf) · [正式入口](https://openaccess.thecvf.com/content/CVPR2023/html/Goyal_Finetune_Like_You_Pretrain_Improved_Finetuning_of_Zero-Shot_Vision_Models_CVPR_2023_paper.html) · [官方代码 @ 215d5bb6](https://github.com/locuslab/FLYP/tree/215d5bb6feeda6675f60e5818abcb4f6465c83af) · 许可证 MIT。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### Mip-Splatting → 联合相机—LiDAR 驾驶传感器仿真中的尺度感知相机渲染

**检索结论：** [已覆盖] · Level 1 - direct mechanism coverage · 优先级 3.4/10 · 下次复核 2026-09-07

**30 秒画面：** Mip-Splatting 用三维平滑与二维 Mip filter 抑制相机采样率改变时的混叠；SplatAD 已把其 EWA 形式直接写进联合驾驶传感器渲染器并做消融，所以这不是未迁移机会。

**源领域与证据：** Graphics and neural rendering；官方 CVPR 论文在单尺度训练、多尺度测试协议中验证三维平滑和二维 Mip filter；这些源任务结果不证明 LiDAR 或闭环安全。

**迁移接口：** 在相机 Gaussian footprint 中以尺度感知 filter 替换固定 screen-space dilation，同时把 LiDAR 的 beam sampling、range readout 和指标保持为单独 contract。

**适配假设：** [判断] 宽泛迁移已被直接覆盖：SplatAD Eq. (5) 明确继承 Mip-Splatting/EWA，Table 5 还比较 full 与 no-EWA。后续只能提出不同 filtering 或跨传感器耦合机制。

**三路检索式：**

- 问题词：driving Gaussian sensor simulation aliasing under camera distance and focal changes
- 机制词：Mip filter EWA Gaussian splatting autonomous driving renderer
- 同义/邻域词：scale-aware splatting novel-view driving simulation thin structures

**检索来源：** CVF proceedings checked 2026-08-08 · arXiv and Crossref/OpenAlex/Semantic Scholar style indexes checked 2026-08-08 · official Mip-Splatting and SplatAD repositories checked 2026-08-08 · ECVA and CVF urban Gaussian papers checked 2026-08-08

**最接近工作：**

- [Mip-Splatting](https://openaccess.thecvf.com/content/CVPR2024/html/Yu_Mip-Splatting_Alias-free_3D_Gaussian_Splatting_CVPR_2024_paper.html)
- [SplatAD](https://openaccess.thecvf.com/content/CVPR2025/html/Hess_SplatAD_Real-Time_Lidar_and_Camera_Rendering_with_3D_Gaussian_Splatting_for_Autonomous_Driving_CVPR_2025_paper.html)
- [DrivingGaussian](https://openaccess.thecvf.com/content/CVPR2024/html/Zhou_DrivingGaussian_Composite_Gaussian_Splatting_for_Surrounding_Dynamic_Autonomous_Driving_Scenes_CVPR_2024_paper.html)
- [Street Gaussians](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/09243.pdf)
- [VEGS](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/7159_ECCV_2024_paper.php)

**最小接入实验：** 先复现固定 SplatAD 配方的 Table 5 full/no-EWA，在同一 checkpoint 体系分层报告相机质量、LiDAR CD、薄结构与吞吐，再判断是否有窄差异。

**回滚基线：** 固定 SplatAD 的 no-EWA row，以及原始 3DGS screen-space dilation。

**什么会推翻它：** 若新主张只是把 Mip-Splatting 加到驾驶 renderer，或匹配条件后不能超越 SplatAD 已公开 EWA 对照，就判定没有剩余贡献。

**最大失效条件：** anti-aliasing 可改善图像 LPIPS，却不保证 LiDAR CD 同向；源仓许可证仅允许研究/非商业使用，部署前还需单独法律审查。

**公开边界：** SplatAD already transfers the Mip-Splatting EWA mechanism and publishes an ablation so this row is a direct collision and legal-risk reminder not a highlighted opportunity.

**源论文与代码：** [论文](https://openaccess.thecvf.com/content/CVPR2024/papers/Yu_Mip-Splatting_Alias-free_3D_Gaussian_Splatting_CVPR_2024_paper.pdf) · [正式入口](https://openaccess.thecvf.com/content/CVPR2024/html/Yu_Mip-Splatting_Alias-free_3D_Gaussian_Splatting_CVPR_2024_paper.html) · [官方代码 @ dda02ab5](https://github.com/autonomousvision/mip-splatting/tree/dda02ab5ecf45d6edb8c540d9bb65c7e451345a9) · 许可证 Inria research-only non-commercial。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### PiToMe → 高效点云与多视图三维感知

**检索结论：** [部分覆盖] · Level 2 - high overlap · 优先级 5.1/10 · 下次复核 2026-09-04

**30 秒画面：** 它把相似 token 合并来省算力，同时尽量保护孤立小区域；但点云 PiToMe 与驾驶多视图 token 压缩都已出现，剩余空间必须缩到几何、标定或运动约束，不能再泛称“把 PiToMe 迁到 3D”。

**源领域与证据：** Efficient Transformers and graph coarsening；官方论文在选定分类与视觉语言协议中节省 40–60% FLOPs，平均性能下降约 0.3–0.5 点，并给出谱保持分析。

**迁移接口：** 合并冗余空间 token，同时尽量保护孤立小区域和原 token 图的谱结构。

**适配假设：** [判断] 宽泛迁移已经被点云 PiToMe 与驾驶 token 压缩覆盖；只可能保留带几何、标定或运动约束的窄变体，而且要重新查碰撞。

**三路检索式：**

- 问题词：PiToMe point cloud autonomous driving token merging
- 机制词：spectrum preserving token merging 3D perception
- 同义/邻域词：token merging multi-view 3D detector BEV

**检索来源：** NeurIPS proceedings checked 2026-08-05 · arXiv checked 2026-08-05 · Semantic Scholar checked 2026-08-05 · CVF and official project pages checked 2026-08-05

**最接近工作：**

- [GitMerge3D](https://arxiv.org/abs/2511.05449)
- [ToC3D](https://arxiv.org/abs/2409.00633)
- [PiToMe source paper](https://proceedings.neurips.cc/paper_files/paper/2024/hash/37094fdc81632915a5738293cf9b7ad4-Abstract-Conference.html)

**最小接入实验：** 先在同一公开 backbone 上复现 GitMerge3D 与 ToC3D 的 token 数—精度—真实时延曲线，再定义更窄差异。

**回滚基线：** 不压缩 backbone，以及已发表的 ToC3D 和通用 PiToMe 对照。

**什么会推翻它：** 几何感知差异若不能在相同 token 数、墙钟时延和小目标指标下超过已有 merging controls，就撤回剩余机会。

**最大失效条件：** 合并可能删掉稀有小目标或破坏跨视图几何；源码仓库还是非商业许可，使用前需单独做法律审查。

**公开边界：** Point-cloud PiToMe adaptation and driving token compression are already public; the radar therefore records only partial remaining scope and does not highlight it.

**源论文与代码：** [论文](https://arxiv.org/abs/2405.16148) · [正式入口](https://proceedings.neurips.cc/paper_files/paper/2024/hash/37094fdc81632915a5738293cf9b7ad4-Abstract-Conference.html) · [官方代码 @ 550b5dee](https://github.com/hchautran/PiToMe/tree/550b5deed94aadfeac28bfbe381d87e672044a40) · 许可证 CC-BY-NC-4.0 repository license。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

### TeaCache → 动作条件驾驶视频世界模型加速

**检索结论：** [部分覆盖] · Level 2 - high overlap · 优先级 5.4/10 · 下次复核 2026-09-06

**30 秒画面：** TeaCache 用时间步嵌入估计相邻去噪输出何时变化较小，再决定是否复用缓存；但通用视频世界模型缓存、驾驶世界模型加速和长时滚动纠错都已有公开工作，因此这里只保留动作切换与历史状态边界上的窄测试。

**源领域与证据：** Video diffusion inference systems；官方 CVPR 论文在 Open-Sora-Plan 源协议上报告最高 4.41 倍加速，VBench 仅下降 0.07%；这不证明驾驶动作一致性或长滚动状态不受损。

**迁移接口：** 在重复执行的 UNet 或 DiT 去噪 block 输出旁加入时间步嵌入感知缓存，同时保持 action condition、history latent 和 sampler schedule 其余部分不变。

**适配假设：** [判断] 只在调制输入变化低于校准阈值时复用特征，并在动作改变、动态小目标或 clip 边界强制重算；检验真实墙钟收益是否能同时保住动作服从与状态稳定性。

**三路检索式：**

- 问题词：driving diffusion world model inference latency and deployment cost
- 机制词：timestep embedding aware cache autonomous driving video denoising
- 同义/邻域词：feature reuse fast sampling action conditioned long horizon world model

**检索来源：** CVF proceedings checked 2026-08-07 · arXiv and web indexes checked 2026-08-07 · OpenAlex/Crossref style indexes partially timed out 2026-08-07 · official TeaCache and Vista repositories checked 2026-08-07 · AAAI and CVPR proceedings checked 2026-08-07

**最接近工作：**

- [TeaCache](https://openaccess.thecvf.com/content/CVPR2025/html/Liu_Timestep_Embedding_Tells_Its_Time_to_Cache_for_Video_Diffusion_CVPR_2025_paper.html)
- [ARCache](https://openaccess.thecvf.com/content/CVPR2026/papers/Nan_Accelerating_Autoregressive_Video_Diffusion_via_History-Guided_Cache_and_Residual_Correction_CVPR_2026_paper.pdf)
- [Fine-flow Driving World Model](https://ojs.aaai.org/index.php/AAAI/article/view/39860)
- [Vista](https://proceedings.neurips.cc/paper_files/paper/2024/hash/a6a066fb44f2fe0d36cf740c873b8890-Abstract-Conference.html)
- [Epona](https://openaccess.thecvf.com/content/ICCV2025/papers/Zhang_Epona_Autoregressive_Diffusion_World_Model_for_Autonomous_Driving_ICCV_2025_paper.pdf)

**最小接入实验：** 固定一个 Vista 类 checkpoint 和单张 GPU，比较 full-step、固定间隔 cache、TeaCache 与 reduced-step；在普通片段、动作切换和多轮 rollout 上用三次种子报告时延、显存、FVD、轨迹差、动态目标误差与状态漂移。

**回滚基线：** 未修改的 full-step sampler，加一个简单固定间隔 cache 与匹配的 reduced-step sampler。

**什么会推翻它：** 若匹配质量后没有墙钟收益，或动作服从、动态小目标、跨 clip 漂移超过预设容差，就只把 TeaCache 保留为负对照。

**最大失效条件：** 全局阈值可能因大面积静态背景而错误复用特征，漏掉小而快的交通参与者或动作变化；rollout 还会累积 cache 误差，且 Vista 是 UNet，源证据很多来自 DiT。

**公开边界：** Video diffusion caching and driving-world-model acceleration are both public; this row records partial overlap only. The remaining test is action- and state-aware caching under a fixed driving protocol not an unused broad opportunity.

**源论文与代码：** [论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Liu_Timestep_Embedding_Tells_Its_Time_to_Cache_for_Video_Diffusion_CVPR_2025_paper.pdf) · [正式入口](https://openaccess.thecvf.com/content/CVPR2025/html/Liu_Timestep_Embedding_Tells_Its_Time_to_Cache_for_Video_Diffusion_CVPR_2025_paper.html) · [官方代码 @ 7c10efc4](https://github.com/ali-vilab/TeaCache/tree/7c10efc4702c6b619f47805f7abe4a7a08085aa0) · 许可证 Apache-2.0。这里只核验仓库身份、固定 SHA 与许可证，没有运行源码或证明迁移收益。

## 当前检索边界

本轮自动多源检索中，OpenReview Python 客户端不可用，OpenAlex、DBLP 部分请求出现 5xx；已用官方 CVF、ICLR/NeurIPS proceedings、OpenReview 网页、arXiv、作者项目页、Semantic Scholar 与 Crossref 交叉补查。这个雷达因此给出的是可复查的有限范围结论，不是对整个学术史的绝对否定。新会议批次、预印本或仓库出现时，自动化必须重新跑碰撞检索；找到直接覆盖就降级或撤下候选。
