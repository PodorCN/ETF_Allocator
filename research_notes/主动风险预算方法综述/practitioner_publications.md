# Practitioner / Asset-Manager Publications on Active Risk Budgeting and TE Budgeting in TAA, Multi-Asset and Sector/ETF Rotation

Scope note: these notes cover primary documents that were fetched and read in full text: Amundi 2020 Blue Paper, GSAM/Litterman 2004, AQR 2014 and 2020, CalPERS 2020 board deck, NBIM 2000 submission, SSGA sector-rotation brochure, Wilshire's due-diligence note on BlackRock models, and Meketa 2024. Items marked "(snippet only)" were seen only through search results and were not read in full. Several named firms (JPMorgan, MSCI/RiskMetrics, Man, Robeco, PIMCO, Russell, WTW, Mercer, Northern Trust, Research Affiliates, Invesco) publish little concrete sizing methodology openly. They are listed under Gaps.

---

## Q1. Which firms publish risk-budgeting methodology, and what is the concrete method? (per-source catalogue)

### Takeaway
The most concrete public methodology comes from Amundi's 2020 "trade sizing" Blue Paper, Litterman/GSAM's active-risk papers and AQR's "Alternative Thinking" notes. Amundi gives a full two-stage process: an annual "planning-ahead" TE budget per alpha pillar, then per-trade sizing at the time of investing. GSAM supplies the equilibrium logic, where optimal active risk is proportional to the information ratio. AQR supplies TE numbers for TAA bands and a "forgone diversification" hurdle. Asset owners (NBIM, CalPERS) supply real-world TE ceilings and the risk models they use (Barra).

### Cited Findings

**Amundi. "Risk budgeting and trade sizing: why they matter to multi-asset portfolio construction". Investment Insights Blue Paper, September 2020. Authors: M. Germano, S. McDonald, M. Ortisi, E. Tazé-Bernard.** [Amundi PDF](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Framework: for a benchmark-relative portfolio, "the focus will be on budgeting the tracking error". An absolute-return portfolio instead budgets VaR and risk contribution. Risk budgets are "not defined as a cap on ex-ante risk" but as guidelines for the average level of risk over time. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- The paper explicitly invokes the Grinold–Kahn Fundamental Law. Its IR comes from skill plus the number of independent ideas, so a higher return target at fixed risk requires either more skill or more diversified ideas. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Risk is allocated across 4 pillars:
  - I. Macro Strategy: a few high-conviction, correlated trades tied to a central scenario.
  - II. Macro Hedging: budgeted as a *cost*, not as TE, maximising protection per unit of cost.
  - III. Satellite: many small, low-correlation relative-value trades.
  - IV. Selection: security, fund or factor baskets.
  - The three alpha pillars (I, III, IV) get a TE budget each. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- "Planning-ahead" (annual) stage inputs:
  - the average number of concurrent strategies
  - the average standalone risk per trade
  - the average correlation / target "Concentration Ratio"
  - The pillar TE budget is computed from these inputs. The pillar target return is then pillar TE × target IR.
  - Hypothetical table: Macro 5 trades × 0.40% standalone risk, avg corr 0.30 → pillar TE 1.10%, target ER 0.45%. Satellite 30 trades × 0.15%, corr 0.10 → TE 1.10%, ER 0.60%. Selection 16 trades × 0.10% → TE 1.05%, ER 0.60%. Portfolio TE 2.05%, target ER 1.10%, IR 0.54. My reconstruction of the garbled PDF table; values should be checked against the original figure. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- A "transfer coefficient" haircut applies: only about two-thirds of the pillar return targets are assumed to be captured at portfolio level. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Validation via hit ratio and win/loss: target return 1.10%, 51 strategies, 6-month average holding period and a 50% hit ratio together imply a required win/loss ratio of 1.22. Stop-loss and position management are meant to create that asymmetry. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Idea-flow arithmetic: a 4-month average horizon means about 90 ideas per year are needed to keep about 30 open at once. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- "Concentration Ratio" metric: 1 means one independent bet; 0 means uncorrelated strategies of equal standalone risk; a negative value signals hedging or inefficiency. It separates concentration caused by correlation from concentration caused by dispersion of sizes. Target a "risk skyline" spread evenly across strategies, with a chart comparing standalone risk to TE contribution per strategy. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- "At investing" trade size depends on (1) standalone risk in volatility units, (2) correlation with the rest of the book, and (3) a conviction level on a 1–4 scale (example: EM debt views on a −−/−/=/+/++ grid). The sizing is **heuristic, not optimisation**: pre-trade simulation of ex-ante TE impact, then adjust. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Regime overlay: a 0–100% market "risk score" averages 4 indicators (Mood On/Off, financial conditions, Cross-Asset Sentinels, US real monetary accelerator). It decides whether to accept a higher overall risk budget or larger trades. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Amundi also states that the TE budget institutional investors allow for TAA is often constrained to 150–200 bps. (snippet only; attributed in search to Amundi research) — [Amundi Research Center](https://research-center.amundi.com/article/articulating-asset-allocation-across-different-time-horizons)

**Goldman Sachs Asset Management. Bob Litterman, "The Active Risk Puzzle: Implications for the Asset Management Industry". GSAM Perspectives, March 2004.** [PDF (Duke course copy)](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- Because pure active risk is uncorrelated with market risk, it adds very little to total risk. Even small expected alpha should therefore justify significant active risk; the optimal active risk allocation is highly sensitive to the expected IR. — [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- Observed pension active-risk budgets are 50–200 bps against 8–12% total volatility. These budgets are optimal only if the aggregate IR is 0.01–0.06. Worked example: 50 bp active risk at 12% total risk with a 4% ERP implies IR 0.010; 200 bp at 8% implies IR 0.064. Market Sharpe is taken as roughly 0.2–0.3. — [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- The paper attributes the narrow range to career/peer risk, a "second risk aversion" to active risk. — [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- The author bio lists the GSAM risk-budgeting lineage:
  - "Managing Market Exposure" (Jan 1996, with Winkelmann)
  - "Hot Spots and Hedges" (Oct 1996)
  - "The Green Zone" (Mar 2000, with Longerstaey, Rosengarten, Winkelmann)
  - "Estimating Covariance Matrices" (1998)
  - *The Practice of Risk Management* (1998, GS Firmwide Risk with SBC Warburg Dillon Read)
  - *Modern Investment Management: An Equilibrium Approach* (2003)
  - "The Intuition Behind Black-Litterman Model Portfolios" (1999)
  - Black-Litterman is described as "a key tool in GSAM's asset allocation process". — [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- "Hot Spots and Hedges" was published in the Journal of Portfolio Management special issue (Oct 1996, pp. 52–75). *The Practice of Risk Management* covers hot-spots reports, best-replicating-portfolio reports and implied-view reports. (snippet only) — [Wikipedia: Robert Litterman](https://en.wikipedia.org/wiki/Robert_Litterman); [Amazon listing](https://www.amazon.com/Practice-Risk-Management-Euromoney-Books/dp/1855646277)
- *Modern Investment Management* (Litterman & GS Quantitative Resources Group, Wiley 2003) is the book-length treatment of equilibrium-based risk budgeting. It is available as a PDF on a university repository, but I did not read it in full. — [Wiley](https://www.wiley.com/en-us/Modern+Investment+Management:+An+Equilibrium+Approach-p-9780471124108)

**AQR. "Tactical Tilts and Forgone Diversification". Alternative Thinking, April 2014.** [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Alternative-Thinking/Tactical-Tilts-and-Foregone-Diversification.pdf)
- Setup: 2 assets, each with 10% vol and Sharpe 0.5. Three strategies are tested: "mild" tilts (average ±10%, maximum ±20%), "aggressive" tilts (average ±25%, maximum ±50%) and full switching.
- Each tactical portfolio equals the strategic portfolio plus a long/short overlay. The paper computes a **breakeven Sharpe ratio** for that overlay, i.e. the SR the tilts need just to match the strategic portfolio.
- The hurdle rises with tilt aggressiveness and with lower correlation between the assets. It is below 0.1 for correlated assets such as sectors or countries, and much higher for stock/bond tilts.
- For hit rates, an overlay SR of 0.2 (0.4) needs 52% (55%) monthly or 58% (66%) annual wins. — [AQR 2014](https://www.aqr.com/-/media/AQR/Documents/Insights/Alternative-Thinking/Tactical-Tilts-and-Foregone-Diversification.pdf)
- Conclusion: tactical tilts "are concentrated and often low-conviction bets and should be sized appropriately". Volatility targeting is treated as distinct from return-seeking timing. — [AQR 2014](https://www.aqr.com/-/media/AQR/Documents/Insights/Alternative-Thinking/Tactical-Tilts-and-Foregone-Diversification.pdf)

**AQR. "Was That Intentional? Ways to Improve Your Active Risk". Alternative Thinking 3Q 2020.** [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)
- Active risk splits into intentional risk (active management, TAA) and unintentional risk (rebalancing lags, common bets, currency hedging, etc.).
- Example: 0.2% expected alpha at 1% TE gives a 67% chance of beating the SAA over 5 years. Adding 1% of unintended TE (total 2%) cuts that to 59%. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)
- TAA TE depends on (1) the size of the over/underweight, (2) the volatilities of the assets and (3) their correlations. Lower correlation gives *higher* active risk.
- Hypothetical TE from tilting a 60/40 portfolio, by stock/bond correlation of −0.5 / 0 / +0.5:
  - conservative ±2.5% → about 0.5% / 0.4% / 0.3%
  - moderate ±5% → 1.0% / 0.8% / 0.7%
  - aggressive ±7.5% → 1.4% / 1.2% / 1.0%
  - These values are read off the chart. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)
- Most investors use weight bands but "rarely do they have an explicit TE budget" for TAA. AQR recommends converting bands into expected TE so TAA can be compared with manager active risk. The active risk implied by US public plans' asset-class deviations averages a little under 1%. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)
- Allocating across managers or sources:
  - Equal weight is appropriate when there is complete uncertainty about TE, returns and correlations.
  - "Allocate by TE" when the sources have similar IRs and predictable TEs.
  - Overweight the most diversifying sources if correlations are stable.
  - Two uncorrelated managers can cut TE more than four managers with 0.4 correlation. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)
- Currency: deviating from the benchmark hedge policy can "eat up a large amount of your active risk budget". In a USD example, fully hedging costs about 2.1% TE for roughly a 1% cut in total volatility. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)

**NBIM (Norges Bank Investment Management) / Government Pension Fund Global**
- Current mandate: manage so that expected relative volatility (ex-ante TE) does not exceed 1.25 pp. The limit was raised from 1.00 pp on 1 Feb 2016. NBIM interprets it as the return difference exceeding 1.25 pp in only about one year in three. Ex-ante TE was 0.37 pp at end-2025 versus 0.44 pp at end-2024. — [NBIM Annual Report 2025](https://www.nbim.no/contentassets/6db259ec684645ebbf171cacbe7cc7de/annual-report-2025.pdf); [NBIM risk management](https://www.nbim.no/en/investments/risk-management/)
- Historical submission "The limit on tracking error for the Petroleum Fund" (5 May 2000):
  - Recommended keeping the limit at 1.5 pp.
  - Ex-ante TE came from a **BARRA aggregate model** combining the equity and fixed-income models. It was computed weekly and at month-end, with a covariance matrix updated monthly and weighted towards recent data.
  - How the TE room was used: index mandates capped at 20 bp; a rebalancing buffer of 50–60 bp in volatile periods; active use of only about 25 bp on average through 1999. — [NBIM 2000 submission](https://www.nbim.no/en/news-and-insights/submissions-to-ministry/2000---1997/the-limit-on-tracking-error-for-the-petroleum-fund/)

**CalPERS. "Tracking Error as a Risk Management Tool". Investment Committee Agenda Item 8a, Attachment 1, November 2020.** [CalPERS PDF](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)
- Total Fund policy: target forecast annual TE of **1.5%**, including active asset allocation and all other active decisions. The Asset Allocation Program has its own target forecast TE of **0.75%** versus the policy benchmark. Both are measured with the "CalPERS Total Fund Risk Management System". — [CalPERS 2020](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)
- Example decomposition: SAA volatility 11.5% versus total-fund active risk of about 1.05% TE. The deck shows security-level contribution to TE (weights times marginal risk).
- Private assets are modelled with Barra's private equity model. The deck flags TE as unreliable for private assets (appraisal smoothing, poor data). The 150 bp total limit becomes a de facto constraint on raising private-asset allocations. — [CalPERS 2020](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)
- Proposals:
  - Move to an "Actionable TE" limit that excludes non-actionable private-asset noise. A risk-equivalent level would be about 100 bp.
  - Consider dropping the separate 75 bp allocation limit in favour of a single limit.
  - Add breach and short-term-departure language. — [CalPERS 2020](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)
- Segment-level TE budgets also exist, e.g. Global Fixed Income at 0–50 bp forecast TE plus weight and duration bands. — [CalPERS 2020](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)

**BlackRock. Target Allocation ETF model portfolios. Wilshire due-diligence note, July 2023.** [Wilshire/BlackRock PDF](https://static.fmgsuite.com/media/documents/eb9763d4-2694-40f3-a05d-9922b8597014.pdf)
- "Tracking error for the portfolios is expected to range between 100–200 bps with up to half of the tracking error budget driven by tactical asset allocation views." The models hold iShares ETFs plus 2% cash, and may add sector and factor ETFs and bond tilts tactically. BlackRock's Risk & Quantitative Analysis group adds a further layer of oversight. — [Wilshire 2023](https://static.fmgsuite.com/media/documents/eb9763d4-2694-40f3-a05d-9922b8597014.pdf)
- BlackRock's product page says the team uses Aladdin risk analytics and "over 30 market signals and indicators" to distil one view. Models rebalance quarterly or semi-annually, or on market events. No TE or sizing formula is disclosed there. — [BlackRock Target Allocation](https://www.blackrock.com/us/financial-professionals/investments/products/model-portfolios/target-allocation)

**Meketa Investment Group. "Risk budgeting primer". Whitepaper, October 2024 (F. Benham, C. Bebee).** [Meketa PDF](https://meketa.com/wp-content/uploads/2024/10/MEKETA_Risk-Budgeting-Primer.pdf)
- A consultant view. It separates total-risk budgeting (contribution to fund volatility) from "active risk budgeting" (contribution to TE versus benchmark). It says risk budgeting suits liquid asset classes best, and that active risk comes from both allocation and selection decisions. Passive TE is typically a few bp but can reach about 50 bp. — [Meketa 2024](https://meketa.com/wp-content/uploads/2024/10/MEKETA_Risk-Budgeting-Primer.pdf)

**MSCI / Barra (tooling)**
- Barra analytics (Aegis, Barra on FactSet) decompose active risk by factor and asset and report marginal contribution to active risk (MCAR). MSCI research published the "x-sigma-rho" decomposition (risk contribution = exposure × volatility × correlation) in the JPM. (snippet only) — [Barra Analytics on FactSet](https://www.msci.com/documents/10199/242721/Barra_Analytics_on_FactSet.pdf/ff81e4d0-a6a6-4b99-923d-35dc2161df1c); [Barra Aegis](https://www.msci.com/documents/10199/242721/Barra_Aegis_Portfolio_Mgr_and_Optimizer.pdf/37f3416e-ac3a-4e34-a7f3-09c90d51332e); [MSCI risk parity / correlation attribution](https://www.msci.com/documents/10199/36c8ed57-cfad-4d77-8d40-6cbcc107a778)
- NBIM (2000) and CalPERS (2020) both use Barra models for ex-ante TE, which is evidence of Barra's role as the industry-standard TE engine for asset owners. — [NBIM 2000](https://www.nbim.no/en/news-and-insights/submissions-to-ministry/2000---1997/the-limit-on-tracking-error-for-the-petroleum-fund/); [CalPERS 2020](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)

**Amundi / Roncalli (academic-practitioner risk budgeting)**
- Roncalli's risk-budgeting (RB) portfolio solves for weights whose risk contributions equal preset budgets b_i. Roncalli also proposes adding expected returns into risk parity, which is directly usable for "risk-budgeted tilts".
  - Relevant papers: Bruder & Roncalli, "Managing Risk Exposures using the Risk Budgeting Approach"; "Introducing Expected Returns into Risk Parity Portfolios"; Amundi WP-79-2019 "Constrained Risk Budgeting Portfolios".
  - (snippet only; PDFs not read) — [Bruder & Roncalli](http://www.thierry-roncalli.com/download/risk-budgeting.pdf); [Active risk parity](http://www.thierry-roncalli.com/download/active-risk-parity.pdf); [Amundi WP-79](https://research-center.amundi.com/files/nuxeo/dl/ceb6dcac-c7f5-45b6-aa30-9911644c1684)

**Russell Investments. Dynamic asset allocation (blog).**
- Russell uses a Cycle / Value / Sentiment (CVS) framework. Tactical views combine 5 inputs: strategic beliefs, asset-class teams, the strategist team, third-party managers, and quantitative CVS indicators. Positions must be "sized appropriately… avoiding too heavy a concentration of risk in a single position". No formula is given. (snippet only) — [Russell AU blog](https://russellinvestments.com/au/blog/dynamic-asset-allocation)

**J.P. Morgan Asset Management. Multi-Asset Solutions.**
- The public process: Long-Term Capital Market Assumptions set the strategic framework, then TAA is layered on "to seek uncorrelated alpha". A contingent-claims framework is one GTAA tool. No public TE-sizing formula was found. (snippet only) — [JPMAM Multi-Asset Solutions](https://am.jpmorgan.com/hk/en/asset-management/institutional/investment-strategies/multi-asset-solutions/); [JPMAM contingent claims case study](https://am.jpmorgan.com/us/en/asset-management/institutional/investment-strategies/multi-asset-solutions/how-a-contingent-claims-framework-can-strengthen-global-tactical-asset-allocation/)

### Inferences
- Across these sources there is one consistent industry template:
  1. Set a total TE budget. Asset owners use roughly 0.75–2% (NBIM 1.25%, CalPERS 1.5% total and 0.75% for allocation); TAA sleeves are typically about 1–2%.
  2. Split it across decision layers or pillars.
  3. Size individual tilts using standalone vol × conviction, adjusted for correlation.
  4. Verify the ex-ante total TE with a factor risk model (Barra/Aladdin).
  5. Monitor contributions for concentration.
- A consistent message (Amundi, AQR) is that tilt sizing should be heuristic or risk-parity-like rather than full mean-variance optimisation, because MVO gives concentrated, unstable active weights.

### Gaps
- *The Practice of Risk Management* (1998) and "Hot Spots and Hedges" (JPM 1996) are paywalled or print-only. Their exact formulas were not verified from the primary text here. The standard hot-spot definition (contribution = w_i × ∂σ/∂w_i, summing to total σ) is widely known but not cited from a fetched source.
- *Modern Investment Management* (2003) contains GSAM's chapters on risk budgeting and TAA. It was located but not read.

---

## Q2. How do firms map signal strength to position size (conviction scoring, vol-scaled tilts, TE per position caps)?

### Takeaway
The published practitioner approach is: **size ∝ conviction × (target risk / standalone vol)**, then adjust for correlation with the existing book and check ex-ante TE. Amundi uses discrete conviction levels (1–4, or −−…++) mapped onto a "typical standalone risk per trade". AQR frames the size limit as a breakeven-Sharpe / forgone-diversification hurdle. Explicit per-position TE caps appear mainly in asset-owner policies (weight bands, segment TE limits) rather than in manager papers.

### Cited Findings
- Amundi sizes each trade at the time of investing from three inputs: standalone risk in volatility units, correlation with the portfolio, and conviction level (the scale runs 1–4 and also depends on market conditions). The workflow is "typical standalone risk per trade → correlation check → conviction → actual trade size → check ex-ante impact on overall portfolio → adjust if necessary". — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Amundi's planning inputs set an *average* standalone risk per trade by pillar: Macro about 0.40%, Satellite about 0.15%, Selection about 0.10% (hypothetical). This works as a per-position risk unit, and conviction scales around it. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Amundi lets a market-regime risk score (0–100%) modulate the overall risk budget and trade sizes. In stress, higher volatility raises each trade's risk, but dislocations can justify taking more risk. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- AQR illustrates tilt sizes as weight bands: ±2.5% / ±5% / ±7.5% on a 60/40 portfolio, or average ±10% and ±25% tilts in a two-asset model. It maps these to TE and to the breakeven overlay Sharpe the tilts need. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en); [AQR 2014](https://www.aqr.com/-/media/AQR/Documents/Insights/Alternative-Thinking/Tactical-Tilts-and-Foregone-Diversification.pdf)
- AQR: "Investors tend to achieve better balanced portfolios if they make allocations in volatility units rather than dollars." (snippet only, attributed in search to AQR) — [AQR search result: Understanding Alternative Risk Premia](https://www.aqr.com/-/media/AQR/Documents/Whitepapers/Understand-Alternative-Risk-Premia.pdf)
- State Street's sector rotation model:
  - Signals: Valuation (forward E/P), Momentum (6-month average price / 12-month average price), Sentiment (earnings-revision diffusion) and Macro (change in GDP-growth forecast). Models also cover Quality.
  - These produce a sector ranking of expected returns. The ranking is reviewed qualitatively by the Investment Solutions Group (ISG) team, then turned into sector weights.
  - Sectors are adjusted 12–20 times a year using UCITS ETFs against MSCI World. — [SSGA Global Equity Sector Rotation Strategy (2025)](https://www.ssga.com/library-content/assets/pdf/emea/capabilities/sector-rotation-etf-model-portfolio.pdf)
- PIMCO states that tactical exposures "should be sized thoughtfully based on conviction and the potential risk/return trade-off". It also optimises factor portfolios under TE and liquidity constraints. (snippet only) — [PIMCO Asset Allocation Outlook](https://www.pimco.com/us/en/insights/balancing-act-building-resilient-portfolios-in-a-changing-landscape)

### Inferences
- A practical rule consistent with Amundi and AQR is: active weight_i = conviction_i (for example −2…+2) × (per-unit risk budget / σ_i), where σ_i is the vol of the asset *relative to the benchmark*. Then scale everything so the ex-ante TE (w'Σw) equals the target. For an ETF sector rotation, the SSGA-style composite signal rank or z-score would supply the conviction term.
- The AQR hurdle implies that sector and country tilts, which are highly correlated, need a much lower breakeven Sharpe than stock/bond tilts. So a sector-rotation sleeve can carry more weight deviation for the same forgone-diversification cost, but also generates *less* TE per unit of weight deviation.

### Gaps
- No manager publicly discloses an exact conviction-to-size function (for example, linear in z-score with a specific cap), except Amundi's qualitative 1–4 scale.
- No verified public document from Man Group, Robeco, Invesco or Research Affiliates gives TAA sizing formulas. Search results for these firms were generic product pages.

---

## Q3. How do firms handle correlations between tilts and aggregate them to a total TE target?

### Takeaway
Everyone aggregates with a covariance or factor model: the ex-ante TE is sqrt(w_a' Σ w_a), computed with Barra, Aladdin or proprietary systems. Diversification across tilts is managed explicitly: Amundi uses a Concentration Ratio and a risk skyline, AQR stresses that lower correlation between tilted assets raises TE, and CalPERS/NBIM set a single total-fund TE ceiling with a sub-limit for allocation.

### Cited Findings
- Amundi builds the portfolio TE from pillar TEs using "an estimated target diversification between the pillars". Its illustrative 3-year ex-ante correlation matrix between pillars is: Macro/Hedging −0.51, Macro/Satellite 0.22, Macro/Selection 0.27, Hedging/Satellite −0.35, Hedging/Selection −0.16, Satellite/Selection 0.20. With three pillar TEs of about 1.05–1.10%, the aggregate TE is about 2.05%, well below their sum. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Amundi warns that a strongly negative correlation between strategies may mean "paying twice for offsetting positions". A new trade gets a pre-trade check of its correlation to the major asset classes, to existing strategies and to the Macro pillar. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- Amundi does not assume independence when turning per-idea IR into pillar IR. It uses the Concentration Ratio instead, which amounts to a Fundamental-Law breadth adjustment for correlated bets. — [Amundi 2020](https://www.amundi.com/institutional/files/nuxeo/dl/dbca9fac-b275-4bfe-b211-4b99a3928b15)
- AQR: for TAA, lower correlation between the over- and underweighted assets means higher active risk. Highly correlated assets with very different volatilities (for example duration timing) can still generate meaningful TE. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)
- NBIM computes one ex-ante TE for the whole fund with the Barra aggregate model (equity and fixed-income sub-models plus 2-year daily FX data) and checks it against a single limit, 1.5 pp in 2000 and 1.25 pp now. — [NBIM 2000](https://www.nbim.no/en/news-and-insights/submissions-to-ministry/2000---1997/the-limit-on-tracking-error-for-the-petroleum-fund/); [NBIM AR 2025](https://www.nbim.no/contentassets/6db259ec684645ebbf171cacbe7cc7de/annual-report-2025.pdf)
- CalPERS runs a nested budget: 1.5% total-fund TE, of which active asset allocation is limited to 0.75%, plus segment-level TE ranges such as Fixed Income 0–50 bp. It is considering a single "Actionable TE" limit of about 100 bp. — [CalPERS 2020](https://www.calpers.ca.gov/sites/default/files/spf/docs/board-agendas/202011/invest/item08a-01_a.pdf)
- BlackRock's TA models allot "up to half" of a 100–200 bp TE budget to TAA views, with the rest going to fund and factor selection. Aladdin is used for the risk analytics. — [Wilshire 2023](https://static.fmgsuite.com/media/documents/eb9763d4-2694-40f3-a05d-9922b8597014.pdf)
- Litterman: pure active risk is uncorrelated with market risk, so its marginal contribution to total risk is near zero at low levels. That is why the TE budget can be optimised separately from SAA risk. — [Litterman 2004](https://people.duke.edu/~charvey/Teaching/BA453_2006/Litterman_active_risk_puzzle_full.pdf)
- AQR on managers: allocate by TE if IRs are similar, and overweight diversifying sources if correlations are stable. Diversification across uncorrelated active sources reduces aggregate TE more than adding more correlated sources. — [AQR 2020](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/Alt-Thinking-3Q20-92820.pdf?sc_lang=en)

### Inferences
- For an ETF allocator, a direct translation of this practice is:
  - Compute a benchmark-relative covariance Σ over the ETFs.
  - Define the active weights w_a from the signals.
  - Compute TE = sqrt(w_a' Σ w_a) and the per-tilt contributions RC_i = w_a,i (Σ w_a)_i / TE.
  - Scale w_a to hit the TE target.
  - Monitor a concentration metric, similar to Amundi's Concentration Ratio or an effective number of bets.
  - Optionally split the budget into sleeves (for example, SAA/TAA 50% and sector rotation 50%, mirroring BlackRock's "up to half").
  - Aggregate the sleeves using their cross-correlation.

### Gaps
- Amundi's exact formula for the Concentration Ratio is not given in the paper; only its interpretation is.
- BlackRock's and SSGA's exact aggregation or optimisation steps (for example, whether XLSR uses an optimiser with a TE constraint) are not disclosed publicly.

---

## Q4. Which sector rotation ETF products or notes describe risk-budget-based sizing?

### Takeaway
SSGA is the only large ETF sponsor found that states active-risk budgeting in a sector rotation product. XLSR (SPDR SSGA US Sector Rotation ETF) "dynamically adjusts active risk budgets relative to the benchmark". The quantitative limits (maximum over- or underweight, TE target) are not disclosed in the materials reviewed.

### Cited Findings
- XLSR:
  - Launched 2 April 2019 against the S&P 500 benchmark.
  - Objective: tactically allocate among GICS sectors of the S&P 500, combining quantitative and qualitative analysis, while dynamically adjusting active risk budgets relative to the benchmark.
  - A proprietary model forecasts sector returns from macro, financial and market data, and the weights seek to maximise expected return.
  - Typically rebalanced monthly; gross expense ratio 0.70%.
  - The fetched page showed YTD performance of 6.15% versus 13.14% for the S&P 500 as of 31 Aug 2026. — [SSGA XLSR page](https://www.ssga.com/us/en/intermediary/etfs/state-street-us-sector-rotation-etf-xlsr)
- The State Street Global Equity Sector Rotation Strategy (EMEA model portfolio, 2025):
  - Covers the 11 GICS sectors via UCITS ETFs against the MSCI World benchmark, adjusted 12–20 times a year.
  - Signals are valuation, momentum, sentiment and macro (plus quality).
  - The ranking goes through ISG qualitative review before becoming weights.
  - The brochure does not disclose a TE budget. — [SSGA brochure](https://www.ssga.com/library-content/assets/pdf/emea/capabilities/sector-rotation-etf-model-portfolio.pdf)
- A US version exists as an ETF model portfolio: the State Street US Equity Sector Rotation ETF Portfolio. (page not fetched) — [SSGA US model page](https://www.ssga.com/us/en/intermediary/capabilities/etf-model-portfolios/state-street-us-equity-sector-rotation-etf-portfolio)
- AQR: sector or country tilts forgo little diversification because sectors are highly correlated. A tactical investor with reliable forecasts is therefore more likely to add value there than in stock/bond tilts. — [AQR 2014](https://www.aqr.com/-/media/AQR/Documents/Insights/Alternative-Thinking/Tactical-Tilts-and-Foregone-Diversification.pdf)
- BlackRock TA models may add sector and factor ETFs tactically, within a 100–200 bp TE budget. — [Wilshire 2023](https://static.fmgsuite.com/media/documents/eb9763d4-2694-40f3-a05d-9922b8597014.pdf)

### Inferences
- XLSR's reported underperformance versus the S&P 500 (fetched page, 2026) is a reminder that a dynamic active-risk budget does not guarantee alpha. It is consistent with AQR's point that tactical bets need a real hit rate above about 52–55% monthly.
- For sector rotation, the TE per unit of active weight is small because sectors are highly correlated with the benchmark. Reaching a given TE budget (for example 2–4%) therefore needs fairly large sector overweights, so per-sector weight caps matter as much as the TE target.

### Gaps
- The XLSR prospectus/SAI was not read. It may contain maximum-deviation or TE constraints.
- No verified risk-budget methodology was found for Invesco (for example its sector rotation or DWA momentum ETFs) or other sector-rotation ETFs.
- WTW, Mercer, Northern Trust, Russell (beyond the CVS blog), Man Group, Robeco, PIMCO (beyond one sentence) and Research Affiliates: none of their fetched public pages had concrete TE-budget sizing methodology within this session's search budget. Some of these firms' research (for example Robeco quant, Man AHL) may exist behind client logins or in journals and was not verified.
