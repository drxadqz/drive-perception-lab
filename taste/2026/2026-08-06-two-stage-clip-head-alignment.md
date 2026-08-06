# 2026-08-06 — Two-Stage CLIP Detection-Head Alignment

> - **卡片状态：** 完成；论文与固定源码已审，checkpoint 未运行
> - **来源论文：** [Benchmarking and Improving Bird’s Eye View Perception Robustness in Autonomous Driving](https://arxiv.org/pdf/2405.17426) · IEEE TPAMI 2025 · Accepted
> - **官方实现：** [worldbench/RoboBEV @ 3a32edaba9434dc27791bd25a1168951d091bd89](https://github.com/worldbench/RoboBEV/tree/3a32edaba9434dc27791bd25a1168951d091bd89)
> - **机制家族：** Staged Foundation-Model Adaptation
> - **迁移目标：** Robust BEV Detection · Multi-Modal BEV · Open-World Perception · Domain-Shift Adaptation
> - **证据标签：** [论文] · [源码] · [判断] · [未核验]

> **一句话 Taste：** 当强预训练 backbone 和随机任务 head 的接口错配时，先冻结 backbone、只让 head 学会“读懂”表示，再端到端微调；这个顺序值得迁移，但它依赖阶段一真的建立任务接口，且不能用见过的 benchmark corruption 冒充未知分布鲁棒性。

## 1. 先看瓶颈：为什么需要它

**30 秒问题故事：** **[笔记解释]** 一位熟悉各种天气的“视觉观察员”CLIP 刚加入自动驾驶团队，但接线到一个随机初始化的三维检测 head。若第一天就让两边一起大幅改参数，随机 head 的噪声梯度会同时改变观察员与接口；若永远冻结观察员，接口又可能始终读不懂 BEV 任务需要的几何信息。两阶段训练先固定观察员、只校正翻译员，再让两者一起细调。

**作者明确瓶颈：** **[论文]** RoboBEV Table 10 显示，冻结 CLIP 直接训练/使用任务头时，clean NDS 只有 0.2223、mRR 52.61，低于 BEVDet baseline 的 0.3500、58.54；随机 head 的 CLIP 端到端微调虽恢复 clean 性能，OOD 提升仍有限。来源：§5.5.2、Figure 4、Table 10，PDF p. 10–11。

**笔记因果重建：** **[判断]** 这是本笔记根据前述瓶颈与论文结构所做的因果重建，不是作者原句：阶段一把“表示学习”和“任务接口学习”暂时解耦，使第一轮直接梯度只进入 head；阶段二再允许 backbone 适应任务。合理性来自梯度路径和受控结果，不证明随机 head 一定会破坏 CLIP，也不证明所有任务都需要两阶段。

**它不是整篇论文换名：** 本卡只分析 Figure 4 中的 head-alignment 训练单元，不把 nuScenes-C、mCE/mRR 或全部 RoboBEV 结果包装成一个模块。

## 2. 原理图：它怎样执行

![先冻结预训练 CLIP 并用带腐蚀输入训练随机检测头，再解冻 CLIP 与已对齐检测头做端到端微调](../../assets/taste/2026-08-06-two-stage-clip-head-alignment/figure-01.png)

> **原图出处：** Xie et al., IEEE TPAMI 2025, Figure 4，PDF p. 10，来自[官方 PDF](https://arxiv.org/pdf/2405.17426)；仅裁取理解模块所需区域，原图版权归原作者及其他权利人。

**执行顺序：**

1. 读取 clean 与 corruption-augmented 环视图像；论文没有公开增强采样比例。
2. 用预训练 CLIP 视觉 backbone 提取透视图像表示；阶段一把它冻结。
3. 随机初始化三维 detection head，让检测监督只更新 head，使 head 对齐 CLIP 表示空间。
4. 解除 CLIP 冻结，以阶段一所得 head 为起点，端到端微调 backbone 与 head。
5. 在 clean nuScenes 与 nuScenes-C 分别评测 NDS 和 mRR。

**输入：** Surround Camera 图像；论文 Table 10 没有公开 CLIP 具体变体、输入分辨率、特征层、每视图特征 shape、camera-to-ego 坐标变换或 corruption mix 比例。

**内部表示：** CLIP perspective-view features → BEVDet 原有 view transformation / BEV features → detection head。论文的云状“CLIP Representation Space”是概念图，不是公开的张量坐标或可直接量化的流形。

**输出：** nuScenes 三维框与检测分数；没有跨帧 prediction-relevant state。训练 optimizer state 只影响参数更新，不能当作模型时序记忆。

**源码边界：** **[源码]** 固定官方树支持 RoboBEV 的 corruption 生成与评测，但本次固定树检索没有 Figure 4 的 CLIP-BEVDet config、阶段切换脚本、checkpoint 或 trainer；通用 `clip_sigmoid.py` 不等价于本单元实现。故本节真实顺序来自论文，不冒充源码调用链。

## 3. 架构位置与接口合同

**位置与上下游：** 它位于 CLIP 图像 backbone 与 BEVDet 的 view transformation / detection head 训练路径之间；部署图本身不新增 layer，而是改变何时冻结与解冻已有参数。

**输入合同：** 多视图 RGB；clean/corruption 标签只决定数据采样，不是额外推理模态。若迁移到 LiDAR-camera fusion，LiDAR 分支应保持相同，以隔离图像 backbone 适配效应。

**输出合同：** 阶段一输出一个能消费冻结 CLIP 特征的已训练 head checkpoint；阶段二输出端到端适配后的 backbone + head checkpoint。两阶段必须保存明确的参数组和 optimizer 边界，避免误把“恢复 optimizer state”当成同一阶段连续训练。

**shape 与坐标系：** **[未核验]** 论文没有给 CLIP feature shape。接入 BEV 模型时必须明确每视图张量 *B* × *V* × *C* × *H* × *W*、相机坐标到 ego/BEV 坐标的 view transform，以及 CLIP 通道是否需要 projection；这些是迁移合同，不是原文已公开值。

**真实梯度路径：**

- **阶段一：** detection loss → detection head 参数；CLIP 参数冻结，梯度路径在 backbone 参数处阻断。若 view transform 属于 head 侧，必须明确它是否更新；原文未公开。
- **阶段二：** detection loss → detection head / view transform → CLIP backbone；两侧参数共同更新。
- **没有直接监督的部分：** 论文没有 feature alignment loss、文本 loss 或显式 corruption classification loss；不能因为同一 batch 有检测 loss 就说它直接监督每层 CLIP feature。

**初始化：** CLIP 使用公开预训练权重；detection head 随机初始化；阶段二从阶段一的已对齐 head 与原/阶段一冻结的 CLIP 权重开始。具体 random seed、初始化分布和 optimizer state 是否重置未公开。

**训练信息一致性：** 论文的强结果使用 corruption augmentation，因此训练见过与 benchmark 同家族的腐蚀；推理不需要 corruption label。作者明确指出，用这些合成腐蚀训练后再把 RoboBEV 当独立模型鲁棒性评测并不合适。

**算力依赖：** 阶段一节省 backbone backward，但仍需 CLIP forward 与 BEV head 训练；阶段二恢复全模型 backward。论文未报告 GPU、wall-clock、FLOPs、显存或总训练预算，不能写“训练更快”或“部署无额外代价”。

**固定 SHA 入口：** [官方固定仓库树](https://github.com/worldbench/RoboBEV/tree/3a32edaba9434dc27791bd25a1168951d091bd89)；[RoboBEV 结果与指标](https://github.com/worldbench/RoboBEV/blob/3a32edaba9434dc27791bd25a1168951d091bd89/README.md#L219-L312)。**[未核验]** 两阶段训练单元未随该树公开，不能给出虚构 symbol。

## 4. 设计 Taste：为什么值得迁移

**瓶颈 → 设计约束：** 强预训练表示与新任务 head 语义错配；需要先隔离随机接口产生的直接梯度，同时不能永远冻结 backbone。

**设计约束 → 机制：** 通过 freeze schedule，而不是新增复杂模块，先让任务端适配固定表示，再让表示端受任务监督微调。

**机制 → 预期作用：** 阶段一应提高 head 对 CLIP feature 的可读性；阶段二应恢复任务几何能力，同时少破坏一开始的预训练鲁棒表征。后半句是可检验假设，不是从结构自动成立。

**训练信号 → 证据：** Table 10 把“直接端到端 CLIP”和“先 head align 再端到端”分开，在有无 corruption augmentation 两组均报告 clean 与 mRR，证据粒度比整模型主结果更接近训练单元。

**可迁移原则：**

- 当 backbone 与 head 来自不同任务/表示空间时，先做接口对齐，再做联合适配。
- 用参数冻结明确梯度所有权：每个阶段谁被直接训练、谁只 forward、谁被阻断必须可审计。
- 阶段性训练的回滚基线不是“旧论文精度”，而是相同 backbone、数据、预算下的直接端到端和永久冻结两端。
- 任何鲁棒性结论都应同时报告 ID 绝对性能、OOD 绝对性能和相对保持率，防止只优化比例。

**自动驾驶可迁移接口：** 图像 backbone → view transform → BEV encoder 的边界最自然；也可用于 VFM/VLM feature 接 Occupancy、地图或开放词汇 head。可迁移只表示接口值得受控测试，不表示零改动必然提升。

## 5. 证据、边界与反证实验

**最强模块级证据：** **[论文]** Table 10，干预为“是否先做 head alignment”。无 corruption augmentation 时，直接端到端 CLIP 为 clean NDS 0.3609、mRR 59.10；head alignment 为 0.3710、61.18，即 +0.0101 NDS（约 +2.8%）和 +2.08 mRR 点（约 +3.5%）。有 augmentation 时为 0.3434/80.84 对 0.3667/84.32，即 +0.0233 NDS（约 +6.8%）和 +3.48 mRR 点（约 +4.3%）。

**证据支持：** 在作者的 CLIP + BEVDet + nuScenes-C 设置里，先 head align 后端到端微调优于直接端到端微调，并且 clean 与相对鲁棒性同时提高。

**证据不支持：**

- **[判断]** 没有独立报告不同冻结轮数、不同 CLIP 变体、不同 heads 或相同总更新步数下的曲线，不能确定增益来自阶段顺序而非额外训练预算。
- **[未核验]** 没有 checkpoint、seed、重复次数或置信区间，不能判断差值跨随机初始化是否稳定。
- **[判断]** corruption augmentation 提升 mRR 不等于未见 OOD 泛化，更不等于真实道路安全。
- **[判断]** 论文没有效率与部署证据；阶段一减少 backward 不能自动推出总训练更快。

**相邻工作核查：** 2026-08-06 执行三路检索：问题词 `CLIP fine-tuning loses OOD robustness`；机制词 `freeze backbone train head then end-to-end fine-tune`；同义/邻域词 `robust fine-tuning weight interpolation feature alignment vision-language model`。覆盖 CVF、OpenReview、PMLR、arXiv、OpenAlex/Semantic Scholar 类索引、官方项目与 GitHub。

**最近工作：**

- [WiSE-FT，CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Wortsman_Robust_Fine-Tuning_of_Zero-Shot_Models_CVPR_2022_paper.html)以 zero-shot 与 fine-tuned 权重插值维持 OOD，覆盖“微调损害鲁棒性”问题，但机制不是先训练任务 head。
- [Finetune Like You Pretrain，CVPR 2023](https://openaccess.thecvf.com/content/CVPR2023/html/Goyal_Finetune_Like_You_Pretrain_Improved_Finetuning_of_Zero-Shot_Vision_Models_CVPR_2023_paper.html)通过使微调目标更接近预训练改善 zero-shot vision model，覆盖表示保持动机，但不是 BEV 几何接口。
- [GRACE，CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Chopra_The_Geometry_of_Robustness_Optimizing_Loss_Landscape_Curvature_and_Feature_CVPR_2026_paper.html)联合曲率与 feature alignment 改善 VLM 鲁棒微调，覆盖更强的通用机制，但其源协议是分类/VLM，不证明 BEV 迁移。
- [RoboBEV，TPAMI 2025](https://ieeexplore.ieee.org/document/10857618)已经在 BEV 检测中直接做两阶段 head alignment，因此“把稳健 CLIP 微调用于 BEV”本身已被覆盖。

**覆盖判断：** **[部分覆盖]**。通用鲁棒微调与 BEV 直接应用都已有工作；可保留差异只能是严格匹配预算后，研究“接口对齐阶段”何时优于权重插值、目标保持或直接端到端，并扩到不同 BEV heads，而不是宣称首次把 CLIP 迁入自动驾驶。

**最小反证实验：** 在同一公开 BEV detector 上固定 CLIP checkpoint、数据、augmentation、总 optimizer steps 和推理预算，比较：原 backbone、永久冻结 CLIP、直接端到端、head alignment → 端到端、WiSE-FT。三次 seed 同时报 clean NDS、未见 corruption NDS/mRR、长尾类、校准、wall-clock 与峰值显存。

**推翻条件：** 匹配总更新步数后 head alignment 的均值/方差不优于直接端到端或 WiSE-FT；换一个 head 或不使用见过的 corruption 后增益消失；或校准/长尾性能超过预设容差恶化，均应拒绝迁移假设。

**最大失效条件：** 预训练表示缺少三维几何所需信息时，先对齐 head 只能适配错误接口；阶段一过长会把 head 锁在不可修正的局部解，阶段二过强仍可能遗忘 OOD 表示；用 benchmark corruption 训练还会污染评测解释。

## 6. 适用场景与最小接入方案

**适合：** 强 VFM/VLM 图像 encoder 接一个新 BEV/Occupancy/map head；head 随机初始化且 backbone 预训练分布广；可以显式控制 freeze schedule，并有 clean、seen-corruption、unseen-corruption 三组验证。

**不适合：** backbone 本身缺任务必要几何；head 与 backbone 已联合预训练；训练预算极小却被迫多阶段；或系统没有独立 OOD/校准评测，只能在训练见过的腐蚀上报提升。

**最小接入顺序：**

1. 固定原 detector 作为回滚基线，记录 clean/OOD/效率与三次 seed。
2. 替换图像 backbone，增加最小 channel projection；其他 BEV encoder、heads、数据和训练预算不变。
3. 阶段一冻结 backbone，只训练 projection、view transform 与 head；逐项记录哪些参数有梯度。
4. 阶段二解冻 backbone；为 backbone 与 head 分开设置参数组，但总 steps 与直接端到端基线匹配。
5. 在未参与训练的 corruption、真实 domain shift 和 sensor dropout 上评测，并与永久冻结、直接端到端、WiSE-FT 对照。

**回滚基线：** 相同 BEV detector 的原公开 backbone/checkpoint，以及相同 CLIP backbone 的直接端到端微调；两者缺一都不能判断收益来自预训练还是阶段顺序。

**许可证与复现状态：** RoboBEV README 声明 CC BY-NC-SA 4.0，并提示子操作另有许可；固定树所链接的 `docs/LICENSE.md` 不存在，需逐组件法律复核。论文 Figure 4 / Table 10 训练实现和 checkpoint 未公开，本卡为 Audited-paper / Partially-audited-code / Not-reproduced 状态，不能直接承诺可复现。

**公开表述边界：** 截至 2026-08-06，在列明来源、检索式与最近工作范围内，本次结论为部分覆盖；本卡只建议做受控迁移测试，不宣称零改动提升、首次使用、训练更快或更安全。
