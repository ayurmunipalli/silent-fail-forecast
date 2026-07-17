"""R-AUDIT — BLIND independent implementation of the spec-§3 censored likelihood.

S3b audit protocol, STEP 1 (blind). Implemented from model_spec.md §3 and the
LOCKED grid (hyperparam_grid.md §3 loss / §4 penalties) ALONE, on 2026-07-17,
BEFORE src/s3b_primary.py exists in the repo (structural blindness — git history
will show this file predates the audited code). I have NOT read A-MODEL's S3b
code, its checkpoints, or its log entries M6+.

PURPOSE: in STEP 2 (dispatched later) I obtain A-MODEL's persisted fixed
evaluation batch (indices, inputs, Y_obs, complaint counts, exposure, u, head
outputs F and p, p_bar, F(x) / F(x+δ) for the Ω₂ subsample, and the config
λ/μ₁/μ₂/u*) and reproduce each reported loss TERM with the functions below. Only
after that verdict do I read the code (STEP 3).

================================================================================
SPEC TEXT THIS IMPLEMENTS (verbatim anchors)
================================================================================
spec §3:  L = BCE(Y_obs, F·R)
             + λ · NLL of observed complaint counts under head p, at
               BUILDING-SEASON grain — complaint events vs confirmed-incident
               exposure per building-season
             + monotone/shape penalties per grid
          R = 1 − (1 − p)^u,  u capped at u*  (structural thinning link)
grid §3:  R = 1 − (1−p)^min(u, u*); NLL = "binomial likelihood of observed
          distinct complaint events against confirmed-incident exposure at
          building-season grain on complaint-positive building-seasons";
          counts source = §2 311 union ONLY.
grid §4:  Ω₁ = μ₁ · mean_batch[(logit p_i − logit p̄)²], p̄ = train-fold pooled
               per-unit reporting rate (a constant);  μ₁ ∈ {0, .01, .1}
          Ω₂ = μ₂ · mean[max(0, F(x) − F(x+δ))²] over a per-batch subsample,
               δ = 0.5 SD on family-1 cumulative-count columns (post-standard.);
               μ₂ ∈ {0, .1, 1.0}.  R-in-u monotonicity is structural (no penalty).

================================================================================
AMBIGUITIES I HAD TO RESOLVE — the spec + grid UNDERDETERMINE these (a
checkability finding for Ayur at FREEZE regardless of whether A-MODEL and I
happen to agree). Each function below is PARAMETERIZED over the open axis so
STEP 2 can identify which choice reproduces A-MODEL's per-term value.

A. AUXILIARY-NLL SUCCESS PARAMETER θ (the central ambiguity).
   The grid calls it a binomial "under head p," but the building-level object is
   R = 1−(1−p)^min(u,u*). Two defensible readings:
     • θ = R  (PRIMARY here): a confirmed incident is "detected"/reported iff ≥1
       unit reports → building detection probability R. Internally coherent with
       "confirmed-incident exposure" as trials and the structural u-link.
     • θ = p  (ALTERNATIVE): literal "under head p" — each unit of exposure
       reported with the per-unit intensity p, u-link not used in the aux term.
   IMPLEMENTED: binomial_nll(theta, ...) takes θ directly; theta_from_p_u()
   builds either. Neither is uniquely spec-determined → FLAGGED.

B. TRIALS vs SUCCESSES, and k>n. Read as successes k = distinct complaint
   events, trials n = confirmed-incident exposure. But complaint multiplicity
   (the very signal identification-(i) invokes) routinely gives k>n, for which a
   Binomial(n,·) is undefined. Options exposed: clip_k=min(k,n) (PRIMARY, report
   clip rate) vs raw-k (flags k>n). This tension is itself the finding: a
   "duplicate-count" likelihood whose duplicates exceed the trial count is not
   reconstructible as a plain Binomial(n,·) from the text alone.

C. BINOMIAL COEFFICIENT. NLL with vs without the log C(n,k) term (constant in
   θ, so irrelevant to gradients but NOT to a reported scalar loss). Exposed via
   include_coeff; PRIMARY = False (drop the constant).

D. REDUCTIONS. BCE over ALL rows; NLL over complaint-positive rows ONLY; Ω over
   their row sets. mean vs sum for each is unspecified. PRIMARY = mean per term
   (grid fixes batch 8192, no class reweighting → per-sample mean is the natural
   reading). Exposed via `reduction`. λ multiplies the (reduced) NLL.

E. NUMERICAL. log/logit clamp ε. PRIMARY ε=1e-6. Tiny ε differences → ~1e-6
   scalar differences; STEP-2 reproduction tolerance set accordingly, not exact.

F. p̄, u, and the Ω₂ subsample selection are NOT defined by the spec as formulas;
   they are supplied by A-MODEL's persisted batch and taken as inputs here (I do
   not re-invent them). Their DEFINITIONS being outside the spec is noted.

If STEP 2 shows a term reproduces only under one specific (θ, clip, coeff,
reduction) combination that the spec did not pin down, the loss is
implementation-defined, not spec-defined — that is the reportable finding.
================================================================================
"""
from __future__ import annotations

import numpy as np

EPS = 1e-6  # ambiguity E


def _clip01(x):
    return np.clip(np.asarray(x, dtype=np.float64), EPS, 1.0 - EPS)


def logit(x):
    x = _clip01(x)
    return np.log(x) - np.log1p(-x)


def _reduce(v, reduction):
    v = np.asarray(v, dtype=np.float64)
    if reduction == "mean":
        return float(v.mean()) if v.size else 0.0
    if reduction == "sum":
        return float(v.sum())
    raise ValueError(reduction)


# ---- structural thinning link (spec §3 / grid §3): unambiguous ----
def R_link(p, u, u_star):
    """R = 1 − (1 − p)^min(u, u*).  p per-unit ∈(0,1); u units; u* cap."""
    p = _clip01(p)
    u_eff = np.minimum(np.asarray(u, dtype=np.float64), float(u_star))
    return 1.0 - np.power(1.0 - p, u_eff)


# ---- term 1: BCE(Y_obs, F·R) ----
def bce_term(F, R, Y, reduction="mean"):
    q = _clip01(np.asarray(F, dtype=np.float64) * np.asarray(R, dtype=np.float64))
    Y = np.asarray(Y, dtype=np.float64)
    per = -(Y * np.log(q) + (1.0 - Y) * np.log1p(-q))
    return _reduce(per, reduction)


# ---- term 2: auxiliary binomial NLL (parameterized over the open axes) ----
def binomial_nll(theta, k, n, mask=None, clip_k=True, include_coeff=False,
                 reduction="mean"):
    """NLL of counts k against exposure n under success prob θ, on the masked
    (complaint-positive) rows. θ is supplied already (=R or =p per ambiguity A)."""
    theta = _clip01(theta)
    k = np.asarray(k, dtype=np.float64)
    n = np.asarray(n, dtype=np.float64)
    if mask is None:
        mask = np.ones_like(k, dtype=bool)
    mask = np.asarray(mask, dtype=bool)
    th, kk, nn = theta[mask], k[mask], n[mask]
    if clip_k:                       # ambiguity B
        kk = np.minimum(kk, nn)
    per = -(kk * np.log(th) + (nn - kk) * np.log1p(-th))
    if include_coeff:                # ambiguity C
        from scipy.special import gammaln  # local: only if this variant is used
        per = per - (gammaln(nn + 1) - gammaln(kk + 1) - gammaln(nn - kk + 1))
    return _reduce(per, reduction)


def theta_from_p_u(p, u, u_star, kind="R"):
    """Build the binomial success prob per ambiguity A: 'R' = building detection
    via the u-link (PRIMARY); 'p' = per-unit intensity (ALTERNATIVE)."""
    if kind == "R":
        return R_link(p, u, u_star)
    if kind == "p":
        return _clip01(p)
    raise ValueError(kind)


# ---- penalties (grid §4) ----
def omega1(p, p_bar, mu1):
    """Ω₁ = μ₁ · mean_batch[(logit p_i − logit p̄)²].  p̄ supplied (ambiguity F)."""
    return float(mu1) * float(np.mean((logit(p) - logit(np.full_like(np.asarray(p, float), p_bar))) ** 2))


def omega2(F_x, F_xpert, mu2):
    """Ω₂ = μ₂ · mean[max(0, F(x) − F(x+δ))²] over the supplied subsample rows."""
    d = np.asarray(F_x, dtype=np.float64) - np.asarray(F_xpert, dtype=np.float64)
    return float(mu2) * float(np.mean(np.maximum(0.0, d) ** 2))


# ---- total (spec §3): L = BCE + λ·NLL + Ω₁ + Ω₂ ----
def total_loss(F, p, u, Y, k, n, p_bar, F_x, F_xpert, *, lam, mu1, mu2, u_star,
               theta_kind="R", clip_k=True, include_coeff=False, reduction="mean",
               cpos_mask=None):
    R = R_link(p, u, u_star)
    theta = theta_from_p_u(p, u, u_star, kind=theta_kind)
    terms = {
        "bce": bce_term(F, R, Y, reduction),
        "nll_raw": binomial_nll(theta, k, n, cpos_mask, clip_k, include_coeff, reduction),
        "omega1": omega1(p, p_bar, mu1),
        "omega2": omega2(F_x, F_xpert, mu2),
    }
    terms["lam_nll"] = float(lam) * terms["nll_raw"]
    terms["total"] = terms["bce"] + terms["lam_nll"] + terms["omega1"] + terms["omega2"]
    terms["_config"] = dict(lam=lam, mu1=mu1, mu2=mu2, u_star=u_star,
                            theta_kind=theta_kind, clip_k=clip_k,
                            include_coeff=include_coeff, reduction=reduction, eps=EPS)
    return terms


# ---- runnable self-test on SYNTHETIC values (proves the artifact executes;
#      uses no A-MODEL data — inputs are hand-made) ----
if __name__ == "__main__":
    rng = np.random.default_rng(0)
    N = 8
    F = rng.uniform(0.01, 0.5, N)
    p = rng.uniform(0.01, 0.4, N)
    u = np.array([2, 4, 6, 12, 25, 50, 80, 150], dtype=float)
    Y = np.array([0, 1, 0, 1, 0, 1, 0, 1], dtype=float)
    k = np.array([0, 3, 0, 5, 0, 2, 0, 9], dtype=float)   # distinct complaint events
    n = np.array([0, 2, 0, 4, 0, 3, 0, 6], dtype=float)   # confirmed-incident exposure
    cpos = k > 0                                          # complaint-positive rows
    p_bar = 0.08
    F_x = F.copy()
    F_xpert = F + rng.normal(0, 0.02, N)                  # perturbed-history F
    for kind in ("R", "p"):
        t = total_loss(F, p, u, Y, k, n, p_bar, F_x, F_xpert,
                       lam=1.0, mu1=0.1, mu2=0.1, u_star=50,
                       theta_kind=kind, cpos_mask=cpos)
        print(f"[theta={kind}] bce={t['bce']:.6f} nll_raw={t['nll_raw']:.6f} "
              f"lam_nll={t['lam_nll']:.6f} O1={t['omega1']:.6f} O2={t['omega2']:.6f} "
              f"total={t['total']:.6f}")
    print("self-test OK — artifact runs; STEP-2 will feed A-MODEL's persisted batch.")
