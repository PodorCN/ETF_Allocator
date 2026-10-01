# Empirical Evidence on Risk-Budgeted TAA and Sector/ETF Rotation

Scope note: ~20 search/fetch calls. Several primary PDFs (Clarke-de Silva-Sapra 2004, Stangl et al. SSRN, Moskowitz-Grinblatt, Faff et al., Cranfield sector-rotation thesis, SSGA TAA-overlay note) could not be retrieved in readable form (403/404/binary), so some numbers come from abstracts or secondary summaries and are flagged. Items marked "[recalled, not re-verified]" are from background knowledge of the literature and should be checked before being quoted as fact.

## 1. Risk-based sizing vs equal/naive sizing of tactical tilts (vol-scaled momentum, TSMOM, vol-managed factors)

### Takeaway
In-sample, volatility scaling of momentum-type tilts is the most strongly supported risk-budgeting result: Sharpe roughly doubles and crash/drawdown risk falls sharply. But much of the headline TSMOM alpha comes from vol scaling (leverage) rather than the signal. The broader "vol-managed factor" claim (Moreira-Muir) weakens a lot out-of-sample and after costs. Momentum and the market factor are the partial exceptions.

### Cited Findings
- **Barroso & Santa-Clara (2015, JFE 116:111-120), "Momentum has its moments":** they scale the WML momentum factor by the inverse of its 6-month realized volatility (constant-vol target). Results:
  - Sharpe rises from 0.53 to 0.97.
  - Excess kurtosis falls from 18.24 to 2.68.
  - Skew improves from -2.47 to -0.42.
  - Max drawdown falls from -96.69% to -45.20% (US, long sample from 1927).
  - Sources: [Alpha Architect summary](https://alphaarchitect.com/risk-of-momentum-crashes/); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X14002566); [ResearchGate](https://www.researchgate.net/publication/256017573_Momentum_Has_Its_Moments)
- **Leverage caveat:** a follow-up GARP whitepaper studies how leverage constraints affect risk-managed momentum. The benefit depends partly on being able to lever up in calm periods, which matters for a long-only ETF book that cannot lever. — [GARP whitepaper](https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054xSXUAY.pdf)
- **Moskowitz, Ooi & Pedersen (2012, JFE), time-series momentum:** they find a large, significant TSMOM alpha in a diversified portfolio of international futures. Each position is scaled to constant ex-ante volatility (40% per instrument in the paper) [recalled, not re-verified]. — [Alpha Architect](https://alphaarchitect.com/time-series-momentum-theory-and-evidence/); [MOP paper](https://elmwealth.com/wp-content/uploads/2017/06/timeseriesmomentum.pdf)
- **Kim, Tse & Wald (2016, J. Financial Markets 30:103-124), "Time series momentum and volatility scaling":**
  - TSMOM monthly alpha falls from 1.27% with vol-scaled weights to 0.41% without vol scaling, which is below the 0.95% alpha of cross-sectional momentum.
  - Without vol scaling, TSMOM alpha is not significantly different from a vol-scaled passive long strategy.
  - Implication: the risk-budgeting step (vol-parity sizing), not the signal, drives much of the headline performance.
  - Sources: [ResearchGate](https://www.researchgate.net/publication/303846490_Time_series_momentum_and_volatility_scaling); [Scholars Portal](https://journals.scholarsportal.info/details/13864181/v30icomplete/103_tsmavs.xml&sub=all)
- **Moreira & Muir (2017, JF), vol-managed portfolios:** cutting factor exposure when volatility is high raises Sharpe ratios and alphas. — [DeMiguel et al. JF 2024 discussion](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13395)
- **Cederburg, O'Doherty, Wang & Yan (2020, JFE):**
  - Vol-managed strategies fail out-of-sample.
  - The Moreira-Muir spanning-regression weights use full-sample moments (look-ahead bias). Calibrating the scaling coefficient in real time leaves vol-managed portfolios underperforming.
  - Their sample covered 103 equity strategies, and they found no systematic out-of-sample improvement [count recalled, not re-verified].
  - Sources: [Xu 2024 CFR summary](https://cfr.ivo-welch.info/forthcoming/papers/xu2024improving.pdf); [DeMiguel et al.](https://lbsresearch.london.edu/id/eprint/3716/1/The%20Journal%20of%20Finance%20-%202024%20-%20DeMIGUEL%20-%20A%20Multifactor%20Perspective%20on%20Volatility%E2%80%90Managed%20Portfolios.pdf)
- **Barroso & Detzel (2021, JFE 140(3):744-767):**
  - After transaction costs, even with five cost-mitigation methods, vol management of common factors other than the market generally produces zero abnormal returns and significantly lower Sharpe ratios.
  - The vol-managed market portfolio stays profitable after costs.
  - Momentum is partly robust.
  - Sources: [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088828); [EconPapers](https://econpapers.repec.org/article/eeejfinec/v_3a140_3ay_3a2021_3ai_3a3_3ap_3a744-767.htm); [Xu 2024](https://cfr.ivo-welch.info/forthcoming/papers/xu2024improving.pdf)
- **DeMiguel, Martin-Utrera & Uppal (2024, JF), multifactor view:** a conditional multifactor vol-managed portfolio beats its unconditional counterpart out-of-sample and net of costs. The gain comes from managing volatility at the combined-portfolio level, not factor by factor. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13395)
- **Further skeptical evidence:** "The disappearing profitability of volatility-managed equity factors" (JFM 2023) and an international follow-up (JEF 2024) show that performance weakens in recent data and outside the US. — [ScienceDirect JFM](https://www.sciencedirect.com/science/article/abs/pii/S1386418123000551); [ScienceDirect JEF](https://www.sciencedirect.com/science/article/pii/S092753982400094X)

### Inferences
- For an ETF TAA/sector tilt engine, the evidence supports **cross-sectional risk normalization**: scaling each tilt by its asset's or active-bet volatility so that no single high-vol sector dominates TE. It also supports managing total active risk at the **portfolio level**, meaning a TE budget with a scalar on the combined tilt (the DeMiguel et al. result).
- It gives weaker support for aggressive **time-series vol timing** of individual signals: those gains are fragile out-of-sample, cost-sensitive and leverage-dependent.
- In a long-only ETF book the upward (levering) leg of vol targeting is capped, so expect only part of the Barroso/Santa-Clara gain. Most of what remains will show up as lower drawdowns, not higher mean returns.
- When a backtest compares "vol-scaled vs naive", check whether the naive version has the same average TE. Otherwise the comparison mixes risk-budget effects with leverage effects, which is the Kim-Tse-Wald lesson.

### Gaps
- I found no study that directly compares, in a head-to-head sector-ETF or TAA backtest, a TE-budgeted signal portfolio against naive signal weights, Black-Litterman and unconstrained MVO on IR, drawdown and turnover together. This comparison probably needs to be done in-house.
- Turnover numbers for vol-scaled vs naive momentum were not retrieved.

## 2. Sector rotation signals applied to sectors/sector ETFs

### Takeaway
Industry momentum is the best-documented sector signal academically, but simple sector-ETF momentum implementations since 1998 show weak, statistically fragile results. Business-cycle rotation adds little even with perfect foresight of cycle phases. Value is mainly a within-industry effect, not a between-sector one. Sentiment and flow evidence at the sector level is thin and inconsistent.

### Cited Findings

**Industry momentum**
- **Moskowitz & Grinblatt (1999, JF 54(4):1249-1290), "Do Industries Explain Momentum?":**
  - A strong industry momentum effect accounts for much of individual-stock momentum.
  - Buying past-winner and selling past-loser industries (6-12m formation, 1-12m holding) is highly profitable after controlling for size, B/M, stock momentum and microstructure effects.
  - Stock momentum is much weaker once industry momentum is controlled for.
  - Exact monthly spreads could not be retrieved this session (PDF link dead).
  - Sources: [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:4:p:1249-1290); [Blank Capital summary](https://blankcapitalresearch.com/learn/moskowitz-grinblatt-industry-momentum)

**Sector ETF momentum**
- **CXO Advisory test on the 9 SPDR sector ETFs (XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY), Dec 1998-Dec 2015:**
  - Setup: hold the single top 6-month-momentum ETF, rebalance monthly, 0.25% friction per trade.
  - CAGR 4.4% vs 6.2% for equal-weight sectors.
  - Sharpe 0.14 vs 0.12; with a 10-month SMA cash filter, 0.19.
  - Caveats: only 34 independent ranking intervals; the 6-month lookback was chosen from prior studies (data-snooping risk); results may depend on falling rates.
  - Sizing was naive: concentrated in one sector, no risk scaling.
  - Source: [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/simple-sector-etf-momentum-strategy-performance/)
- **Quantpedia, "Sectoral Intramonth Momentum Cycle" (9 SPDR sector ETFs + SPY, Dec 1998-Jun 2026):** the spread from trailing 252-day sector momentum is positive on the first trading day of the month, then sharply reverses on days 2-3. Execution timing matters for sector-ETF momentum. — [Quantpedia](https://quantpedia.com/sectoral-intramonth-momentum-cycle/)

**Business-cycle rotation**
- **Stangl, Jacobsen & Visaltanachoti (2009), "Sector Rotation over Business Cycles":**
  - Assuming perfect foresight of NBER cycle stages and conventional rotation rules, and ignoring transaction costs, sector rotation beats the market by at most 2.3% a year over 1948-2007.
  - In realistic settings, where cycle stages are not known in advance, the outperformance quickly disappears.
  - An alternative rotation strategy historically beat the market by about 7%, but that is an in-sample finding.
  - Their conclusion: the gains are unlikely to cover the difficulty of identifying the cycle stage.
  - Sources: [ResearchGate](https://www.researchgate.net/publication/228425439_Sector_rotation_over_business-cycles); [SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID1572888_code386377.pdf?abstractid=1467457&mirid=1); [CXO "Perfect Sector Rotation"](https://www.cxoadvisory.com/economic-indicators/perfect-sector-rotation/)
- **Fidelity business-cycle framework (practitioner, descriptive rather than a tested strategy):**
  - Early cycle: the market returned more than 20% a year since 1962, with interest-rate-sensitive and economically sensitive sectors leading.
  - Mid cycle: about 14% a year, with IT relatively best.
  - Recession: defensives (staples, utilities, health care, telecom) outperform.
  - Phase classification is judgment-based and made after the fact.
  - Source: [Fidelity Business Cycle Approach](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/fixed-income/Business_Cycle_Sector_Approach.pdf)

**Value in sectors**
- **Asness, Porter & Stevens (2000); Cohen & Polk (1998):**
  - Splitting B/M and other characteristics into within-industry and across-industry parts shows the value effect is mainly intra-industry.
  - Within-industry sorts earn comparable returns with lower volatility.
  - Intra-industry HML has a higher cash-flow beta and a higher average return than inter-industry HML.
  - This implies a weak sector-level (between-sector) value signal.
  - Sources: [AQR working paper](https://www.aqr.com/Insights/Research/Working-Paper/Predicting-Stock-Returns-Using-IndustryRelative-Firm-Characteristics); [Campbell et al. 2025 "What drives booms and busts in value"](https://campbell.scholars.harvard.edu/sites/g/files/omnuum5881/files/2025-05/Paper%20PDF%20(May%202025)_0.pdf)

**Cross-asset value + momentum (closest TAA analogue)**
- **Blitz & van Vliet (2008, JPM 35(1):23), "Global Tactical Cross-Asset Allocation," 12 asset classes, 1986-2007:**
  - A long top-quartile / short bottom-quartile portfolio on combined momentum and value earns about 12% a year (another summary reports ">9%").
  - They report that the result is stable over time, present out-of-sample, survives costs, and is not explained by beta or Fama-French/Carhart factors.
  - Sources: [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1079975); [JPM](https://jpm.pm-research.com/content/35/1/23); [CXO](https://www.cxoadvisory.com/value-premium/combined-value-momentum-tactical-asset-class-allocation/)

**Sentiment and flows**
- **Salhin, Sherif & Jones (2016), UK, 1985-2014, 5 sector groups, EC consumer and business confidence indices:**
  - Sentiment significantly affects returns at the aggregate level and for some sectors, dominated by Manufacturing.
  - Estimates across sectors are inconsistent.
  - Source: [RePEc](https://ideas.repec.org/p/hwe/cfidps/1602.html)
- **Sector ETF flows (Lawrence, SWER):**
  - Higher flows predict significantly higher next-month returns, not significant at 2-3 months.
  - Outflows are more predictive than inflows.
  - Small, single-study evidence.
  - Source: [Lawrence, Sector ETFs flow & return](https://swer.wtamu.edu/sites/default/files/Data/Lawrence.pdf)

**Mixed and multi-strategy studies**
- **MDPI JRFM 2026, TSX 60, 2000-2025, 72 sector-rotation variants:**
  - Headline: Sharpe 0.922 vs 0.624 for equal-weight buy-and-hold.
  - Testing 72 variants creates a serious multiple-testing risk.
  - Source: [MDPI](https://www.mdpi.com/1911-8074/19/1/70)
- **Another academic test:** the rotation strategy trailed the benchmark by 0.34% a year with higher volatility. — [Journal of Business](https://thejournalofbusiness.org/index.php/site/article/download/488/393/1470)

### Inferences
- **Realistic expectations:** a single-signal sector-ETF rotation on about 10-11 US sector ETFs probably has monthly cross-sectional ICs of roughly 0.02-0.08. This range is my inference; I found no sector-ETF-specific IC study.
- With only about 11 bets a month, the fundamental law (IR ≈ IC·√BR·TC) suggests IRs of about 0.2-0.5 before constraints. That is consistent with the weak Sharpe differences in the CXO test.
- **Signal combination** (value + momentum, as in Blitz-van Vliet) and **risk-scaled diversified sizing** look far more robust than concentrated "top-1 sector" implementations.
- Business-cycle signals should be treated as a modest, low-confidence tilt. Even perfect foresight gives only about 2.3% a year of gross outperformance.
- **Data-mining flags:**
  - Lookback choices are inherited from the stock-level literature.
  - The SPDR-era sample (since 1998) is short, with few independent observations.
  - Multi-variant studies (72 strategies) need to be deflated for multiple testing.
  - Turn-of-month timing effects can change results.

### Gaps
- No verified numbers for Moskowitz-Grinblatt's monthly spreads or t-stats (PDF unavailable).
- No verified ICs or IRs for sector-level value (e.g., sector P/E or P/B spreads) on ETFs.
- No robust sector-ETF studies of news or text sentiment were found.
- Stangl et al.'s exact sector lists and the "7%" alternative strategy details were not retrieved (SSRN 403).

## 3. Transfer coefficient losses from long-only constraints and caps

### Takeaway
Clarke, de Silva & Thorley show the long-only constraint is the single largest source of transfer-coefficient loss. It gets worse as the TE target rises, and in practice TCs of about 0.3-0.8 are typical. This means realized IR is often half or less of the unconstrained IC·√BR.

### Cited Findings
- **Clarke, de Silva & Thorley (2002, FAJ 58(5)):**
  - The paper adds the transfer coefficient to the fundamental law: IR = TC·IC·√BR.
  - Managers under typical constraints have TCs of about 0.3-0.8.
  - In a long-only portfolio, raising TE usually lowers TC, because the no-short constraint binds for more securities.
  - Sources: [CFA Institute](https://rpc.cfainstitute.org/en/research/financial-analysts-journal/2002/portfolio-constraints-and-the-fundamental-law-of-active-management); [T&F](https://www.tandfonline.com/doi/abs/10.2469/faj.v58.n5.2468); [ResearchGate](https://www.researchgate.net/publication/228182902_Portfolio_Constraints_and_the_Fundamental_Law_of_Active_Management)
- **Clarke, de Silva & Sapra (2004, JPM):**
  - They measure empirically how various constraints hurt information efficiency.
  - The long-only constraint is often the most costly. TC falls more from long-only than from any other single restriction, with the possible exception of tight turnover limits.
  - Market-neutral construction had the highest TC, 130/30 was in between, and long-only was lowest.
  - Sources: [Lo 130/30 paper citing these results](https://web.mit.edu/Alo/www/Papers/13030.pdf); [Clarke-de Silva-Sapra PDF](https://www.hillsdaleinv.com/uploads/Toward_More_Information-Efficient_Portfolios,_Roger_G._Clarke,_Harindra_de_Silva,_Steven_Sapra,_The_Journal_of_Portfolio_Management,_Fall_2004,_Pages_54-63.pdf)

### Inferences
- For a sector-ETF TAA book the "universe" is small (about 11 sectors) and benchmark weights are large (several above 10%). The long-only constraint therefore binds mainly on underweights of small sectors such as Materials, Utilities and Real Estate. Expected TC loss is moderate at low TE budgets (1-3%) but grows with TE, in line with CdST's result.
- Tight turnover limits are the next biggest TC killer. Prefer turnover penalties or no-trade bands over hard caps.
- Reporting ex-ante TC (the correlation between risk-adjusted signal and active weights) each rebalance is a cheap diagnostic.

### Gaps
- Exact TC values by constraint (e.g., long-only S&P 500 TC at a given TE) were not retrieved; the PDFs were unreadable. Commonly cited illustrations put long-only TC around 0.3-0.6, but that is not verified here.
- No TC studies specific to ETF/sector TAA with few assets were found.

## 4. Black-Litterman vs risk budgeting in TAA backtests

### Takeaway
There is little rigorous head-to-head empirical evidence. The theory shows BL and risk-budgeted active construction can be equivalent under some conditions. Practitioner and academic backtests generally favor both over unconstrained MVO, mainly because they are more stable and robust to bad views, not because of clearly higher IR.

### Cited Findings
- **CFA Digest summary (2013), "The Black-Litterman Model: A Risk Budgeting Perspective":** the expected returns produced by BL can also be obtained with a risk-budgeting approach to active portfolio construction, so the two frameworks are closely linked. — [CFA Institute Digest](https://rpc.cfainstitute.org/research/cfa-digest/2013/08/the-blacklitterman-model-a-risk-budgeting-perspective-digest-summary)
- **Practitioner use:** BL is preferred for TAA because the optimized portfolio is anchored to the current or strategic allocation. Empirical tests suggest BL improves risk-adjusted returns over passive strategies and over Markowitz. — [Global TAA using BL (academia.edu)](https://www.academia.edu/66943202/Global_tactical_asset_allocation_using_the_Black_Litterman_model)
- **Robo-advisor study (arXiv 1902.07449):** robust or risk-based alternatives show a better risk-reward trade-off than their BL counterparts and are more robust to incorrect investor views. — [arXiv](https://arxiv.org/pdf/1902.07449)
- **Roncalli (arXiv 1403.1889):** risk budgeting ignores expected returns, which gives stable, robust portfolios. — [arXiv](https://arxiv.org/pdf/1403.1889)
- **Pomorski walk-forward TAA with ML views + BL:** beats passive benchmarks with comparable or lower risk. The author warns that backtests flatter everything and live results will be worse. Blog, not peer-reviewed. — [Substack](https://piotrpomorski.substack.com/p/tactical-asset-allocation-with-ml)

### Inferences
- Treat BL (with a TE-calibrated τ and view confidences) and TE-budgeted signal tilts as close substitutes. The practical differences are in calibration: BL's τ and Ω vs an explicit TE target and risk-contribution caps.
- Evidence consistently favors either one over unconstrained MVO on turnover and weight stability.
- Reasonable house evidence would be a walk-forward comparison using the same signals, TE and cost model.

### Gaps
- I found no peer-reviewed study that runs BL, risk-budgeted tilts and naive tilts on the same TAA or sector signals and reports IR, max drawdown and turnover. This is a clear literature gap.

## 5. Typical TE budgets in TAA and realized IRs of TAA programs

### Takeaway
Industry TAA overlays usually target IRs of 0.5-1.0 and need about 75-100 bp of gross alpha to justify their costs. Realized evidence from fund studies is mixed: TAA adds value in some asset classes and detracts in others.

### Cited Findings
- **Targets and hurdles (secondary summaries of SSGA's 2025 "Building a TAA overlay"; primary PDF returned 404):**
  - Tactical managers target IRs of 0.5-1.0 relative to the strategic baseline.
  - A TAA programme needs at least 75-100 bp of gross alpha to be worth running after costs.
  - Source: [SSGA PDF link (404 at fetch time)](https://www.ssga.com/ca/en/institutional/library-content/assets/pdf/global/mas/2025/building-a-taa-overlay.pdf)
- **Faff, Gallagher et al. (2005), Australian multi-sector funds:**
  - TAA returns were positive in 39 of 45 funds, and significant at 5% in 17 of them.
  - TAA in international shares and domestic fixed income generally destroyed value. Capital Stable funds' domestic-bond TAA averaged -0.027% a month, significant at 5%.
  - Source: [UNSW PDF](https://wwwdocs.fce.unsw.edu.au/banking/staff/profiles/dgallagher/Tactical_Asset_Allocation_19Jan2005_Final.pdf)
- **US DB pensions (J. Asset Management 2015), "How tactical should the plan be?":**
  - Limited tactical flexibility (bands) may help plans weather down markets.
  - Wider mandates should depend on proven manager TAA skill.
  - Source: [Springer](https://link.springer.com/article/10.1057/jam.2015.26)
- **Allspring (Wells Fargo) runs a dedicated TAA overlay strategy** (commercial example of overlay implementation). — [Allspring](https://www.allspringglobal.com/investments/equity/strategies/taa-overlay/)

### Inferences
- Combining the fundamental-law constraints above with the 75-100 bp alpha hurdle and IR targets of 0.5-1.0 implies overlay TE budgets of roughly 1-2%. A realistic IR of about 0.3-0.5 would need 2-3% TE to clear the hurdle.
- This is consistent with the 1-3% TE range in the brief, but I could not verify a published survey of TE budgets.
- Realized IRs of long-run TAA programs appear well below the 0.5-1.0 targets, based on the mixed fund evidence and the weak sector-rotation evidence above.

### Gaps
- No verified survey data on actual TE budgets or realized IRs across institutional TAA overlays; the SSGA primary document was unavailable.
- No US mutual-fund "tactical allocation" category performance study was retrieved. Such studies (e.g., Morningstar tactical-allocation category reviews) generally report underperformance, but that is not verified here.
