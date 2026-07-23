# Cross-paper open questions

这个文件只收录跨至少一篇论文或一段源码证据支持的问题。每个问题必须能转换
为可证伪假设，不能只是“未来可以提升性能”。

## Active questions

| ID | Question | Evidence notes | Falsifiable hypothesis | Minimum test | Collision status |
|---|---|---|---|---|---|
| Q001 | Can one historical camera-frame write be removed exactly without replay? | ST-Occ fuses cameras before nonlinear overwrite and retains no per-camera ledger | Additive sufficient-statistic memory reaches FP32 state error <1e-5 versus its own masked rerun with <0.5 clean mIoU loss | One scene; single/multi camera-frame revocation at delays 1/2/4/8 | Active; broad exact-deletion prior exists |
| Q002 | Does long Occupancy memory retain sensor faults after input recovery? | ST-Occ measures long-history benefits but has no persistent-fault/post-recovery protocol | Faults lasting 1/4/8 frames leave at least 2–4 frames of measurable aftereffect; full masked replay beats reset/skip | 30–50 paired nuScenes episodes, three fault families and scene bootstrap | Active; sensor-memory contamination literature must be checked |
| Q003 | Can dynamic motion evidence remain revocable after it changes future sampling? | ST-Occ predicted flow changes later attention locations | Separate trusted ego transport and revocable motion statistics retain exact deletion with <1.0 dynamic-class IoU loss | no/GT/predicted/revocable flow variants with dynamic-class CFGap | Active; requires dynamic-map collision search |
| Q004 | Can temporal consistency distinguish stable correctness from sticky error? | mSTCV measures changes and uses GT correction, not counterfactual equality | A sticky-memory control improves flicker while worsening CFGap; exact repair improves both | native/freeze/reset/full-replay/revocable Pareto | Active |

## Retired questions

被已有工作覆盖、实验否定或失去价值的问题移到这里，并保留终止原因。
