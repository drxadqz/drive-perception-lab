# SensorLedger3D Daily Paper Reading Log

这是一个面向流式 3D 感知、Occupancy、时序记忆、鲁棒多传感器融合、
延迟故障修复与可撤销状态的每日论文精读项目。

目标不是积累论文摘要，而是每天完成一篇可审计的“论文＋官方开源仓库”
联合精读，持续回答四个问题：

1. 这篇论文真正解决了什么问题，核心证据是否支持其主张？
2. 关键模块在源码中究竟如何实现，而不只是论文图中如何描述？
3. 哪些设计可以迁移到 SensorLedger3D，哪些会破坏 exact revocation 假设？
4. 论文和代码留下了什么未解决问题，可以形成新的可证伪创新假设？

## 选择优先级

1. 近五年的 CVPR、ICCV、ECCV、ICLR、NeurIPS、ICML、CoRL 等正式录用论文；
2. 与 streaming 3D perception、occupancy、temporal memory、sensor failure、
   delayed alarms、counterfactual repair、machine unlearning 高相关；
3. 有作者官方 GitHub 仓库、公开 checkpoint 或完整配置；
4. 代码入口清楚、可定位关键模块；
5. 对当前项目有直接可迁移价值或构成重要 novelty collision。

预印本可以作为“新颖性预警”阅读，但不能伪装成已录用顶会论文；如果当天
选择预印本，笔记标题和元数据必须明确标注。

## 目录

```text
notes/YYYY/              每日精读笔记
index/papers.csv         去重、状态和主题索引
index/open_questions.md  跨论文未解决问题与创新假设
templates/               固定笔记模板
```

## 每日交付标准

每篇笔记至少包含：

- 正式录用身份或预印本身份核验；
- 论文、补充材料、官方代码、checkpoint 与固定 commit 链接；
- 论文问题、核心机制、关键公式和实验逻辑；
- 源码入口、调用链、关键类/函数和配置；
- 论文描述与源码实现的一致或不一致之处；
- 对 SensorLedger3D 可迁移的模块；
- 会破坏精确撤销假设的设计；
- 尚未解决的问题；
- 至少一个可以被实验推翻的创新假设；
- 下一步最小验证实验；
- 证据、推断和建议的明确分栏。

## 提交约定

- 每天一篇论文为默认上限，宁缺毋滥；
- commit message：`read: YYYY-MM-DD <short title>`；
- 笔记不复制大段受版权保护的正文或源码；
- 只引用必要的短句、公式结构和源码 permalink；
- 遇到仓库 license 不清楚时只做链接和分析，不复制实现。

