# YYYY-MM-DD — Paper title

`Venue YYYY` · `Accepted / Preprint` ·
`论文已读 / 源码已读 / 已运行或未运行`

**主方向：** PXX · 中文方向名 ·
**输入模态：** Surround Camera / LiDAR / Language ·
**交叉标签：** 任务、表示、学习范式、可靠性或大模型关系

[▶ 从第一张图开始](#1-看图论文到底做了什么) ·
[返回首页](../../README.md) · [全部精读](../../index/papers.md) ·
[官方论文](https://example.org/paper.pdf) ·
[官方代码 @ 固定 SHA](https://github.com/example/repo/tree/FULL_SHA)

证据与行文标签：**[原文翻译]** 忠实中文译文；**[笔记解释]** 帮助理解的
通俗讲解；**[论文]** 作者材料直接支持；**[源码]** 固定 commit 直接支持；
**[判断]** 本笔记分析；**[未核验]** 尚未独立运行或确认。译文中不混入解释
或判断。

## 0. 阅读起点：术语先导与摘要完整翻译

### 0.1 首次术语解释

**术语覆盖声明：** 摘要中的核心专业术语先在这里解释；摘要之后第一次出现的
新术语仍须在正文首次出现处解释，之后全文保持相同中文名、英文名、缩写与符号。

- **领域通行中文名（English full name, ABC）**：用一句面向初学者但专业
  准确的话说明它是什么、在本文承担什么角色；后文统一写 ABC。
- **论文自定义方法名（Original method name）**：保留作者原名，并说明它是
  模型、模块、数据集还是任务；不要自行创造看似正式的中文名。
- **评测或实现术语（Evaluation or implementation term, EIT）**：解释它怎样
  影响本文实验流程、指标含义或复现边界，并锁定后文的统一写法。

> 术语必须结合该领域和本文语境确定，不能脱离专业含义逐字硬译，也不能为了
> “更通顺”随意意译。

### 0.2 摘要完整专业中文翻译

**原文锚点：** Abstract，PDF p. 1 / proceedings p. XXXX。

<a id="abstract-a01"></a>
> **[原文翻译] Abstract · PDF p. 1 · A01**
>
> 在这里按原摘要的段落顺序给出完整专业中文翻译。保留作者的限定词、否定、
> 比较关系、数值、指标和因果边界，不把摘要压缩成要点或改写成笔记观点。

如果原摘要包含多个段落，为每段依次增加 `A02`、`A03` 等稳定锚点，并分别
标出 PDF 页码。抽取不清楚的词句使用 **[未核验]** 标记，不凭上下文猜写。

**完整性声明：** 明确说明摘要是否按全部实质段落完整、未删减翻译，以及是否
存在抽取不清或原文缺失内容。

> [!TIP]
> **[笔记解释] 读完摘要再看这一句：** 用一句话说明论文做了什么、最强证据
> 是什么、最大边界是什么。这不是摘要译文。

**学习顺序：**
[0 摘要与术语](#0-阅读起点术语先导与摘要完整翻译) →
[1 看原图](#1-看图论文到底做了什么) →
[2 读原式](#2-读公式核心机制怎样表达) →
[3 看结果](#3-看结果证据是否支持主张) →
[4 对源码](#4-对源码公式如何落地) →
[5 记结论](#5-记结论贡献边界与开放问题)

## 1. 看图：论文到底做了什么

![能够独立说明图片内容的替代文本](../../assets/notes/NOTE_KEY/fig-method.png)

> **原图出处：** Author et al., Venue YYYY, Figure X, PDF p. Y。
> [官方 PDF](https://example.org/paper.pdf)。仅作学术讲解所需的局部摘录，
> 原图版权归原作者及其他权利人。

### 这张图按什么顺序看

1. 先看输入、坐标系或状态；
2. 再看论文真正新增的模块；
3. 最后看输出、训练目标或状态写回。

**看完应能复述：** 用一句话把信息流讲清楚。

**这张图没有证明：** 写清方法图不能替代哪些实验事实。

## 2. 读公式：核心机制怎样表达

### 原文公式 1：公式名称

**原文公式：** 论文 Eq. (X)，PDF p. Y。

<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="../../assets/notes/NOTE_KEY/formulas/eq-x-short-name-dark.png"><img src="../../assets/notes/NOTE_KEY/formulas/eq-x-short-name-light.png" alt="公式：论文 Eq. X，用自然语言说明这条公式做什么" width="480" height="84"></picture></p>

> **公式来源：** Author et al., Venue YYYY, Eq. (X)，PDF p. Y；
> 本图按原符号重排。[官方 PDF](https://example.org/paper.pdf) ·
> [可复制 TeX](../../assets/notes/NOTE_KEY/formulas/source.tex)。

**符号说明**

- *x*：标量；
- *M*<sub>*t*</sub>：时刻 *t* 的记忆状态；
- *ψ*：论文定义的映射。

**纯文字读法：** 用普通文本完整朗读公式，确保图片加载失败时仍能理解。

**玩具例子：** 用一个明确标为“教学示例、不是论文实验”的小数字走一遍。

**专业解释：** 说明这条式子定义的运算、假设和信息流。

**回到上面的图：** 指出对应箭头或模块。

**落到源码：** [文件 / symbol @ 固定 SHA](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

**公式省略了什么：** 写出实现中的 shape、mask、坐标、状态或数值细节。

> 如果论文没有不可替代的公式，删除上面的占位式并明确写：
> **原文无必要公式：** 这篇论文的核心贡献由算法流程或系统设计表达，
> 本笔记不为满足模板而编造公式。
>
> 如果关键原式没有编号，写成：
> **原文未编号公式：** 论文 PDF p. Y。不要为了通过检查伪造 Eq. 编号。
>
> “原文公式 / 原文未编号公式”与“原文无必要公式”只能选择一种模式。
>
> 块级公式由同一 TeX 命名块生成内容紧裁、像素尺寸一致的 2× light/dark
> PNG pair，并用单行 `<p><picture>…</picture></p>` 按自然尺寸居中；
> `<img>` 的 `width` / `height` 写显示尺寸，不把短公式铺满正文。普通行内数学
> 使用 Unicode、Markdown 斜体/粗斜体和 `<sub>` / `<sup>`；反引号只保留给
> `real_source_symbol` 这类真实源码标识。正文不使用 live MathJax。复杂源码
> 等价式或本笔记推导也使用公式图，但必须分别标成
> **[源码] 非论文原式** 或 **[判断] 非论文原式**。

## 3. 看结果：证据是否支持主张

### 3.1 原文公开的实验配置

**原文锚点：** 主论文 Experiments / Implementation Details，PDF p. X–Y；
Appendix / Supplement §X，PDF p. Z；固定 SHA config 与运行文档。

- **数据集、版本与 train/val/test 划分。** **[论文]** 写公开值和构造方式；
  未公开项明确说明。来源：论文 §X，PDF p. Y。
- **传感器、输入范围、分辨率与预处理。** **[论文/源码]** 写正文与固定
  config；两者不一致时并列。
- **训练硬件、软件与关键依赖。** **[源码]** 写 setup 或环境文件；GPU 型号、
  时长等未公开时使用 **[未核验]**。
- **初始化或预训练权重。** **[论文/源码]** 写来源、是否冻结及公开下载入口。
- **优化器、学习率与 scheduler。** **[论文/源码]** 区分论文直接报告的值和
  config 中的基础值、倍率或 param group。
- **batch size、训练轮数/steps 与增强。** **[论文/源码]** 写清总 batch 与
  per-device batch，不能混为一个数字。
- **随机种子、重复次数与模型选择。** **[未核验]** 原文未公开时直说，不按
  领域惯例补齐。
- **推理设置、阈值与后处理。** **[论文/源码]** 写输入组装、状态、采样参数、
  输出和 evaluator 前处理。
- **指标定义与基线公平设置。** **[论文]** 说明指标计算对象、方向、评测协议
  和基线结果来源。
- **checkpoint 与最短复现入口。** **[源码]** 链接公开权重、命令和
  [固定 SHA 配置](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)；
  没有真正运行时保留 **[未核验]**。

### 3.2 原文公开的实验流程

**原文锚点：** 主论文 Method / Experiments，PDF p. X–Y；Appendix /
Supplement §X；固定 SHA 数据、训练、推理和评测入口。

1. **数据准备：** **[论文]** 数据版本、划分、标注构造、过滤、坐标系和
   预处理；来源：论文 §X，PDF p. Y。
2. **训练阶段：** **[论文/源码]** 预训练/初始化、阶段顺序、冻结策略、损失、
   采样与增强；来源：[固定 SHA 训练配置](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)。
3. **验证与选模：** **[未核验]** 原文未公开验证频率、模型选择标准、随机种子
   或重复实验策略。
4. **推理与后处理：** **[源码]** 输入组装、阈值、时序状态、测试时增强和
   输出生成；来源：[固定 SHA 推理入口](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)。
5. **最终评测：** **[论文]** benchmark protocol、指标计算、提交服务器或
   本地脚本；来源：论文 §X，PDF p. Y。

流程只写公开证据能够支持的步骤，每一步附论文 PDF 页码、附录/补充材料章节
或固定 SHA 源码链接。论文与源码未形成完整闭环时，单列“复现仍缺什么”，
不要把合理猜测画成作者公开的实验流程。

### 3.3 核心结果

![能够独立说明表格内容的替代文本](../../assets/notes/NOTE_KEY/table-main.png)

> **原图出处：** Author et al., Venue YYYY, Table X, PDF p. Y。
> [官方 PDF](https://example.org/paper.pdf)。仅作学术讲解所需的局部摘录，
> 原图版权归原作者及其他权利人。

### 三个必须看的对照

1. **最强 baseline：**
2. **关键消融：**
3. **效率、稳健性或泛化：**

### 证据支持

- **[论文]**

### 证据没有支持

- **[判断]**
- **[未核验]**

## 4. 对源码：公式如何落地

```text
input
→ encoder
→ state read
→ key module
→ state write
→ prediction
```

### 1. 状态读取：`symbol`

- **论文对应：**
- **源码行为：**
- **需要留意：**
- [打开固定 SHA 源码](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

### 2. 核心计算：`symbol`

- **论文对应：**
- **源码行为：**
- **需要留意：**
- [打开固定 SHA 源码](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

### 3. 状态写回或输出：`symbol`

- **论文对应：**
- **源码行为：**
- **需要留意：**
- [打开固定 SHA 源码](https://github.com/example/repo/blob/FULL_SHA/path#L1-L20)

<details>
<summary><strong>展开完整源码审计、环境和复现风险</strong></summary>

- 状态张量与辅助状态：
- in-place 更新：
- 训练与测试差异：
- 环境与依赖：
- checkpoint / config：
- 最短复现命令：

</details>

## 5. 记结论：贡献、边界与开放问题

### 5.1 原文结论完整翻译

论文使用什么章节名就保留什么章节名，不把 Discussion、Summary、Limitations
与 Future Work 混成一个自拟结论。如果作者没有独立 Conclusion，先写精确
缺失声明，再以 `Discussion`、`Summary` 或 `Concluding Remarks` 等真实章节名
标记 C01、C02，只翻译其中实际承担收束作用的连续相关段落。

**原文锚点：** Conclusion，PDF p. X / proceedings p. YYYY。

<a id="conclusion-c01"></a>
> **[原文翻译] Conclusion · PDF p. X · C01**
>
> 在这里完整翻译 Conclusion 的第一个实质段落，保留原文的结论强度、限制
> 条件、数字和语气，不加入本笔记评价。后续段落依次使用 C02、C03。

若真实收束章节是 Discussion，则把上方译文头改成
`[原文翻译] Discussion · §X Discussion / PDF p. X · C01`；Summary 或
Concluding Remarks 同理。稳定代码仍使用 C01，但绝不把真实章节名改成
Conclusion。

**完整性声明：** 明确说明 Conclusion 是否已按全部实质段落完整、未删减翻译。

**原文缺失声明：** 若论文没有独立 Conclusion，改写为：
“论文没有独立 Conclusion；已检查真实收束章节 Discussion / Summary，本节
按原章节名翻译相关连续段落，不冒充、不改写为作者未设置的 Conclusion。”

### 5.2 原文局限与展望完整翻译

**原文锚点：** Limitations / Discussion / Future Work，PDF p. X–Y。

<a id="limitations-l01"></a>
> **[原文翻译] Limitations / Discussion · PDF p. X · L01**
>
> 在这里完整翻译作者公开的局限。不要把笔记发现的缺点冒充为作者承认的
> 局限；后续段落依次使用 L02、L03。

<a id="outlook-o01"></a>
> **[原文翻译] Future Work / Outlook · PDF p. X · O01**
>
> 在这里完整翻译作者提出的未来工作。若它位于 Limitations 或 Conclusion
> 的连续上下文中，保持原顺序；后续段落依次使用 O02、O03。

**完整性声明：** 明确说明局限与展望是否已按相关连续段落完整、未删减翻译。

**原文缺失声明：** （Limitations）如果论文没有独立 Limitations 或没有作者
明确陈述的局限，写清检查过的真实章节，并声明本笔记不代写、不补写作者没有
承认的局限。

**原文缺失声明：** （Future Work）如果论文没有独立 Future Work / Outlook
或没有明确展望，写清检查过的真实章节，并声明本笔记不代写、不补写作者没有
提出的未来工作。

结论、局限和展望中的新术语仍执行首次出现解释规则。译文之后再进入下面的
笔记归纳，两个层次不得合并。

### 5.3 笔记分析与研究启发

**[笔记解释]** 说明下面怎样把作者结论转成读者可复述的知识。

**[判断]** 说明下面的批评、研究切口和可证伪实验是本笔记分析，不是作者已经
证明的结论，也不自动代表学界尚无相邻工作。

#### 5.3.1 学完必须记住的三点

1. **[论文] 方法核心：**
2. **[论文/源码] 最强证据：**
3. **[判断] 最大缺口：**

#### 5.3.2 仍未解决的问题

- **已观察事实：**
- **为什么仍是问题：**
- **能区分解释的最小测试：**
- **相邻工作：**

<details>
<summary><strong>身份、许可与证据账本</strong></summary>

- Venue 与权威录用来源：
- Paper / supplement：
- 官方仓库与固定 commit：
- License：
- Checkpoint：
- 已读源码：
- 尚未运行或核验：

</details>

> [!NOTE]
> 发布前必须运行索引、公式资产和公开页面检查；逐张核对图号、页码、出处、
> 替代文本、PNG/TeX 一致性及 iPad 竖屏/横屏清晰度；原文公式与本笔记推导
> 不得混写，正文必须保持零 live MathJax。还必须逐段核对摘要、结论、局限
> 与展望是否完整，原文章节/PDF 页码/稳定锚点是否正确，实验配置是否区分
> “已公开”“未公开”和“本笔记未运行”，首次术语是否已经解释且全文一致。
