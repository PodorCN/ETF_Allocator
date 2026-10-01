# Turning Investment Signals into Active Weights under a Tracking-Error Risk Budget (vs. Black-Litterman and TE-constrained MVO)

Context for the reader: the target system is an ETF allocator with benchmark b = SAA risk-parity weights, and a TAA overlay a = w − b driven by momentum / value / macro / sentiment sector signals. Notation used throughout: N assets, Σ = N×N covariance of asset returns, σ_i = sqrt(Σ_ii), b = benchmark (SAA) weights, w = portfolio weights, a = w − b active weights (Σ a_i = 0 for a fully invested portfolio), TE(a) = sqrt(aᵀΣa) ex-ante tracking error, α = vector of expected active (residual) returns.

Note on sourcing: fetched primary/secondary sources are cited inline. Items marked **[derivation]** are standard algebra I derived from the cited formulas (verifiable by hand). Items marked **[background, unverified this session]** come from domain knowledge of well-known papers that I could not fetch/confirm in this session; treat with care and check before relying on exact details.

---

## Q1. Signal → alpha conversion (Grinold "Alpha = IC × Volatility × Score"), normalization, winsorizing, combining signals

### Takeaway
The standard, well-sourced recipe is: (1) turn each raw signal into a cross-sectional score with mean 0 / std 1 (ideally by rank-mapping to a standard normal, which also handles outliers), (2) scale to an expected return with α_i = IC × σ_i × z_i, and (3) combine several signals with weights proportional to Σ_IC⁻¹ · IC (IC-IR-optimal), which collapses to "IC-weighted" when signal ICs are uncorrelated and equally noisy.

### Cited Findings
- Grinold's rule: "Alpha = Volatility · IC · Score", where IC = correlation between forecast and subsequent return, Score = z-score of the signal, Volatility = std. dev. of the return being forecast; because scores have mean 0 / std 1, the alphas should have mean 0 and cross-sectional std ≈ Volatility·IC — [Zhipeng Yan, notes on Grinold & Kahn, Active Portfolio Management](https://people.brandeis.edu/~yanzp/Study%20Notes/Active%20Portfolio%20Management.pdf); original: Grinold, R. (1994) "Alpha Is Volatility Times IC Times Score," JPM 20(4):9–16 (reference list in [Shah, Northfield 2007](https://www.northinfo.com/Documents/247.pdf)).
- Derivation of the rule as a linear least-squares forecast: α(g) = E(y) + ρ(y,g)·std(y)·[g − E(g)]/std(g), i.e. "IC × volatility × score" — [Shah, "Alpha Scaling Revisited", Northfield 2007](https://www.northinfo.com/Documents/247.pdf).
- Worked example (per-security vol): DELL α = 0.10 × 27% × 1 = 2.7%; MSFT = 0.10 × 25% × 2 = 5.0%; PEP = 0.15 × 9% × 3 = 4.0% (different ICs per group) — [Shah 2007](https://www.northinfo.com/Documents/247.pdf).
- Cross-sectional version (forecasting return relative to the benchmark): α_k = IC × (cross-sectional volatility) × (cross-sectional score); cross-sectional variance ≈ Σ_s w_s σ_s² − σ_m² ("avg stock variance − variance of the market"), taken straight from the risk model — [Shah 2007](https://www.northinfo.com/Documents/247.pdf).
- Caveat: "Expect lower IC's for volatile securities (harder to predict)... Using a single IC exaggerates volatile securities' alphas"; IC can be estimated per group (same cap/industry/volatility) — [Shah 2007](https://www.northinfo.com/Documents/247.pdf).
- Robust preprocessing: "Map raw signals by rank onto standard normal e.g. 25th percentile → Φ⁻¹(.25)"; in the example the correlation between raw and reshaped values was 0.98 — [Shah 2007](https://www.northinfo.com/Documents/247.pdf).
- Adjustments for horizon and signal decay "are important, particularly in low-turnover portfolios" — [Shah 2007](https://www.northinfo.com/Documents/247.pdf).
- Multi-signal combination: for a composite of sub-factors with weight vector v, maximizing the composite's IC-IR gives v* ∝ Σ_IC⁻¹ · IC̄ (Σ_IC = covariance matrix of the sub-factors' IC time series; IC̄ = mean IC vector) — Sorensen, Qian, Hua et al. (2004), summarized in [Qian, Hua & Sorensen, Quantitative Equity Portfolio Management (preview)](https://api.pageplace.de/preview/DT0400.9781420010794_A38131426/preview-9781420010794_A38131426.pdf) and search summary of [Qian "Information Horizon, Portfolio Turnover, and Optimal Alpha Models", JPM 2007](http://gyanresearch.wdfiles.com/local--files/alpha/JPM_FA_07_Qian.pdf).
- Qian & Hua (2004): the standard deviation of IC over time (not just its mean) drives realized tracking error / realized IR in a multi-period setting — [ResearchGate: Active Risk and Information Ratio](https://www.researchgate.net/publication/228289309_Active_Risk_and_Information_Ratio).

### Inferences
- **[derivation] Recommended pipeline per rebalance date t, per signal k:**
  1. raw s_{k,i} → winsorize (e.g. clip at 1st/99th pct or ±3 MAD) *or* rank-map: z_{k,i} = Φ⁻¹((rank_i − 0.5)/N). With only ~10–30 sector ETFs rank-mapping is safer than z-scoring because one outlier dominates sample std at small N.
  2. re-standardize: z ← (z − mean)/std cross-sectionally (optionally demean within asset-class groups so a TAA sector signal doesn't produce an equity-vs-bond bet you didn't intend).
  3. α_{k,i} = IC_k · σ_i^{resid} · z_{k,i}, where σ_i^{resid} is the vol of the thing being forecast (sector return *relative* to the benchmark/peer group, not total vol).
  4. composite: α_i = Σ_k v_k α_{k,i}, with v = Σ_IC⁻¹ IC̄ / (1ᵀΣ_IC⁻¹ IC̄) (IC-IR-optimal), or simpler v_k ∝ IC̄_k / var(IC_k), or v_k ∝ IC̄_k (IC-weighted), or equal weights (robust default when IC history is short).
- For small cross-sections (sector ETFs, N≈10–20), per-period IC estimates are extremely noisy (SE of a correlation ≈ 1/sqrt(N−3) ≈ 0.25–0.33 per period), so IC-weighting should use long trailing windows and shrink toward equal weights. Typical TAA ICs are small (0.02–0.10), so absolute α magnitudes are small — this is fine because TE scaling (Q2) typically rescales the final bet anyway.
- Because the final TE scaling absorbs the overall level of α, the *common* IC multiplies out in most direct methods; only *relative* IC across signals/assets matters for weights. Getting σ_i and relative IC right matters more than the absolute IC.

### Gaps
- Could not fetch Grinold (1994) original; the formula is confirmed via two secondary sources.
- No sourced consensus found on winsorizing thresholds (±3σ vs ±2.5σ vs rank-mapping); practitioner choice.
- Sign-flip / regime-dependent IC (e.g., momentum crashes) handling not researched here.

---

## Q2. Signal → weight direct methods and TE scaling; risk contributions; budget allocation

### Takeaway
Three families: (a) **optimizer-implied** a ∝ Σ⁻¹α then scaled to target TE (this is exactly unconstrained TE-MVO); (b) **heuristic diagonal tilts** a_i ∝ z_i·(TE budget)/σ_i or rank tilts, then rescaled so sqrt(aᵀΣa) = TE* using the full Σ; (c) **active risk budgeting**, solving for a so each bet's Euler contribution to TE matches a target budget. Because TE is homogeneous of degree 1 in a, any direction can be scaled linearly to hit the TE target exactly (when unconstrained).

### Cited Findings
- Tracking error of portfolio x vs benchmark b: e = (x − b)ᵀR, σ(x|b) = sqrt((x − b)ᵀΣ(x − b)) — [Roncalli, Introduction to Risk Parity and Budgeting – solutions (arXiv:1403.1889)](https://arxiv.org/pdf/1403.1889); same definitions in Roll (1992) as summarized by [Harvey, Duke lecture notes on tracking error](https://people.duke.edu/~charvey/Classes/ba453/trackerr/trackerr.htm): G = (q_p − q_B)ᵀR = xᵀR, TEV = xᵀVx.
- TE optimization used by Roncalli: x* = argmax xᵀ(μ + ... ) − (γ-scaled) ½(x − b)ᵀΣ(x − b), written as the QP x* = argmin ½xᵀΣx − γ xᵀ(μ + Σb)/… (exact γ-placement garbled in extraction; structure is "maximize excess return minus ½·TE variance / risk tolerance") — [Roncalli solutions, §1.5–1.6](https://arxiv.org/pdf/1403.1889).
- Linear TE scaling: optimal portfolios at different TE levels satisfy x = b + ℓ(x₀ − b), with σ(x|b) = ℓ·σ(x₀|b), so "the leverage is the ratio of tracking error volatilities" ℓ = σ(x|b)/σ(x₀|b), and the information ratio is unchanged by ℓ (unconstrained case) — [Roncalli solutions, §1.6](https://arxiv.org/pdf/1403.1889).
- Numerical example with ERC benchmark (Roncalli exercise): TE target 1% → excess return 1.13%, IR 1.13; TE 10% → IR falls to 0.81 once long-only constraints bind — [Roncalli solutions, Table 1.3](https://arxiv.org/pdf/1403.1889). This is directly analogous to an "ERC SAA + active overlay" design.
- Risk contributions for volatility (Euler): RC_i = x_i (Σx)_i / sqrt(xᵀΣx), Σ RC_i = σ(x); ERC example output shows MR_i, RC_i = 3.52% each, 25% each for 4 assets — [Roncalli solutions, §1.6 ERC table](https://arxiv.org/pdf/1403.1889).
- In Roncalli's framework the benchmark can be the ERC portfolio, with active management done via TE optimization relative to it — [Roncalli solutions](https://arxiv.org/pdf/1403.1889); see also [Bruder & Roncalli, "Managing Risk Exposures using the Risk Budgeting Approach"](https://www.researchgate.net/publication/228206265_Managing_Risk_Exposures_Using_the_Risk_Budgeting_Approach) and [Roncalli, "Introducing Expected Returns into Risk Parity Portfolios"](http://www.thierry-roncalli.com/download/active-risk-parity.pdf) (could not fetch; TLS cert error).
- Generalized fundamental law: IR = TC × IC × sqrt(N); TC is "the correlation between the risk-adjusted expected returns and the risk-weighted active exposures" — [Clarke, de Silva & Sapra, JPM 2004, CFA Digest summary](https://www.hillsdaleinv.com/uploads/Toward_More_Information-Efficient_Portfolios,_Roger_G._Clarke,_Harindra_de_Silva,_Steven_Sapra,_The_Journal_of_Portfolio_Management,_Fall_2004,_Pages_54-63.pdf).

### Inferences (formulas for implementation)
- **[derivation] (a) Optimal unconstrained direction.** max αᵀa − (λ/2)aᵀΣa ⇒ a* = (1/λ)Σ⁻¹α. Choose λ to hit TE*: TE(a*) = sqrt(αᵀΣ⁻¹α)/λ ⇒ λ = sqrt(αᵀΣ⁻¹α)/TE*, so
  a* = TE* · Σ⁻¹α / sqrt(αᵀΣ⁻¹α),  expected active return = TE*·sqrt(αᵀΣ⁻¹α), IR* = sqrt(αᵀΣ⁻¹α).
  With a budget constraint 1ᵀa = 0 use the projected version a* ∝ Σ⁻¹(α − c·1), c = (1ᵀΣ⁻¹α)/(1ᵀΣ⁻¹1) (i.e. demean alphas in the Σ⁻¹ metric).
- **[derivation] (b) Diagonal / volatility-scaled tilt.** Assume Σ diagonal → a_i = (1/λ)α_i/σ_i² = (IC·z_i)/(λσ_i). So the "Grinold alpha + diagonal risk" portfolio is a_i ∝ z_i/σ_i — the vol-scaled tilt. The heuristic a_i = s_i × TE_i/σ_i is the same thing where TE_i is a per-bet stand-alone TE budget: stand-alone TE of position i is |a_i|σ_i = |s_i|·TE_i. Then rescale by the full Σ: a ← a · TE*/sqrt(aᵀΣa). (Before rescaling, impose 1ᵀa = 0 e.g. by subtracting a Σ-weighted or equal-weighted mean, or by funding from a "cash/benchmark" leg.)
- **[derivation] Rank-based tilt.** a_i ∝ (rank_i − (N+1)/2)/σ_i (or top-k long / bottom-k short with equal risk: a_i = ±c/σ_i), then rescale with full Σ. Robust to outliers and to mis-estimated IC; loses magnitude information.
- **[derivation] Euler decomposition of TE.** TE(a) = sqrt(aᵀΣa) is 1-homogeneous ⇒ TE = Σ_i a_i ∂TE/∂a_i, with MCTE_i = (Σa)_i/TE, ARC_i = a_i(Σa)_i/TE, Σ_i ARC_i = TE. Percent: ARC_i/TE. For signal-level (bet-level) attribution, write a = Σ_k a^{(k)} (one active vector per signal); RC_k = a^{(k)ᵀ}Σa / TE, Σ_k RC_k = TE. ARC_i can be negative (hedging bets), which is the main difference from long-only risk parity.
- **[derivation] (c) Active risk budgeting (target bet-level budgets β_k, Σβ_k = 1).** Keep the *direction* d_k of each signal's active vector fixed (e.g. d_k = Σ⁻¹α^{(k)} or d_k = z^{(k)}/σ) and solve for positive scalars θ_k in a = Σ_k θ_k d_k such that θ_k d_kᵀΣa / (aᵀΣa) = β_k. This is exactly a long-only risk-budgeting problem on the K "bet portfolios" with covariance C = DᵀΣD (D = [d_1..d_K]): because θ ≥ 0 and C is PSD, the standard Spinu/Roncalli convex formulation applies: min ½θᵀCθ − Σ_k β_k ln θ_k, then rescale θ to hit TE*. Existence/uniqueness hold as in ordinary long-only risk budgeting since θ_k > 0 (asset-level active weights may still be long/short). Asset-level active risk budgeting with signed a_i is harder: the RB system with signed weights can have multiple solutions (one per orthant; see Q3 Gaps) — so budgeting at the *bet/signal* level is cleaner than at the asset level.
  Fixed-point alternative (simple to code): θ_k ← θ_k · (β_k / (RC_k/TE))^{η}, η≈0.5, iterate, then rescale.
- **Budget allocation choices (β_k):** equal (1/K); IR- or IC-proportional; the IR-optimal allocation when bets are uncorrelated is β_k ∝ IR_k² (because optimal risk to bet k is TE_k ∝ IR_k and its contribution share with zero correlation is TE_k²/TE² ∝ IR_k²) **[derivation]**; conviction-proportional (|composite z| or signal agreement). With correlated bets, the IR-optimal budget is whatever falls out of a* = Σ⁻¹α (budgets are then an *output*, not input) — the Grinold/Kahn and Roncalli-style argument that risk budgeting = MVO when budgets are set to the MVO-implied contributions (see Q4).
- Given TE* target and a TC < 1 (long-only/caps), realized TE will be below target after constraints bind; practical fix is to iterate: solve constrained problem, measure TE, scale target up, repeat (or put the TE constraint inside the optimizer).

### Gaps
- Exact γ placement in Roncalli's TE QP was garbled in text extraction; the linear-leverage result (x = b + ℓ(x₀−b)) is clean.
- I did not find a single canonical paper for "a_i = s_i × TE_i/σ_i"; it is best described as a practitioner heuristic equivalent to diagonal-Σ MVO (derivation above).
- Did not verify Menchero & Hu "x-sigma-rho" active risk attribution (ARC_i = a_i σ_i ρ_i,a) from source [background, unverified this session] — algebraically identical to Euler: (Σa)_i/TE = σ_i ρ(r_i, active return).

---

## Q3. Handling correlated bets: clustering, orthogonalizing signals, factor budgets, Σ⁻¹ adjustment, shrinkage

### Takeaway
Diagonal tilts double-count correlated sector bets (e.g., momentum and macro both long cyclicals); the principled correction is Σ⁻¹ (which nets out correlated bets), but Σ⁻¹ is unstable with sample covariance, so it must be paired with shrinkage (Ledoit-Wolf), factor models, or clustering (HRP-style). At the signal level, IC-covariance weighting (Σ_IC⁻¹) or orthogonalization handles correlated signals.

### Cited Findings
- Multi-signal composite optimum v* ∝ Σ_IC⁻¹ IC — explicitly accounts for correlated signals via IC covariance — [Qian/Hua/Sorensen, QEPM](https://api.pageplace.de/preview/DT0400.9781420010794_A38131426/preview-9781420010794_A38131426.pdf); [search summary of Sorensen et al. 2004].
- The risk contribution of each asset "is affected by the risk contributions of all other assets due to their non-null correlations" — [Portfolio Optimizer blog, Effective Number of Bets](https://portfoliooptimizer.io/blog/the-effective-number-of-bets-measuring-portfolio-diversification/) (the blog also covers Meucci's effective number of bets via decorrelated/principal-component factors).
- ERC's popularity is partly because it is "relatively insensitive to small errors in the covariance matrix estimation, compared to alternative approaches" — [FTSE Global ERC Index white paper](https://research.ftserussell.com/products/downloads/FTSE_Global_Equal_Risk_Contribution_Index_Series_Whitepaper.pdf).
- Library support: skfolio optimizers (MeanRisk, RiskBudgeting) take a pluggable prior/covariance estimator (e.g., shrinkage, denoising) — [skfolio optimization user guide](https://skfolio.org/user_guide/optimization.html); PyPortfolioOpt BL uses a supplied covariance and He-Litterman Ω = τPΣPᵀ — [PyPortfolioOpt BL docs](https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html).

### Inferences
- **[derivation] Why Σ⁻¹ matters:** with two assets with correlation ρ, same σ, same α: a* ∝ Σ⁻¹α gives each position ∝ α/(σ²(1+ρ)) — correlated bets are shrunk by 1/(1+ρ); opposite-signed α on highly correlated assets gets *amplified* by 1/(1−ρ) → the classic unstable "long XLK / short XLC" pair. Hence: shrink Σ and cap active weights.
- **Ledoit-Wolf shrinkage [background, unverified this session]:** Σ̂ = δF + (1−δ)S, F = constant-correlation or scaled identity target, δ* chosen to minimize expected Frobenius loss (Ledoit & Wolf 2003/2004); available as `sklearn.covariance.LedoitWolf`, and in PyPortfolioOpt `risk_models.CovarianceShrinkage` and skfolio's `ShrunkCovariance`/`LedoitWolf` estimators.
- **Practical options, ordered by complexity:**
  1. Diagonal tilt + full-Σ TE rescaling (ignores correlation in direction, respects it in size).
  2. Σ_shrunk⁻¹ α (MVO direction) with active caps.
  3. Partial Σ⁻¹: a ∝ (κΣ + (1−κ)diag(Σ))⁻¹α, κ∈[0,1] interpolates between diagonal tilt (κ=0) and MVO (κ=1) — a common robustification **[derivation]**.
  4. Factor/cluster budgets: group sector ETFs (e.g., cyclicals/defensives/rate-sensitive via hierarchical clustering on correlation distance d = sqrt(½(1−ρ))), allocate TE budget per cluster, then within cluster use diagonal tilts.
  5. Orthogonalize signals before combining (regress sentiment on momentum; use residual) so the composite does not implicitly overweight the common component; or use Σ_IC⁻¹ weights.
- For ETF sector universes, the first principal component (market) usually dominates; a zero-sum active vector (1ᵀa = 0) with beta-neutrality (aᵀΣb ≈ 0 in beta units) removes much of the common-factor exposure, which is the concern Roll (1992) raised (see Q4).

### Gaps
- Could not fetch Ledoit-Wolf papers or HRP (López de Prado 2016) this session; their formulas above are background knowledge.
- No sourced evidence found comparing these correlation-handling choices specifically for sector-ETF TAA.

---

## Q4. Comparison: Black-Litterman (He-Litterman, Idzorek, Meucci) and MVO with TE constraint (Roll 1992, Jorion 2003); when they coincide with risk budgeting

### Takeaway
All three are, in the unconstrained Gaussian case, the same machine: BL produces a posterior μ_BL whose MVO weights equal the benchmark plus a Σ⁻¹-shaped tilt per view; TE-constrained MVO gives a = TE*·Σ⁻¹α/sqrt(αᵀΣ⁻¹α); and active risk budgeting reproduces MVO only if the budgets are set equal to the MVO-implied Euler contributions. They differ in how alpha is scaled (BL: via τ, Ω, confidence), and in what is held fixed (TE vs. confidence vs. risk shares). Roll/Jorion show pure TE-MVO is total-risk inefficient (beta > 1) and should be paired with beta or total-volatility constraints.

### Cited Findings
- **BL posterior:** E(R) = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹[(τΣ)⁻¹Π + PᵀΩ⁻¹Q]; prior Π = δΣw_mkt; δ = (R − R_f)/σ²; default τ = 0.05; He-Litterman default Ω = τ·PΣPᵀ (diagonal of it in the implementation); BL weights w = (δΣ)⁻¹E(R) — [PyPortfolioOpt Black-Litterman docs](https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html).
- **Idzorek:** user gives confidence 0–100% per view; method: compute the 100%-confidence BL return/weights for each view, derive the implied tilt vs. market weights, multiply by confidence to get the target tilt, and back out ω_k that produces it; ω = 0 ⇔ 100% confidence. PyPortfolioOpt implements a closed form via `omega="idzorek"` with `view_confidences` — [Idzorek, "A Step-by-Step Guide to the Black-Litterman Model" (Duke copy)](https://people.duke.edu/~charvey/Teaching/BA453_2006/Idzorek_onBL.pdf); [PyPortfolioOpt docs](https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html); [PyPortfolioOpt issue #95](https://github.com/robertmartin8/PyPortfolioOpt/issues/95).
- **Signals as BL views:** each row of P is a signal portfolio (e.g., momentum rank long/short), Q the expected spread, Ω diagonal certainty; BL assumes normal returns and views only on returns — [Newfound Research, "Combining Tactical Views with Black-Litterman and Entropy Pooling"](https://blog.thinknewfound.com/2017/07/combining-tactical-views-black-litterman-entropy-pooling/).
- **Meucci entropy pooling:** reweight equally-probable prior scenarios to satisfy views while minimizing relative entropy (KL divergence) to the prior; supports non-normal priors and views on ranks, vols, correlations, tails; generalizes BL — [Newfound Research](https://blog.thinknewfound.com/2017/07/combining-tactical-views-black-litterman-entropy-pooling/); [Meucci, "Fully Flexible Views: Theory and Practice" (Semantic Scholar)](https://www.semanticscholar.org/paper/Fully-Flexible-Views:-Theory-and-Practice-Meucci/62b8ff225c6eec3f83e00e69e830089e0beb1990); R implementation [PortfolioAnalytics::EntropyProg](https://search.r-project.org/CRAN/refmans/PortfolioAnalytics/html/EntropyProg.html). Rank views ("A will outperform B") are natural for ranking signals — [Newfound](https://blog.thinknewfound.com/2017/07/combining-tactical-views-black-litterman-entropy-pooling/).
- **Roll (1992), "A Mean-Variance Analysis of Tracking Error," JPM 18(4):13–22:** the TE-minimum-variance (TMV) frontier lies to the right of and nested inside the global efficient frontier; unconstrained TE optimization usually yields a managed portfolio with more market risk than the benchmark (beta > 1); Roll suggests constraining beta — [Harvey lecture notes](https://people.duke.edu/~charvey/Classes/ba453/trackerr/trackerr.htm); [search summaries incl. ResearchGate](https://www.researchgate.net/publication/323300185_Feasible_portfolios_under_tracking_error_b_a_and_utility_constraints).
- **Jorion (2003), FAJ 59(5):70–82, DOI 10.2469/faj.v59.n5.2565:** constant-TEV portfolios form an ellipse in mean/total-vol space; because the ellipse is flat, adding a constraint on total portfolio volatility can substantially improve the managed portfolio — [ResearchGate record](https://www.researchgate.net/publication/228183529_Portfolio_Optimization_with_Tracking-Error_Constraints); [Semantic Scholar](https://www.semanticscholar.org/paper/Portfolio-Optimization-with-Tracking-Error-Jorion/1d8c00f230a8fd860e82f658df567e78d1296c3d).
- Roncalli's exercise: max-IR TE portfolios are a line b + ℓ(x₀ − b); with long-only constraints IR declines as TE rises (1.13 at 1% TE → 0.81 at 10% TE) — [Roncalli solutions](https://arxiv.org/pdf/1403.1889).

### Inferences
- **[derivation] BL ⇒ active weights.** Unconstrained, w_BL = (δΣ)⁻¹μ_BL. Using Π = δΣb (benchmark as "market"): w_BL − b = (1/δ)Σ⁻¹(μ_BL − Π). With the standard identity, μ_BL − Π = τΣPᵀ(PτΣPᵀ + Ω)⁻¹(Q − PΠ), so
  a_BL = (τ/δ)·Pᵀ(τPΣPᵀ + Ω)⁻¹(Q − PΠ)  — the active vector is a linear combination of the view portfolios (rows of P), weighted by view surprise over view uncertainty. With He-Litterman Ω = diag(τPΣPᵀ) and one view, a_BL = (1/(2δ))·Pᵀ(Q − PΠ)/(PΣPᵀ): half the "100% confidence" tilt.
  → So BL with signal views ≈ "direct tilt along each signal portfolio, sized by signal strength/view variance", then (implicitly) scaled by δ. TE is *not* controlled directly; you must still rescale to TE* (or solve TE-constrained MVO with μ_BL).
- **Mapping Grinold alpha into BL:** set P = I (absolute views per asset) with Q − Π = α (Grinold alphas), Ω_ii = τσ_i²·(1−IC²)/IC² gives a posterior shrinkage consistent with a forecast of correlation IC **[derivation / background; check]**; or simply feed α directly into TE-MVO — the BL step is mostly useful when you want the *prior* to dominate weak or missing signals and to express relative (long/short) views.
- **When the methods coincide [derivation]:**
  1. TE-MVO (no other constraints) ≡ a* = TE*·Σ⁻¹α/sqrt(αᵀΣ⁻¹α).
  2. BL + unconstrained MVO + TE rescale ≡ (1) with α = μ_BL − Π.
  3. Active risk budgeting ≡ (1) iff budgets β_i = a*_i(Σa*)_i/(a*ᵀΣa*) = a*_i α_i /(a*ᵀα) (since Σa* ∝ α): i.e., the MVO-optimal risk budget of each bet is proportional to its expected contribution to active return ("risk budget ∝ alpha contribution"). This is the Grinold/Kahn-style result that at the optimum, marginal return / marginal risk is equal across bets. Equal risk budgets coincide with MVO only in special cases (e.g., uncorrelated bets with equal IR).
  4. Diagonal tilt a_i ∝ z_i/σ_i ≡ (1) iff Σ is diagonal (uncorrelated active returns) and IC is constant.
- **Implications for the design:** add a beta-to-benchmark constraint (|aᵀΣb/bᵀΣb| ≤ small) or a total-vol cap (wᵀΣw ≤ σ_b² or target vol) to the TE-MVO, per Roll/Jorion. In an SAA-risk-parity + sector-TAA design, a zero-sum within-equity overlay mostly addresses this, but TE optimizers will still favor high-beta sectors if alphas are not risk-neutralized.

### Gaps
- Could not fetch Roll (1992) or Jorion (2003) full text; closed-form expressions for Jorion's ellipse are not reproduced here.
- He & Litterman (1999) original not fetched; Ω = τPΣPᵀ attributed via PyPortfolioOpt docs.
- The Ω mapping from IC is my derivation-level suggestion, not sourced.

---

## Q5. Practical issues: active weight caps, long-only / budget constraints and TC loss, turnover, rebalancing, no-trade bands, covariance windows, vol targeting

### Takeaway
Constraints (especially long-only, which bites hard when benchmark weights are small) are the largest source of efficiency loss; TC is the right diagnostic. Transaction costs are best handled by partial trading toward an "aim" portfolio (Gârleanu-Pedersen) or no-trade bands; both reduce turnover with little IR loss when signals are slow (value, macro) and matter more for fast signals (sentiment, short momentum).

### Cited Findings
- TC evidence (S&P 500, 4% ex-ante TE, value signal, beta-neutral): TC = 0.332 with all constraints; relaxing industry/sector constraints → 0.347 / 0.34 / 0.422 (both); relaxing position limits → 0.298; relaxing market-cap constraint → 0.471; relaxing long-only → 0.678 — [Clarke, de Silva & Sapra 2004 (CFA Digest summary)](https://www.hillsdaleinv.com/uploads/Toward_More_Information-Efficient_Portfolios,_Roger_G._Clarke,_Harindra_de_Silva,_Steven_Sapra,_The_Journal_of_Portfolio_Management,_Fall_2004,_Pages_54-63.pdf).
- TC rises with TE up to an optimum then declines; low-TE portfolios maximize TC with modest shorting (110/10) and high-TE (> 3%) with more (150/50) — [same source](https://www.hillsdaleinv.com/uploads/Toward_More_Information-Efficient_Portfolios,_Roger_G._Clarke,_Harindra_de_Silva,_Steven_Sapra,_The_Journal_of_Portfolio_Management,_Fall_2004,_Pages_54-63.pdf).
- Clarke, de Silva & Thorley (2002) show TC falls more from the long-only constraint than from any other single restriction — [Lo & Patel, "130/30: The New Long-Only" (MIT)](https://web.mit.edu/Alo/www/Papers/13030.pdf); [ResearchGate: Portfolio Constraints and the Fundamental Law](https://www.researchgate.net/publication/228182902_Portfolio_Constraints_and_the_Fundamental_Law_of_Active_Management). Market-neutral construction achieved highest TC historically, 130/30 intermediate, long-only lowest — [MSCI, The Long and Short of Factor Indexing](https://www.msci.com/downloads/web/msci-com/research-and-insights/paper/the-long-and-short-of-factor-indexing-how-portfolio-construction-shapes-investment-outcomes/webp/The%20Long%20and%20Short%20of%20Factor%20Indexing.pdf).
- Gârleanu & Pedersen (2013, JF): optimal policy = "aim in front of the target" and "trade partially toward the current aim"; new portfolio = linear combination of current portfolio and an aim portfolio (weighted avg of current and expected future Markowitz portfolios); net Sharpe ~20% better than best static strategy in their application — [NBER w15205](https://www.nber.org/system/files/working_papers/w15205/w15205.pdf) (via search summary); [Wiley JF](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12080).
- Roncalli exercise: turnover is not an increasing function of TE in general (constrained case) — [Roncalli solutions, Fig. 1.10](https://arxiv.org/pdf/1403.1889).
- Library support for constraints: Riskfolio-Lib supports TE and turnover constraints, risk budgeting with constraints, inequality constraints on risk contributions (CVXPY-based) — [Riskfolio-Lib GitHub](https://github.com/dcajasn/Riskfolio-Lib), [docs](https://riskfolio-lib.readthedocs.io/en/latest/index.html); skfolio RiskBudgeting supports weight/budget/group constraints, transaction costs, L1/L2 regularization, turnover constraints, **tracking error constraints**, custom constraints and prior estimators; `BenchmarkTracker` minimizes risk of excess returns; `max_tracking_error` in MeanRisk — [skfolio user guide](https://skfolio.org/user_guide/optimization.html), [skfolio TE example](https://skfolio.org/auto_examples/mean_risk/plot_10_tracking_error.html), [BenchmarkTracker](https://skfolio.org/generated/skfolio.optimization.BenchmarkTracker.html).
- Evidence caution: Australian multi-sector managers "have been unable to deliver investors with superior returns through tactical asset allocation" — Gallagher et al., "Tactical Asset Allocation: Australian Evidence" (PDF retrieved in-session; publisher URL not captured — treat as secondary).

### Inferences (implementation recipe)
- **[derivation] Caps & long-only.** Constraint set: w = b + a ≥ 0 ⇒ a_i ≥ −b_i; |a_i| ≤ min(c_abs, c_rel·b_i) (e.g., c_abs = 3–5%, c_rel = 50–100% of SAA weight); 1ᵀa = 0; group limits (Σ_{i∈G} a_i within ±x%). With an SAA risk-parity benchmark, low-vol assets (bonds) have big b_i and high-vol sectors small b_i, so underweights in small sectors are truncated at −b_i → asymmetric, lower TC. Monitor TC_t = corr(Σ^{1/2}a, Σ^{-1/2}α) (risk-adjusted form, per Clarke-de Silva-Thorley definition cited above) each rebalance.
- **Solving with constraints:** convex QP (cvxpy): max αᵀa − κ‖a − a_prev‖₁ (costs) s.t. aᵀΣa ≤ TE*² (SOC), 1ᵀa = 0, −b ≤ a, |a| ≤ cap, optional |aᵀΣb| ≤ ε·bᵀΣb (beta), wᵀΣw ≤ σ_max² (Jorion). This is the recommended "reference" solver; heuristic tilts are then benchmarks to check it against.
- **Turnover control options:** (1) L1 cost term / turnover cap in the QP; (2) partial adjustment a_t = a_{t−1} + ϕ(a*_t − a_{t−1}), ϕ∈(0,1] (Gârleanu-Pedersen spirit; ϕ smaller for fast-decaying signals — actually G-P aim *ahead* for slow signals, so weight slow signals more in the aim); (3) signal smoothing (EMA of z-scores) before α; (4) no-trade bands: trade asset i only if |a*_i − a_{i,t−1}| > band_i, band ∝ sqrt(cost_i)·σ-related; trade to band edge, not to target.
- **Rebalancing frequency:** monthly is the natural cadence for momentum/value/macro sector signals; sentiment may warrant faster checks with bands. [background; no source fetched]
- **Covariance windows [background, unverified]:** common practice: EWMA with half-life ~ 60–126 trading days for vol, longer (1–3y) for correlations, shrink (Ledoit-Wolf) and use weekly returns to reduce asynchronous-close effects across global ETFs. Since TE is ex-ante, vol regime shifts change realized TE; re-scale the overlay each rebalance to TE* ("TE targeting"), optionally cap the scaling factor change.
- **Vol targeting:** apply at total-portfolio level (SAA scaled to target vol) separately from overlay TE targeting; with Jorion's total-vol constraint these can be done jointly in the QP.

### Gaps
- No sourced quantitative comparison of no-trade-band widths or rebalancing frequency for sector-ETF TAA found in this session.
- Could not verify covariance-window recommendations from a primary source.
- Grinold (2005) "Implementation efficiency" and Qian's 2007 turnover/alpha-horizon paper were not read in full.

---

## Q6. Open-source implementations supporting active risk budgeting

### Takeaway
No major Python library offers a turnkey "active (TE) risk budgeting on signals" routine; the practical path is (i) skfolio or Riskfolio-Lib for TE-constrained MVO / risk budgeting with constraints, (ii) PyPortfolioOpt for BL (He-Litterman / Idzorek), and (iii) a small custom cvxpy/Spinu solver for bet-level active risk budgeting (Q2c).

### Cited Findings
- **Riskfolio-Lib** (CVXPY + pandas): TE and turnover constraints, index-tracking examples, risk budgeting with constraints, inequality constraints on risk contributions for variance — [GitHub](https://github.com/dcajasn/Riskfolio-Lib); [docs](https://riskfolio-lib.readthedocs.io/en/latest/index.html); [constraints functions](https://riskfolio-lib.readthedocs.io/en/latest/constraints.html). TE support discussed in [issue #2](https://github.com/dcajasn/Riskfolio-Lib/issues/2).
- **skfolio** (scikit-learn API): `RiskBudgeting` with tracking-error constraints, turnover, costs, priors; `MeanRisk(max_tracking_error=...)`; `BenchmarkTracker` optimizing on excess returns (RMSE-type TE on returns) — [skfolio optimization](https://skfolio.org/user_guide/optimization.html); [TE example](https://skfolio.org/auto_examples/mean_risk/plot_10_tracking_error.html); [BenchmarkTracker](https://skfolio.org/generated/skfolio.optimization.BenchmarkTracker.html).
- **PyPortfolioOpt**: `BlackLittermanModel` (Ω default τPΣPᵀ, `omega="idzorek"` with `view_confidences`, τ default 0.05, `market_implied_prior_returns`, `market_implied_risk_aversion`, `bl_weights`) — [docs](https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html).
- **Meucci entropy pooling**: MATLAB "Fully Flexible Views and Stress-testing" — [MathWorks File Exchange](https://www.mathworks.com/matlabcentral/fileexchange/21307-fully-flexible-views-and-stress-testing); R `PortfolioAnalytics::EntropyProg` — [CRAN](https://search.r-project.org/CRAN/refmans/PortfolioAnalytics/html/EntropyProg.html).
- **optimalportfolios** (PyPI) appears in search results for TE-constrained / risk-budgeting portfolios — [PyPI](https://pypi.org/project/optimalportfolios/5.1.4/) (not inspected; capabilities unverified).
- **Roncalli**: book solutions (arXiv:1403.1889) include TE optimization with an ERC benchmark and risk-budgeting exercises — [arXiv](https://arxiv.org/pdf/1403.1889); Roncalli's site hosts papers ("active-risk-parity", "risk-budgeting") but was unreachable (TLS certificate mismatch) this session.
- Portfolio Optimizer (web API) provides TE computation and index-tracking portfolios — [blog](https://portfoliooptimizer.io/blog/index-tracking-reproducing-the-performance-of-a-financial-market-index-and-more/); [API docs](https://docs.portfoliooptimizer.io/index.html).

### Inferences
- Suggested minimal stack for this repo: numpy/pandas + `sklearn.covariance.LedoitWolf` for Σ; cvxpy for the reference TE-constrained QP; ~30 lines for the bet-level risk-budgeting solver (log-barrier on θ via cvxpy or Newton); PyPortfolioOpt only if BL views are needed. This avoids fitting a benchmark-relative problem into library APIs that assume long-only total-risk budgeting.
- Sanity tests to implement: (1) unconstrained TE-MVO output has TE exactly TE* and IR = sqrt(αᵀΣ⁻¹α); (2) Σ_i ARC_i = TE; (3) bet-level RB returns budgets within tolerance; (4) with diagonal Σ, MVO == vol-scaled tilt; (5) BL with Ω→∞ returns a = 0.

### Gaps
- Did not verify whether Riskfolio-Lib's risk-budgeting mode can target risk contributions of *active* weights (w − b) rather than total weights; its TE support is as a constraint. Same for skfolio `RiskBudgeting` (budgets appear to be on total risk, TE as a constraint).
- Did not locate an official public code repo from Roncalli for active risk budgeting.
