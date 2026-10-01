# Academic Foundations of Active Risk (Tracking-Error) Budgeting

Scope: benchmark-relative (active) risk budgeting, meaning how tracking error (TE) is spread across bets, assets, asset classes or managers, and how signals become active weights. Total-risk parity comes in only where it connects.

Notation used throughout: benchmark weights b, portfolio weights w, active weights a = w − b, covariance Σ, alpha forecast α (expected active return), TE σ_A = sqrt(aᵀΣa), IR = α_P/σ_A, risk aversion λ.

Verification note: I checked the bibliographic details (authors, venue, volume and pages) against publisher, SSRN, RePEc or JSTOR landing pages wherever the links below allow. Formulas marked "(standard result)" are textbook derivations that I did not re-read in the primary text during this session, because most full texts (SSRN, T&F, PM-Research) returned 403 or paywalls. They are listed under Inferences where the primary text was not reached.

---

## Q1. Grinold & Kahn: Fundamental Law, alpha = IC × vol × score, optimal active weights, IR-proportional risk allocation; Grinold's "Implementation Efficiency" and "Signal Weighting"

### Takeaway
The Grinold/Kahn framework is the canonical engine for turning signals into active weights and TE budgets. It rests on three steps. (1) Scale signals into alphas with α = IC·ω·z. (2) Solve the unconstrained mean/active-variance problem, which gives a* = Σ⁻¹α/(2λ) (or /λ, depending on how the ½ is written). (3) The resulting IR = IC·√BR, and the optimal TE is σ* = IR/(2λ). When bets are independent, each bet's optimal TE is proportional to its own IR. Grinold's later papers (2005, 2010) extend this to constraints and costs through an "implementation efficiency" or transfer-coefficient measure, and to allocating risk across several signals.

### Cited Findings
- **Grinold, R.C. (1989). "The Fundamental Law of Active Management." *Journal of Portfolio Management* 15(3), Spring, 30–37.** Links IR, forecasting skill (IC) and breadth (N): IR = IC·√N. — [PM-Research](https://www.pm-research.com/content/iijpormgmt/15/3/30); [SciSpace](https://scispace.com/papers/the-fundamental-law-of-active-management-3sgb3bdt9p)
- The theory built on the fundamental law "culminated in" **Grinold, R.C. & Kahn, R.N. (2000). *Active Portfolio Management*, 2nd ed., McGraw-Hill** (1st ed. 1995). — [Zhou, JPM 2008 (PDF)](http://gyanresearch.wdfiles.com/local--files/alpha/JPM_SU_08_ZHOU.pdf); the edition and publisher are also given in the footnote of [Litterman 2004 (PDF)](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- **Grinold, R.C. (1994). "Alpha is Volatility Times IC Times Score." *JPM* 20(4), Summer, 9–16.** Introduced the rule for converting raw scores into alphas for optimizer input (α_i = ω_i · IC · z_i, where ω_i is residual volatility and z_i is a standardized score). — [PM-Research/IIJ](https://jpm.iijournals.com/content/20/4/9); [Semantic Scholar](https://www.semanticscholar.org/paper/Alpha-is-Volatility-Times-IC-Times-Score-Grinold/2a4f17ec623c0f299e52ada43065a9152449fefc). A practitioner follow-up is MSCI Barra, "Converting Scores into Alphas" (2010). — [MSCI PDF](https://www.msci.com/documents/10199/1645561/PI_Converting_Scores_Into_Alphas.pdf/7adf1f42-10aa-40eb-9e8c-ecc11eeba2d4); another is Shah (2007), "Alpha Scaling Revisited" (Northfield). — [Northfield PDF](https://www.northinfo.com/Documents/247.pdf)
- **Grinold, R.C. (2005). "Implementation Efficiency." *Financial Analysts Journal* 61(5), Sep/Oct, 52–64.** Addresses how constraints and implementation reduce the IR that can be realized from a signal; it belongs to the transfer-coefficient line of work. — [SSRN 827425](https://ssrn.com/abstract=827425) (abstract page returned 403; bibliographic data from search snippet)
- **Grinold, R.C. (2010). "Signal Weighting." *JPM* 36(4), Summer, 24–34.** "Signal weighting is the allocation of risk between several potential sources or themes"; it gives a portfolio-based approach to choosing signal weights when trading costs are present. — [PM-Research](https://www.pm-research.com/content/iijpormgmt/36/4/24); [ResearchGate](https://www.researchgate.net/publication/314314528_Signal_Weighting)
- The CFA curriculum reading "Analysis of Active Portfolio Management" breaks expected value added into skill (IC), portfolio structuring (TC), breadth (BR) and aggressiveness (tracking risk σ_A). — [CFA Institute](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/analysis-active-portfolio-management)

### Inferences
- (Standard result, Grinold & Kahn ch. 5/14.) Objective: max_a aᵀα − λ·aᵀΣa. First-order condition: a* = Σ⁻¹α/(2λ). Then IR* = sqrt(αᵀΣ⁻¹α), which is the "IR of the alpha set". The optimal TE is σ_A* = IR*/(2λ), and the optimal value added is IR*²/(4λ). The optimal active risk therefore rises linearly with IR, and the ratio of optimal alpha to optimal TE is a constant.
- (Standard result.) With N independent bets, Σ is diagonal with residual variances ω_i². Then a_i* = α_i/(2λω_i²), and the TE taken on bet i is |a_i*|·ω_i = |α_i/ω_i|/(2λ) = |IR_i|/(2λ). This gives the practical rule "TE_i ∝ IR_i" (per-bet information ratio). Total IR² = Σ IR_i², which is the fundamental law when every IR_i = IC.
- If α = IC·ω·z is substituted into a* with diagonal Σ, then a_i* = IC·z_i/(2λω_i). Active weights are proportional to the score divided by volatility, so each bet's TE contribution is proportional to IC·|z_i|. This is the "signal → active weight" conversion used in quant equity and TAA.
- Signal weighting (Grinold 2010): to combine K signals with per-signal IRs IR_k and correlation matrix C among signal portfolios, the optimal risk allocation across signals follows the same structure, TE-weights ∝ C⁻¹·IR. When signals are uncorrelated, this reduces to TE_k ∝ IR_k. I did not verify the exact formula in the paper, so treat it as the standard MVO logic applied to signal portfolios.

### Gaps
- I could not access the full texts of Grinold (2005) or Grinold (2010) because of paywalls. Their exact formulas (for example Grinold's definition of "implementation efficiency" and how he treats trading costs in signal weighting) are not verified here.
- I could not confirm from an accessible source whether the unconstrained "optimal active risk" formula in Grinold & Kahn is written with λ or 2λ. This depends on convention (G&K use U = α − λ_A·ω², which gives ω* = IR/(2λ_A)).

---

## Q2. Litterman "Hot Spots and Hedges" (1996) and Winkelmann's risk budgeting chapters

### Takeaway
Litterman (1996) introduced the marginal-contribution / risk-decomposition language: each position's contribution to risk equals its weight times its marginal risk, and these contributions add up to total risk. Litterman called the largest contributors "hot spots" and identified the best hedges and implied views. Winkelmann (2000; 2003 chapters in Litterman's *Modern Investment Management*) applied this at the total-fund level. Active risk budgets across asset classes and managers are set so that each manager's expected alpha is proportional to its marginal contribution to total-fund active risk (the optimality condition). Litterman (2004) used the same calculus to show that the typical pension fund's 50–200 bp active risk implies an aggregate IR of only about 0.01–0.06, which he called the "Active Risk Puzzle".

### Cited Findings
- **Litterman, R. (1996). "Hot Spots™ and Hedges." Goldman Sachs Risk Management Series, October 1996**; also reported as published in ***JPM* 22(5) (special issue, Dec 1996), 52–75**. — [EconBiz record](https://www.econbiz.de/Record/hot-spots-tm-and-hedges-litterman-robert/10007318928); date "Oct 1996" per the author bio in [Litterman 2004 PDF](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf). **Flag:** the JPM volume and pages come from a search-engine summary and were not checked on the publisher page.
- Litterman interpreted risk contribution through marginal analysis. The asset that adds a large risk increment to total risk is the "hot spot", and risk contribution = share × risk increment. — [Qian (2006) PDF, literature review](https://faculty.washington.edu/ezivot/econ589/ssrn-id684221.pdf); [Springer: "Generalized marginal risk"](https://link.springer.com/article/10.1057/jam.2010.30)
- Other Litterman/Winkelmann GS Risk Management Series papers: "Managing Market Exposure" (Jan 1996, with Winkelmann), "The Green Zone" (Mar 2000, with Longerstaey, Rosengarten, Winkelmann), "Estimating Covariance Matrices" (Jan 1998, with Winkelmann). — [Litterman 2004 PDF](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf); [GS Estimating Covariance Matrices PDF](http://www.andreisimonov.com/4106/pdf/GS_Estimating_covariance_matrices.pdf)
- **Winkelmann, K. (2000). "Risk Budgeting: Managing Active Risk at the Total Fund Level." In L. Rahl (ed.), *Risk Budgeting: A New Approach to Investing*, Risk Books, London.** — [PM-Research guide listing](https://guides.pm-research.com/content/iijspecial/2000/1/64)
- **Litterman, R. and the Quantitative Resources Group, GSAM (2003). *Modern Investment Management: An Equilibrium Approach*. Wiley.** Includes Winkelmann chapters on "Developing an Optimal Active Risk Budget" and related risk budgeting topics. — [Wiley](https://www.wiley.com/en-us/Modern+Investment+Management:+An+Equilibrium+Approach-p-9780471124108); chapter title via [search summary / NYU syllabus](https://pages.stern.nyu.edu/~aalford/syllabus.htm). **Flag:** the exact chapter numbering and title were not verified against the table of contents.
- **Litterman, R. (2004). "The Active Risk Puzzle: Implications for the Asset Management Industry." GSAM *Perspectives*, March 2004** (primary text read):
  - Many pension funds run 50–200 bp active risk against 8–12% total volatility. That allocation is optimal only if the aggregate active IR is 0.01–0.06. For example, at 12% total risk and a 4% equity premium, 50 bp of active risk is justified at IR = 0.010; at 8% total risk, 200 bp is justified at IR = 0.064.
  - Because active risk is roughly uncorrelated with market risk, "it adds very little to overall portfolio risk". Even small expected alpha should therefore, at the margin, lead to significant active risk allocations.
  - Litterman rejects the "two separate risk aversions" explanation (which he attributes to Grinold & Kahn 2000 and Waring & Siegel 2003) as "a convenient fiction". He points instead to career/peer risk (agency), and to the historical coupling of strategic asset allocation and active risk that portable alpha and derivatives now make it possible to break.
  - Source: [Litterman 2004 PDF](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)

### Inferences
- (Standard result.) Euler decomposition for TE: σ_A = Σ_i a_i·∂σ_A/∂a_i = Σ_i a_i(Σa)_i/σ_A. The marginal contribution to TE is MCTE_i = (Σa)_i/σ_A, and the risk contribution is RC_i = a_i·MCTE_i. Hot spots are the positions with large RC_i. The best hedge for position i is the change in a_i that minimizes σ_A.
- Litterman's footnote-5 calculus generalizes as follows. With market risk σ_M and market Sharpe ratio SR, adding uncorrelated active risk σ_A is optimal when IR/σ_A ≈ SR/σ_M·(…). In the simple uncorrelated case, the optimal ratio is σ_A*/σ_M* = IR/SR. His numbers fit this: 0.5%/12% × (4%/16%) ≈ 0.010.
- Winkelmann's optimality condition for an active risk budget (implied-views logic): at the optimum, α_i/MCTE_i is the same for every manager or asset class and equals the total-fund IR. The reverse direction gives the implied alpha of the current budget: α_implied = IR_total·(Σa)/σ_A.

### Gaps
- I could not access the full text of Winkelmann's 2003 chapter, so its exact numerical examples (for example GS's illustrative optimal manager TE budgets) are not included.
- I did not verify the JPM publication details of "Hot Spots and Hedges" on the publisher page.

---

## Q3. Sharpe (2002), "Budgeting and Monitoring Pension Fund Risk"

### Takeaway
Sharpe gives risk budgeting its mean-variance justification. In an optimal portfolio, each component's marginal risk is proportional to its expected excess return. A risk budget can therefore be read as a set of implied expected returns (reverse optimization). Monitoring then means spotting deviations of the actual marginal risks and implied views from their targets.

### Cited Findings
- **Sharpe, W.F. (2002). "Budgeting and Monitoring Pension Fund Risk." *Financial Analysts Journal* 58(5), Sep/Oct, 74–86.** — [CFA Institute RPC](https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/budgeting-and-monitoring-pension-fund-risk); [T&F DOI 10.2469/faj.v58.n5.2470](https://www.tandfonline.com/doi/abs/10.2469/faj.v58.n5.2470); [RePEc (pages 74–86)](https://ideas.repec.org/a/taf/ufajxx/v58y2002i5p74-86.html); [SSRN 377422](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=377422); working version on [Sharpe's site](https://web.stanford.edu/~wfsharpe/art/q2001/q2001.htm)
- The paper describes mean-variance procedures for setting target risk characteristics for the components of a pension portfolio and for monitoring deviations. Because manager returns are correlated, portfolio risk is not the sum of component risks, although expected returns do add. "The relationship between marginal risks and implied expected excess returns provides the economic rationale for the risk budgeting." It also covers liabilities, factor models, and aggregation/disaggregation. — [CFA Institute RPC abstract](https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/budgeting-and-monitoring-pension-fund-risk)

### Inferences
- Practical takeaway: a TE budget across managers is internally consistent only if the manager alphas it implies (α_i ∝ ∂σ_A/∂w_i) are ones the sponsor actually believes. Otherwise the budget is suboptimal. This is the same condition as Winkelmann's and the implied-premium result in Q7 (Roncalli).

### Gaps
- I did not reach Sharpe's full text (for example his pension-fund numerical example) in this session.

---

## Q4. Clarke, de Silva & Thorley (2002): the transfer coefficient, and later work on constraints

### Takeaway
Constraints (long-only, sector/country bounds, turnover) break the proportionality a ∝ Σ⁻¹α. Clarke, de Silva & Thorley (CdST) measure this with the transfer coefficient TC = corr(risk-adjusted active weights, risk-adjusted alphas), which gives the generalized law E[IR] = TC·IC·√N. Long-only constraints typically cut TC well below 1, so much of the TE budget is "spent" on noise rather than on signal.

### Cited Findings
- **Clarke, R., de Silva, H. & Thorley, S. (2002). "Portfolio Constraints and the Fundamental Law of Active Management." *Financial Analysts Journal* 58(5), Sep/Oct, 48–66.** Gives an ex-ante generalized fundamental law, plus an ex-post correlation decomposition of performance into the success of the return-prediction process and the "noise" caused by portfolio constraints. — [SSRN 290322](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=290322); [ResearchGate](https://www.researchgate.net/publication/228182902_Portfolio_Constraints_and_the_Fundamental_Law_of_Active_Management)
- TC captures the "leaking" of IR caused by construction constraints such as country/sector limits and long-only. These produce suboptimal weights and reduce the maximum IR that can be achieved. — [search summary of SSRN/secondary literature](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=290322). **Flag:** one search summary dated the TC to "FAJ 2000". The SSRN/FAJ record points to 2002 (58(5)), which I use here.
- Follow-up: **Clarke, R., de Silva, H. & Sapra, S. (2004). "Toward More Information-Efficient Portfolios." *JPM* Fall 2004, 54–63.** — [PDF (Hillsdale)](https://www.hillsdaleinv.com/uploads/Toward_More_Information-Efficient_Portfolios,_Roger_G._Clarke,_Harindra_de_Silva,_Steven_Sapra,_The_Journal_of_Portfolio_Management,_Fall_2004,_Pages_54-63.pdf)
- Related work on the dynamics of the fundamental law: Ding (2010), "The Fundamental Law of Active Management: Time Series Dynamics and Cross-Sectional Properties". — [SSRN](https://doi.org/10.2139/ssrn.1625834); Zhou (2008), "On the Fundamental Law of Active Portfolio Management" (JPM Summer 2008). — [PDF](http://gyanresearch.wdfiles.com/local--files/alpha/JPM_SU_08_ZHOU.pdf)
- The CFA curriculum puts TC into the value-added decomposition (IC, TC, BR, σ_A). — [CFA Institute](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/analysis-active-portfolio-management)

### Inferences
- (Standard result, CdST.) TC = corr(σ_i·a_i, α_i/σ_i) cross-sectionally. E[R_A] = TC·IC·√BR·σ_A, and the optimal TE under constraints is σ_A* = TC·IR*/(2λ). Constraints therefore lower both the IR and the optimal amount of active risk to take. For a TE budget, TC is the efficiency of the risk spent.
- Practical takeaway for an ETF/TAA allocator: build the unconstrained a* = Σ⁻¹α/(2λ) first, then measure TC after applying the long-only/bound constraints. A low TC means the TE budget should be cut or the constraints relaxed. It does not mean simply scaling up risk.

### Gaps
- The typical TC values reported by CdST (for example for long-only portfolios) were not verified from the primary text, because the SSRN page returned 403. I have deliberately left out specific numbers.

---

## Q5. Allocating TE across managers and asset classes: Waring et al. (2000), Waring & Siegel (2003), Baierl & Chen (2000), Berkelaar–Kobor–Tsumagari (2006), Berkelaar–Kobor–Kouwenberg

### Takeaway
Manager structure is itself a portfolio-optimization problem. Maximize total-fund alpha subject to total-fund active risk, with managers as assets described by (α_i, ω_i, ρ_ij) plus "misfit" risk against the policy benchmark. Because pure active risk is roughly uncorrelated with policy risk, the active-risk problem can be separated from the policy asset-mix problem. Optimal solutions tilt toward index and risk-controlled (enhanced) active funds and away from highly concentrated funds. Berkelaar et al. show that naive risk budgeting (equalizing or matching risk contributions without reference to alphas) is optimal only under the MVO implied-alpha condition, and they provide a global optimizer that uses fitted asset-class excess-return/TE frontiers.

### Cited Findings
- **Waring, M.B., Whitney, D., Pirone, J. & Castille, C. (2000). "Optimizing Manager Structure and Budgeting Manager Risk." *JPM* 26(3), Spring, 90–104.** Treats manager structure as portfolio construction: for a given risk budget, a single combination of managers maximizes risk-adjusted expected active return. Won the Bernstein-Fabozzi/Jacobs Levy award and is credited as the lead article on active risk budgeting. — [PM-Research JPM 26(3)](https://www.pm-research.com/content/iijpormgmt/26/3); [ProQuest](https://www.proquest.com/docview/195589993); [Barton Waring publications](http://www.bartonwaring.com/p/barton-warings-publications.html)
- **Waring, M.B. & Siegel, L.B. (2003). "The Dimensions of Active Management." *JPM* 29(3), Spring, 35–51.** Once market factors are removed, pure alpha remains, and its cost is active risk. The manager portfolio problem can be solved separately from the asset-mix problem because pure active risk is uncorrelated with policy risk. Optimal solutions emphasize index and risk-controlled active funds, give lighter weights to traditional active funds, almost nothing to highly concentrated funds, and include market-neutral long-short where shorting is allowed. — [PM-Research](https://jpm.pm-research.com/content/29/3/35); [ResearchGate](https://www.researchgate.net/publication/247905848_The_Dimensions_of_Active_Management)
  - Their argument for a higher risk aversion to active risk than to policy risk (active bets are "rewarded only conditionally on skill, and in a declining proportion to risk taken") is quoted and disputed in [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf).
  - **Flag:** I found no paper titled "Active risk budgeting in action" by Waring & Siegel. The relevant Waring papers are the two above.
- **Baierl, G.T. & Chen, P. (2000). "Choosing Managers and Funds." *JPM* 26(2), Winter, 47–53.** Selects portfolios of managers or mutual funds that implement a target asset allocation while maximizing alpha for each level of TE. Uses discrete optimization to meet minimum investment requirements, and uses Sharpe returns-based style analysis to estimate fund style weights, which controls misfit risk. — [PM-Research](https://www.pm-research.com/content/iijpormgmt/26/2/47)
- **Berkelaar, A.B., Kobor, A. & Tsumagari, M. (2006). "The Sense and Nonsense of Risk Budgeting." *FAJ* 62(5), Sep/Oct, 63–77.** — [SSRN 935149](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=935149); [JSTOR](https://www.jstor.org/stable/4480773); [T&F](https://www.tandfonline.com/doi/abs/10.2469/faj.v62.n5.4283). **Correction to the brief:** the co-author on this FAJ paper is Tsumagari, not Kouwenberg.
- **Berkelaar, A.B., Kobor, A. & Kouwenberg, R. (2006). "Advanced Risk Budgeting Techniques."** Book chapter in an Elsevier/Academic Press volume (ISBN prefix 978-0-12-088438-4, which I believe is M. Ong (ed.), *Risk Management: A Modern Perspective*, 2006; **not confirmed**, since ScienceDirect returned 403). — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/B978012088438450006X). The model, as described:
  - A structured global optimization budgets total-fund TE across asset classes or managers, maximizing total-fund expected excess return for a given total TE.
  - Asset-class and total TE are controlled only through the choice of managers with different active-risk profiles.
  - Each asset class's efficient frontier (expected excess return vs TE) is fitted to a functional form, and the optimal active risk per asset class is solved using those frontier functions as inputs.
  - Source: [ResearchGate/search summary](https://www.researchgate.net/scientific-contributions/Arjan-B-Berkelaar-3227269). **Flag:** description taken from secondary summaries.
- An alpha-beta risk budget result: when alpha and beta are uncorrelated, the optimal risk budget ratio equals the ratio of the information ratio to the Sharpe ratio. — [search summary, source paper not identified](https://www.pm-research.com/content/iijpormgmt/26/2/47). **Flag:** attribution unclear, but consistent with Litterman (2004) above.

### Inferences
- The unified rule across managers, with manager active returns having alphas α, residual risks ω and correlation ρ: capital or TE weights = Σ_A⁻¹α/(2λ), where Σ_A is the active-return covariance. With uncorrelated managers, manager i's TE contribution ∝ IR_i, so a manager with twice the IR gets twice the TE. With correlated managers, TE goes to managers whose alpha is diversifying.
- The "sense" in Berkelaar et al., consistent with Sharpe (2002): a risk budget is sensible when RC_i/σ_A matches α_i/α_P, meaning each contribution to TE equals its share of expected alpha. The "nonsense" is setting risk budgets (for example equal) without reference to alphas.

### Gaps
- I could not access the full texts of Berkelaar–Kobor–Tsumagari (2006) or the Kouwenberg chapter. Their exact functional forms (for example a concave α(TE) frontier) and empirical results are not verified.
- The exact title of the 2006 book that holds the Kouwenberg chapter is not confirmed.

---

## Q6. Roll (1992) and Jorion (2003): inefficiency of TE-constrained optimization

### Takeaway
Maximizing alpha for a given TE, with no control on total risk, produces portfolios that are mean-variance inefficient in absolute terms. Roll showed they lie on a frontier parallel to and to the right of the efficient frontier, carrying extra total risk and beta above 1. Jorion showed that fixed-TE portfolios form an ellipse in mean/total-variance space, and that adding a total-risk constraint (for example total volatility no higher than the benchmark's) recovers much of the inefficiency.

### Cited Findings
- **Roll, R. (1992). "A Mean/Variance Analysis of Tracking Error." *JPM* 18(4), Summer, 13–22.** First formal optimization framework for TE volatility as the variance of the portfolio-minus-benchmark return. — [Harvey course note on TE](https://people.duke.edu/~charvey/Classes/ba453/trackerr/trackerr.htm); [JEF citation](https://jefjournal.org.za/index.php/jef/article/view/566/1085). **Flag:** the issue number (4) comes from my own knowledge; volume 18 and pages 13–22 are confirmed by search.
- **Jorion, P. (2003). "Portfolio Optimization with Tracking-Error Constraints." *FAJ* 59(5), Sep/Oct, 70–82, DOI 10.2469/faj.v59.n5.2565.** Constant-TE portfolios form an ellipse in the mean–variance plane. Jorion recommends maximizing return subject to a TE constraint and total risk equal to the benchmark's. — [Semantic Scholar](https://www.semanticscholar.org/paper/Portfolio-Optimization-with-Tracking-Error-Jorion/1d8c00f230a8fd860e82f658df567e78d1296c3d)
- Extensions: Bajeux-Besnainou et al. (2011), "Portfolio Optimization under Tracking Error and Weights Constraints", *Journal of Financial Research*. — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/j.1475-6803.2011.01292.x); "Another Look at Portfolio Optimization Under Tracking-Error Constraints". — [ResearchGate](https://www.researchgate.net/publication/228317465_Another_Look_at_Portfolio_Optimization_Under_Tracking-Error_Constraints)
- Roncalli's tutorial solutions show there is "no equivalence between the Sharpe ratio ordering and the information ratio ordering". In his example the tangency portfolio has IR = −0.55 against the benchmark. — [Roncalli 2014, arXiv 1403.1889 (solutions to TR-RPB exercises), §1.5](https://arxiv.org/pdf/1403.1889)

### Inferences
- (Standard result, Roll.) The unconstrained TE-optimal active portfolio a* ∝ Σ⁻¹(μ − c·1) is fully invested (1ᵀa = 0). It is independent of the benchmark and typically has β_a ≠ 0, so the total portfolio w = b + a is inefficient unless b itself is efficient. Practical fixes: constrain the active beta to 0 (β_P = 1), or cap total volatility at the benchmark's (Jorion).
- For a TAA/ETF overlay whose benchmark is the SAA portfolio, this justifies adding a beta-neutral or total-vol constraint alongside the TE budget.

### Gaps
- I did not read the full texts of Roll and Jorion. Numerical results, such as how much of the inefficiency Jorion's constraint recovers, are not verified.

---

## Q7. Risk contribution interpretation and books: Qian (2006), Menchero & Hu (2006), Roncalli (2013), Lee (2000), Scherer (2002)

### Takeaway
Risk contributions, including TE contributions, have a financial meaning: they are expected contributions to loss (Qian). They also decompose as exposure × volatility × correlation (Menchero's x-σ-ρ). The textbooks (Lee for TAA, Scherer for budgeting active risk and multi-manager allocation, Roncalli for Euler allocation and implied premia) formalize the link between risk budgeting and MVO. A risk-budget portfolio is MVO-optimal exactly when each asset's (active) expected return equals SR (or IR) × its marginal risk.

### Cited Findings
- **Qian, E.E. (2006). "On the Financial Interpretation of Risk Contribution: Risk Budgets Do Add Up." *Journal of Investment Management* 4(4), Q4 2006.** Risk contribution (by standard deviation or VaR) is closely linked to expected contribution to losses, so risk budgeting can be viewed as loss budgeting. Cornish-Fisher is used for non-normal VaR contributions. — [SSRN 684221](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=684221); [PDF (UW)](https://faculty.washington.edu/ezivot/econ589/ssrn-id684221.pdf); [PanAgora PDF](https://www.panagora.com/assets/JOIM-On-the-Financial-Interpretation-of-Risk-Contribution.pdf)
- **Menchero, J. & Hu, J. (2006). "Portfolio Risk Attribution." *Journal of Performance Measurement* 10(3), Spring, 22–33.** Introduces the x-sigma-rho decomposition, RC_i = x_i·σ_i·ρ_{i,P}. — [Menchero PDF (TSG)](https://tsgperformance.com/wp-content/uploads/2021/11/Risk-Attribution-x-sigma-rho.pdf); follow-up: **Menchero, J. & Davis, B. (2011). "Risk Contribution Is Exposure Times Volatility Times Correlation: Decomposing Risk Using the X-Sigma-Rho Formula." *JPM*** (volume/issue not verified). — [Semantic Scholar](https://www.semanticscholar.org/paper/Risk-Contribution-Is-Exposure-Times-Volatility-Risk-Menchero-Davis/71ef3efc5dcbe190232d6d86615e5188e3eef49d/figure/1); MSCI application to alpha and beta risk attribution. — [MSCI/QWAFAFEW PDF](https://sanfrancisco.qwafafew.org/wp-content/uploads/sites/9/2017/01/Alpha-and-Beta-Risk-Attribution.pdf)
- **Roncalli, T. (2013). *Introduction to Risk Parity and Budgeting*. Chapman & Hall/CRC Financial Mathematics Series, 410 pp.** Covers Euler allocation, marginal risk, risk contributions, and the tracking-error / information-ratio optimization in ch. 1 (the TE problem is on TR-RPB p. 19). — [Author site](http://www.thierry-roncalli.com/RiskParityBook.html); [SSRN 2272973](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2272973)
  - From the solutions book (primary text read): for a portfolio x₀ believed to be optimal, the implied risk premium is π = λΣx₀ = SR(x₀|r)·Σx₀/√(x₀ᵀΣx₀). That is, **π_i = SR·MR_i**: "The implied risk premium of asset i is then a linear function of its marginal volatility and the proportionality factor is the Sharpe ratio of the portfolio." Also SR = Σx_iπ_i / ΣRC_i. — [arXiv 1403.1889, §1.8](https://arxiv.org/pdf/1403.1889)
  - The TE problem is x* = argmax xᵀ(μ + γΣb) − (γ/2)xᵀΣx (maximizing excess return minus TE variance). Long-only and bound constraints can make positive-IR portfolios infeasible. — [arXiv 1403.1889, §1.5](https://arxiv.org/pdf/1403.1889)
- Related: Bruder, B. & Roncalli, T. (2012). "Managing Risk Exposures Using the Risk Budgeting Approach." — [SSRN](https://doi.org/10.2139/ssrn.2009778); [MPRA](https://mpra.ub.uni-muenchen.de/37246/)
- **Lee, W. (2000). *Theory and Methodology of Tactical Asset Allocation*. Frank J. Fabozzi Associates / Wiley, 160 pp., ISBN 978-1-883249-72-4.** Analytical tools for TAA. Lee was then at Credit Suisse AM and previously at J.P. Morgan IM. — [Wiley](https://www.wiley.com/en-us/Theory+and+Methodology+of+Tactical+Asset+Allocation-p-x000228097); [Google Books](https://books.google.com/books/about/Theory_and_Methodology_of_Tactical_Asset.html?id=e2V1TvPITqAC)
- **Scherer, B. (2002). *Portfolio Construction and Risk Budgeting*. Risk Books** (later editions 2004, 2007, 2010, 2014). Covers "budgeting active risk", "multiple manager allocation", satellite investing, Bayesian methods and estimation-error heuristics. — [AbeBooks](https://www.abebooks.com/9781899332441/Portfolio-Construction-Risk-Budgeting-Scherer-1899332448/plp); [Open Library](https://openlibrary.org/books/OL9329572M/Portfolio_Construction_and_Risk_Budgeting)

### Inferences
- **When risk budgeting equals MVO.** Apply Roncalli's implied-premium result to active space: a TE-budget portfolio a with contributions RC_i is MVO-optimal if and only if α_i = IR_P·MCTE_i for all i, which is equivalent to α_i·a_i/α_P = RC_i/σ_A (the "alpha share = risk share" condition).
  - Special cases. (i) Uncorrelated bets: RC_i = a_i²ω_i²/σ_A, and optimality gives TE_i ∝ IR_i. (ii) Equal TE contributions (active "risk parity") are optimal only if all bets have equal IR and the correlation structure is uniform. This mirrors the total-risk result that ERC is MVO-optimal when Sharpe ratios are equal and correlations constant (Maillard-Roncalli-Teiletche 2010; not verified in this session).
- Qian's loss-contribution view supports communicating TE budgets to investment committees as "expected share of underperformance in a bad period".
- I could not confirm from an accessible TOC whether Lee (2000) contains an explicit active-risk-budgeting derivation. The frequently cited contribution is the treatment of TAA as a benchmark-relative bet: optimal TAA active weights ∝ Σ⁻¹ forecast, and the TAA IR depends on forecast correlation (IC) and breadth. This is my recollection, not verified.

### Gaps
- Roncalli's book chapter on risk budgeting with a benchmark ("active risk budgeting") was not read directly. Only the tutorial solutions were accessible, and they cover TE optimization and implied premia, not a dedicated active-RB chapter. **Flag:** I cannot confirm the book has a chapter titled "active risk budgeting".
- The contents of Lee (2000) and Scherer (2002) were not verified beyond publisher and bookseller descriptions.
- The volume and issue of Menchero & Davis (2011) were not verified.

---

## Q8. The optimal TE allocation rule and when risk budgeting equals MVO (synthesis)

### Takeaway
Every source above arrives at one rule. The optimal active weights are a* = Σ⁻¹α/(2λ). Each bet's (or manager's) contribution to TE then equals its share of total expected alpha, and every bet has the same ratio of marginal alpha to marginal TE (= IR_P). When bets are independent, this becomes TE_i ∝ IR_i. With correlation, allocate via Σ⁻¹, so diversifying bets receive more TE. Constraints reduce efficiency through TC. Pure TE-maximization ignores total risk (Roll/Jorion), and the choice of active-risk aversion is itself disputed (Waring & Siegel vs Litterman).

### Cited Findings
- Marginal risk ∝ implied expected excess return is the economic basis of risk budgeting. — [Sharpe 2002 abstract](https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/budgeting-and-monitoring-pension-fund-risk)
- Implied premium π_i = SR × MR_i, with SR = Σx_iπ_i/ΣRC_i. — [Roncalli arXiv 1403.1889 §1.8](https://arxiv.org/pdf/1403.1889)
- IR = IC·√N; generalized to TC·IC·√N. — [Grinold 1989](https://www.pm-research.com/content/iijpormgmt/15/3/30); [Clarke-de Silva-Thorley 2002](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=290322)
- For a given risk budget, a unique optimal manager combination maximizes risk-adjusted active return. — [Waring et al. 2000](https://www.pm-research.com/content/iijpormgmt/26/3)
- The optimal split between market risk and uncorrelated active risk depends on IR relative to the market Sharpe ratio. Typical 50–200 bp budgets imply IR of about 0.01–0.06. — [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- Signal weighting is risk allocation across themes. — [Grinold 2010](https://www.pm-research.com/content/iijpormgmt/36/4/24)

### Inferences
Derivations are my own, consistent with the sources above.
1. **General case.** max αᵀa − λaᵀΣa gives a* = Σ⁻¹α/(2λ). Contribution RC_i = a_i(Σa)_i/σ_A = a_iα_i/(2λσ_A), which is proportional to a_iα_i, the alpha contribution. So the **risk share equals the alpha share** at the optimum.
2. **Independent bets.** TE_i = |a_i|ω_i = IR_i/(2λ), so TE_i ∝ IR_i and σ_A = sqrt(Σ TE_i²).
   - Example: two uncorrelated sleeves with IR 0.5 and 0.25 and a total TE budget of 2%. Stand-alone TEs are in the ratio 2:1, giving 2%·2/√5 ≈ 1.79% and 0.89%.
   - Allocating TE equally instead gives total IR = (0.5 + 0.25)/√2 ≈ 0.53, versus √(0.5² + 0.25²) ≈ 0.56 at the optimum.
3. **Correlated bets.** Stand-alone TE vector ∝ C⁻¹·IR, where C is the correlation matrix of the unit-TE bet returns. Bets that are positively correlated with higher-IR bets get less TE, and they can even be shorted.
4. **Risk budgeting equals MVO** if and only if the chosen budgets b_i (shares of TE) satisfy b_i = a_iα_i/Σ_j a_jα_j. This is equivalent to α = IR_P·∂σ_A/∂a. Equal-risk-contribution active budgets are MVO-optimal only when IRs are equal and correlations uniform. Budgets proportional to IR are optimal only when bets are independent.
5. **Practical scaling.** Set the total TE target from σ_A* = TC·IR_P/(2λ), or pick it from the governance budget. Scale a* to hit it, then check TC after constraints and monitor implied alphas (Sharpe 2002) for drift.

### Gaps
- I did not find a single primary paper that states the "TE_i ∝ IR_i" rule verbatim with its conditions. It is the standard corollary of Grinold–Kahn and Winkelmann-style analysis. The citation for the explicit statement should be treated as Grinold & Kahn (2000), ch. 14–15 ("Portfolio Construction"/"Long/Short"), pending verification.
