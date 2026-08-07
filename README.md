# DrivePerceptionLab

> **自动驾驶感知论文精读与可迁移算法设计卡。** 每天产出两份可以真正学懂、可以回查
> 证据的研究资产：一篇自动驾驶感知深度精读，
> 一张跨领域可迁移的算法 Taste 设计卡。精读系统覆盖 13 个感知主方向；设计卡只收
> 有明确瓶颈、接口、受控证据和失败边界的模块、主干网络或训练单元。

[▶ 今天的论文精读](#-今日论文精读) · [🧩 今天的算法 Taste](#-今日算法-taste) ·
[🏁 SOTA 协议雷达](sota/README.md) · [🔭 跨领域迁移雷达](transfer/README.md) ·
[🗺 13 类学习路线](index/topics.md) · [📚 全部精读](index/papers.md) ·
[💡 全部设计卡](taste/README.md) · [🎯 为什么选它](docs/daily-selection-and-gap-audit.md)

<!-- AUTO:STATS:START -->
**12 篇精读** · **12 篇正式录用** · **12 篇关键源码已审** · **7 张算法 Taste 卡** · **覆盖 12/13 个感知主方向** · 最近更新：**2026-08-07**
<!-- AUTO:STATS:END -->

<!-- AUTO:LATEST:START -->
## ▶ 今日论文精读

### [Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability](notes/2026/2026-08-07-vista.md)

**NeurIPS 2024**

> Vista 以三帧 latent 替换和统一动作适配生成高保真未来；FID/FVD 强，但训练读真值历史、推理读生成历史，方差奖励也未获闭环安全校准。

**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 → 固定版本源码 → 证据边界

[正式录用](https://proceedings.neurips.cc/paper_files/paper/2024/hash/a6a066fb44f2fe0d36cf740c873b8890-Abstract-Conference.html) · **世界模型与生成式 3D/4D 建模** · Monocular Camera + Vehicle State · World Model · Video Diffusion · Future Prediction · Action Conditioning · Autoregressive Rollout · Uncertainty · Reward Modeling · Foundation Model · 官方源码已核到固定 commit · **Checkpoint 未运行**

[论文原文](https://proceedings.neurips.cc/paper_files/paper/2024/file/a6a066fb44f2fe0d36cf740c873b8890-Paper-Conference.pdf) · [官方代码 @ cc9821b4](https://github.com/OpenDriveLab/Vista/tree/cc9821b4253ca7987c32757613d2fc2448fa9f5d)
<!-- AUTO:LATEST:END -->

<!-- AUTO:TASTE:START -->
## 🧩 今日算法 Taste

### [Dynamic-Prior Latent Replacement](taste/2026/2026-08-07-dynamic-prior-latent-replacement.md)

> 把少量历史状态写成不可再预测的干净槽位并只监督未来；迁移关键是明确 read/write/reset 与训练—推理历史身份。

**来自：** [Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability](https://proceedings.neurips.cc/paper_files/paper/2024/file/a6a066fb44f2fe0d36cf740c873b8890-Paper-Conference.pdf) · [正式录用](https://proceedings.neurips.cc/paper_files/paper/2024/hash/a6a066fb44f2fe0d36cf740c873b8890-Abstract-Conference.html) · **History Injection in Latent Diffusion**

**可迁移到：** Streaming BEV · Occupancy Forecasting · Video World Models · Temporal Query Memory

**先记边界：** 历史错位或 scene reset 泄漏会把错误硬写成事实；Table 3 只控制 prior 数量并未证明 replacement 优于 concat/attention。

[看原理图、接口合同、适用场景与反证实验 →](taste/2026/2026-08-07-dynamic-prior-latent-replacement.md) · [固定实现 @ cc9821b4](https://github.com/OpenDriveLab/Vista/tree/cc9821b4253ca7987c32757613d2fc2448fa9f5d)
<!-- AUTO:TASTE:END -->

## 三种读法

- **5 分钟判断值不值得深读：** 先看摘要后的“为什么今天值得读”、问题背景、
  前置论文路线、第一张方法图和证据边界；
- **30 分钟真正理解：** 沿“原图 → 公式画面 → 变量身份与变化 → 小数字例子
  → 结果与消融”读到数据集怎样分、实验怎样跑，以及证据支持什么、没有支持
  什么；公式中的“领域惯用”只表示概念角色常见，不表示所有论文强制用同一字母；
- **研究级核验：** 再进固定版本源码、论文—源码差异、复现账本与
  [相邻工作核查](docs/daily-selection-and-gap-audit.md#3-下一步是否已经做过的强制检索)。

想按问题系统学习，从[13 类学习路线](index/topics.md)进入；想寻找可迁移接口，
打开[算法 Taste](taste/README.md)；想继续追可证伪的问题，查看
[开放问题雷达](index/open_questions.md)。要核对当前指标量级与严格比较协议，查看
[SOTA 与指标雷达](sota/README.md)；要寻找其他计算机领域尚值得受控验证的窄迁移
接口，并同时看到已经发生的检索碰撞，查看[跨领域迁移雷达](transfer/README.md)。

## 每日怎么选

先看近 24 个月及当前/前两个会议年份的正式顶会内容，再看仍影响今天研究判断的
关键经典；同时综合 13 类覆盖、后续采用、受控证据、官方源码、作者/团队研究
脉络与可验证的创新空间。MIT 等顶尖团队会进入优先候选池，但机构名望、引用和
热度都不能替代方法质量。每篇新笔记公开同轮候选对照；每个准备突出显示的
“下一步”都先检索最接近已有工作，有限检索结论绝不写成“学界无人做过”。

[查看完整选文评分与缺口核查协议 →](docs/daily-selection-and-gap-audit.md)

## 最近完成

<!-- AUTO:RECENT:START -->
- **2026-08-07 · NeurIPS 2024** — [Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability](notes/2026/2026-08-07-vista.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-06 · IEEE TPAMI 2025** — [Benchmarking and Improving Bird’s Eye View Perception Robustness in Autonomous Driving](notes/2026/2026-08-06-robobev.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
- **2026-08-05 · CVPR 2022** — [TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers](notes/2026/2026-08-05-transfusion.md) — 官方源码已核到固定 commit；**Checkpoint 未运行**
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
