**RETROSPECTIVE AND NON-BLIND** — RP2 single_shot table, season 2025-26 (machine-generated).

| Model | AP | p@250 | zero-311 p@250 | any-311 p@250 |
|---|---|---|---|---|
| B0 | 0.2155 | 0.7360 | 0.0280 | 0.7360 |
| B1 | 0.2784 | 0.6320 | 0.0520 | 0.6320 |
| B2 | 0.2734 | 0.8000 | 0.0480 | 0.8000 |
| B3 | 0.4339 | 0.8480 | 0.1240 | 0.8480 |
| B4 | 0.4533 | 0.8560 | 0.1600 | 0.8560 |
| B5 | 0.4528 | 0.8640 | 0.1520 | 0.8640 |
| joint_q | 0.4408 | 0.8280 | 0.1160 | 0.8280 |
| joint_F | 0.4406 | 0.8280 | 0.1160 | 0.8280 |

Criterion-3-style (dual screen, W=30): 
- joint_F: realized n=35, T=-0.0022, sign-test p=0.9996, reject@.05=False (zeros dropped 1)
- B4: realized n=35, T=-0.0004, sign-test p=0.9552, reject@.05=False (zeros dropped 0)
- B5: realized n=35, T=-0.0004, sign-test p=0.9552, reject@.05=False (zeros dropped 0)
- sensitivity 311-only screen: n=36, joint T=-0.0023
