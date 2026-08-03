# 2026-08-04 — Depth-Aware Ray Sampling

> - **卡片状态：** 已完成论文、补充材料与固定源码审计；结果未独立复现
> - **来源论文：** [UniPAD: A Universal Pre-training Paradigm for Autonomous Driving](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.pdf) · CVPR 2024 · Accepted
> - **官方实现：** [Nightmare-n/UniPAD @ 3d24add15f887a4c5b7b54cb3a6b4a812c24ca52](https://github.com/Nightmare-n/UniPAD/tree/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52)
> - **机制家族：** Geometry-Guided Supervision Sampling
> - **迁移目标：** 相机自监督预训练 · BEV 特征学习 · 多模态表示学习 · 神经渲染
> - **证据标签：** [论文] · [源码] · [判断] · [未核验]

**录用核验：** [CVPR 2024 官方 proceedings 页面](https://openaccess.thecvf.com/content/CVPR2024/html/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.html)。

> **一句话 Taste：** 把有限训练预算优先投到“能同时得到观测与几何真值”的位置，可提高每条射线的监督密度；但当几何传感器稀疏、失配或有系统性盲区时，这种选择也会把偏差写进表示。

## 1. 先看瓶颈：为什么需要它

一辆车在路口有六路相机图像和稀疏 LiDAR。若渲染所有像素，绝大多数计算花在重复背景上；若均匀随机抽 512 个像素，很多像素没有 LiDAR 深度，只能给颜色监督。Depth-Aware Ray Sampling 不改变渲染器，而是在固定射线预算内优先选择投影 LiDAR 有效的位置，让同一条射线同时产生 RGB 与几何误差。

**作者明确瓶颈：** [论文] UniPAD §3.4，PDF pp. 4–5 指出，对高分辨率图像做稠密 volumetric rendering 会消耗大量内存；随机采样可能缺少足够三维几何信息，因此作者使用 LiDAR 深度引导采样。

**笔记因果重建：** [判断] 这是本笔记根据前述瓶颈与论文结构所做的因果重建，不是作者原句：当每条射线成本近似固定时，优化问题可理解为提高“单位射线获得有效几何监督”的概率；但最优采样分布还必须覆盖没有 LiDAR 回波却对下游重要的区域。

**零基础术语：** **射线（ray）** 是从相机光心穿过一个像素向三维空间延伸的直线；**监督密度（supervision density）** 是一个训练 batch 中真正拥有目标值、能贡献有效损失的位置比例；**投影深度（projected depth）** 是用相机–LiDAR 标定把三维点映射到像素后得到的距离。

## 2. 原理图：它怎样执行

![膨胀、随机与深度感知射线采样：后者把预算优先放在有 LiDAR 投影的像素](../../assets/taste/2026-08-04-depth-aware-ray-sampling/figure-04-depth-aware-ray-sampling.png)

> **原图出处：** [论文] Figure 4，PDF p. 5 / proceedings p. 15242，来自[官方 PDF](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_UniPAD_A_Universal_Pre-training_Paradigm_for_Autonomous_Driving_CVPR_2024_paper.pdf)；仅裁取理解模块所需区域，原图版权归原作者及其他权利人。

**执行顺序：**

1. **投影：** [源码] 读取 LiDAR 点和相机标定，把点从 LiDAR 坐标系投影到六个相机像素平面。
2. **有效性过滤：** 只保留落在图像内且 LiDAR 平面半径位于 3–50 m 的点；同一像素的深度来源由投影结果决定。
3. **几何优先抽样：** 每视角最多从这些深度像素中无放回随机抽 512 个。
4. **预算补齐：** 若深度像素不足 512，固定源码从图像网格补射线：跳过顶部 40% 区域，空间步长 4；这些射线的深度标成无效，只提供 RGB 监督。
5. **沿射线采点：** 每条射线在 3–50 m 范围内先取 72 个均匀样本，再取 24 个重要性样本，总计 96 点。
6. **损失分流：** 所有 512 条射线计算 RGB L1；只有有效深度大于零的射线计算 depth L1。

**[笔记解释] 小数字例子：** 假设随机 512 条射线中只有 90 条有深度，而引导采样得到 400 条有效深度射线。在渲染点数不变时，后者一批可得到约 4.4 倍的几何误差项。但如果 400 条全部集中在近处车辆和路面，远处交通灯仍可能被欠采样；“更多有效监督”不自动等于“更全面的监督”。数字仅为教学例子，不是论文实测。

## 3. 架构位置与接口合同

**位置与上下游：** 位于数据准备和渲染解码器之间。上游提供原始 LiDAR 点、六相机图像、LiDAR-to-camera 与 camera-to-image 标定；下游是 `RayBundle`、NeuS 采样器与 RGB/depth loss。

**输入：** 每个 batch 的 LiDAR 点坐标、图像 tensor、标定矩阵和数据增强后的图像 shape。固定实现首先用点云横纵坐标计算平面半径，再把齐次三维点映射到相机。

**输出与 shape：** 每个相机输出最多 512 个二维像素、对应 RGB、深度标签和相机射线；六相机在 batch 内合并。每条射线下游生成 96 个三维采样点。像素坐标属于增强后的相机平面，射线三维点位于统一 LiDAR/world 约定的场景坐标；标定增强的一致性必须保持。

**状态语义：** 该单元没有跨帧 prediction-relevant state，也没有序列 slot 或 reset；LiDAR sweeps 是当前样本的聚合输入。随机数生成器状态会影响抽到哪些射线，但它是训练过程状态，不是模型记忆。

**训练信号与真实梯度路径：** RGB L1 直接监督所有选中射线，depth L1 只监督 `depth_gt > 0` 的射线；损失经 NeuS 权重、SDF/RGB 网络、三线性体积采样和共享参数间接训练体积、FPN 与未冻结编码器。离散投影过滤与 `np.random.choice` 索引不可微，标定矩阵和采样概率没有梯度。不能因为 depth loss 与所有射线同处一个 batch，就说它直接训练了 RGB-only 回退射线。

**初始化：** 单元本身无可学习参数，不需要权重初始化；其行为由标定、随机种子、射线预算、距离范围、网格间隔和 sky-region 常量初始化。相机 backbone 的 ImageNet 初始化与冻结属于上游，不是该采样单元的能力。

**算力依赖：** [论文] 固定射线预算降低相对稠密/膨胀采样的显存；Table 12 只报告 1× 与 1.4× memory。没有 FLOPs、训练吞吐或 wall-clock 数据，因此不能写“训练更快”。投影、NumPy 选择和 LiDAR 数据读取仍有额外开销。

**固定源码入口：** [源码] [RenderHead.sample_rays](https://github.com/Nightmare-n/UniPAD/blob/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52/projects/mmdet3d_plugin/models/dense_heads/render_head.py#L152-L298)；[RenderHead.forward](https://github.com/Nightmare-n/UniPAD/blob/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52/projects/mmdet3d_plugin/models/dense_heads/render_head.py#L300-L462)；[深度 mask 损失](https://github.com/Nightmare-n/UniPAD/blob/3d24add15f887a4c5b7b54cb3a6b4a812c24ca52/projects/mmdet3d_plugin/models/render_utils/models/base_surface_model.py#L120-L138)，均来自 Nightmare-n/UniPAD @ `3d24add15f887a4c5b7b54cb3a6b4a812c24ca52`。

## 4. 设计 Taste：为什么值得迁移

**瓶颈 → 设计约束：** 渲染预算不足，且并非每个位置都有几何标签；所以选择器既要提高有效监督比例，又不能改变下游渲染接口或扩大显存。

**设计约束 → 机制：** 用一个便宜、无需学习的几何传感器投影作为 proposal distribution，优先抽到能同时计算 RGB 与 depth loss 的位置；不足时用网格回退保持固定 batch shape。

**机制 → 预期作用：** 同样 512 条射线包含更多几何监督，减少“随机抽到大量无深度背景”的方差；回退分支保留一定图像覆盖，避免因 LiDAR 稀疏而无法凑 batch。

**预期作用 → 证据：** [论文] Table 12 的固定 memory 比较显示小幅正增益；固定源码证实深度 loss 的有效性 mask 与回退语义。证据没有隔离“有效深度数量”和“几何位置先验”，因此可迁移的是实验假设，不是未经测试的必然收益。

**可迁移原则：** [判断] 对昂贵的稀疏监督任务，先定义每个候选位置能提供哪些损失，再按“稀缺监督可用性”分配预算；同时保留一部分与该辅助传感器无关的探索样本，并记录实际 inclusion probability。这个原则可用于 BEV occupancy query、稀疏深度补全、跨模态对齐 token 和需要昂贵 teacher 标注的区域选择。

**为什么不是简单 hard-example mining：** 这里没有按当前模型误差选择“难例”，而是按外部几何真值是否存在选择“信息更完整的位置”。它减少无效标签，不保证选择最难或最有语义价值的样本。

## 5. 证据、边界与反证实验

**最强模块级证据：** [论文] UniPAD Table 12，PDF p. 8：在作者低数据消融设置中，直接替换采样策略。Depth-aware 为 1× memory、32.9 NDS / 32.6 mAP；Random 为 1×、32.5 / 32.1；Dilation 为 1.4×、31.9 / 32.4。相对 Random 的绝对增益为 0.4 NDS、0.5 mAP；相对 Dilation 为 1.0 NDS、0.2 mAP且表中 memory 更低。

**证据支持：** 在该 nuScenes/UVTR-C/低数据设置和单次报告下，几何引导采样优于作者的随机、膨胀替代，且没有增加相对 Random 的表中显存倍率。

**证据不支持：** 没有多种子方差、训练时间、FLOPs、不同射线数、有效深度比例、跨数据集、纯图像预训练、标定扰动或类别覆盖统计。0.4/0.5 点不能未经方差就宣称稳健；memory 结果不能改写成“更快”；检测指标不能改写成“更安全”。

**最大失效条件：** [判断] 辅助 LiDAR 稀疏、时间不同步、标定偏移或在远处/反光/恶劣天气下系统性缺失时，采样器会过度代表“LiDAR 容易看见的区域”。若下游关键目标恰在这些盲区，例如远处行人、灯色或被遮挡物体，监督密度更高也可能降低任务覆盖。

**仍不知道：** [未核验] Table 12 的收益来自有效 depth ray 数量、空间位置分布、3–50 m 过滤还是 RGB-only 回退；论文没有逐项隔离。

**最小反证实验：**

1. 固定 backbone、512 rays、96 points、总有效 depth-ray 数、显存和训练步数。
2. 比较均匀随机、原 depth-aware、深度数量匹配但位置随机、类别/距离分层四组，每组三个以上种子。
3. 对投影施加 0、0.25、0.5、1.0 像素可控偏移，并在另一个传感器布局上复测。
4. 报告 NDS/mAP 均值与方差、每类/距离段覆盖、有效监督比例、显存与 wall-clock。

**推翻条件：** [判断] 若匹配有效深度数量后原方法不再优于位置随机，说明收益主要来自标签数量而非几何引导位置；若轻微标定偏移就使其显著劣于随机，或跨布局稳定反向，则推翻“该采样规则可直接迁移”的假设。

## 6. 适用场景与最小接入方案

**适合：** 训练期有可靠辅助几何真值、单位置解码成本高、有效标签稀疏、且目标允许固定预算抽样的相机/BEV 自监督任务；辅助传感器可以只在训练期存在。

**不适合：** 没有 LiDAR/深度 teacher、标定不可靠、关键语义与几何回波弱相关、需要无偏稠密覆盖，或法规/安全验证要求明确 inclusion probability 的场景。它也不适合直接替代下游推理采样，因为原证据只覆盖预训练。

**自动驾驶迁移接口：** 上游只需输出候选位置、辅助标签有效 mask 与坐标变换；下游保持原来的 ray/query decoder 和 loss。将“深度有效”替换为 occupancy 边界有效、跨车协同重叠区有效或高置信 teacher 标签有效时，必须重新检查覆盖偏差。

**最小接入顺序：**

1. 在现有训练器中记录随机采样的有效监督率、类别/距离覆盖和显存，得到不可省略的 baseline。
2. 新增纯函数 sampler：输入候选与 valid mask，输出固定数量索引；先不改 backbone、decoder 或 loss。
3. 预留 20%–50% 均匀探索 quota，剩余预算按辅助监督有效性抽样；把 quota 作为唯一新变量扫描。
4. 记录每个位置被选概率和有效监督比例，至少三种子比较；确认收益后再尝试距离/类别分层。

**回滚基线：** 同预算的 Uniform Random Sampling。若验证均值没有超过其跨种子标准差、类别覆盖恶化、或标定扰动显著放大损失，立即回滚；不要同时改 ray 数、decoder 或 loss 权重。

**许可证与复现状态：** [源码] 官方仓库根许可为 Apache-2.0，并含 OpenMMLab 派生组件。采用代码前仍应保留版权与许可声明并复核依赖。**[未核验]** 本卡只审计固定 SHA 的公开源码，没有编译 CUDA 算子、下载 nuScenes/checkpoint、计时或复现 32.9/32.6。

**最终 Taste：** 可迁移的不是 `sample_rays` 这段具体代码，而是“在固定昂贵预算下，把稀缺有效监督的可用性纳入采样分布，并用探索 quota 与受控匹配实验约束选择偏差”的设计原则。
