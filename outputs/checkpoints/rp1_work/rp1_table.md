**RETROSPECTIVE AND NON-BLIND** — RP1 pilot validation table (machine-generated — no hand transcription). Means over the 4 pilot folds v = 2021..2024.

| Model | mean AP | mean p@250 | mean zero-311 p@250 | mean any-311 p@250 |
|---|---|---|---|---|
| B0 | 0.1476 | 0.6210 | 0.0180 | 0.6200 |
| B1 | 0.2104 | 0.5550 | 0.0410 | 0.5600 |
| B2 | 0.1913 | 0.6360 | 0.0390 | 0.6430 |
| B3 | 0.3694 | 0.8260 | 0.1170 | 0.8260 |
| B4 | 0.3695 | 0.8050 | 0.0980 | 0.8050 |
| B5 | 0.3701 | 0.8020 | 0.0850 | 0.8020 |
| joint (q=F*R) | 0.3434 | 0.7250 | 0.0830 | 0.7390 |
| joint (F ranking) | 0.3433 | 0.7240 | 0.0830 | 0.7350 |

AP for the joint rows: q=F·R vs Y_obs (selection metric) and the F ranking respectively; p@250 columns use each row's own score.
B3 row: frozen booster, folds ≤2024 only; v∈{2021,2022,2023} in-sample (WFF training seasons); no season-2025 row scored in RP1.

| Seed | mean AP (F·R) | mean p@250 (F) | mean zero-311 p@250 (F) |
|---|---|---|---|
| 42 | 0.3434 | 0.7240 | 0.0830 |
| 43 | 0.3465 | 0.7660 | 0.0740 |
| 44 | 0.3283 | 0.6880 | 0.0770 |
| 45 | 0.3347 | 0.7100 | 0.0790 |
| 46 | 0.3299 | 0.7200 | 0.0770 |

Per-fold joint winner AP (F·R), v=2021..2024: 0.2231 / 0.3186 / 0.4087 / 0.4234
Per-fold B4 AP: 0.2849 / 0.3374 / 0.4169 / 0.4390
Per-fold B5 AP: 0.2846 / 0.3375 / 0.4187 / 0.4398
