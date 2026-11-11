#!/usr/bin/env python3
"""Deterministic primary-source ledger for the be3c20e8 decision guide.

Every `quote` is copied from the page named in `url` during this session's
2026-11-11 re-read.  `reading` is a plain-language explanation, not a
translation or an official interpretation.  `figures` contains only values
printed by that publisher; model.py may derive arithmetic from them.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
READ = "2026-11-11"

S = []

def add(**kw):
    kw.setdefault("retrieved", READ)
    kw.setdefault("status", "read 2026-11-11")
    kw.setdefault("official", True)
    S.append(kw)

add(
    id="B01", title="中国银行外汇牌价 (BOC foreign-exchange board)", publisher="Bank of China",
    url="https://www.boc.cn/sourcedb/whpj/", source_class="bank primary",
    locator="USD row, 2026/11/11 20:39:19; website disclaimer paragraph 1",
    quote="美元 | 665.91 | 665.91 | 668.71 | 668.71 | 671.91 | 2026/11/11 | 20:39:19\n本汇率表单位为100外币换算人民币，仅供参考，客户办理结/购汇业务时，应以中国银行网上银行、手机银行、智能柜台或网点柜台实际交易汇率为准",
    reading="USD telegraphic-transfer buy, cash buy, telegraphic-transfer sell, cash sell and BOC conversion price, each per 100 USD. The board is for reference only; the rate actually offered in the transaction channel governs.",
    figures={"boc_buy_tt_per100": 665.91, "boc_buy_cash_per100": 665.91, "boc_sell_tt_per100": 668.71, "boc_sell_cash_per100": 668.71, "boc_conversion_per100": 671.91, "per": 100, "published_time": "20:39:19"},
    limits="Intraday board; not an executable quote. An earlier reading the same day was different; see F-04.",
)
add(
    id="B02", title="汇丰银行（中国）外汇汇率", publisher="HSBC Bank (China)",
    url="https://www.services.cn-banking.hsbc.com.cn/PublicContent/common/rate/zh/exchange-rates.html", source_class="bank primary",
    locator="USD row; page header last updated 2026年11月10日; disclaimer",
    quote="最后更新时间： 2026年11月10日\n美元 (USD) | 6.7030239 | 6.7030239 | 6.6362813 | 6.5997540\n请注意，以上汇率均为外币对人民币之汇率。汇率仅供参考，如有变更，恕不另行通知。",
    reading="CNY per 1 USD: cash/TT sell 6.7030239, TT buy 6.6362813, cash buy 6.5997540. Reference only and subject to change without notice.",
    figures={"hsbc_sell_cash": 6.7030239, "hsbc_sell_tt": 6.7030239, "hsbc_buy_tt": 6.6362813, "hsbc_buy_cash": 6.5997540, "board_date": "2026-11-10"},
    limits="Dated one day before the BOC reading; not an executable quote.",
)
add(
    id="B03", title="中国银行电子银行个人服务转账汇款费率表", publisher="Bank of China",
    url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", source_class="bank primary",
    locator="跨境汇款（电汇） row; 备注 1; effective date in table header",
    quote="跨境汇款（电汇） | 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。\n1、另有协议约定、价格优惠、地方性收费差异的，按照协议或当地公示的内容收取相关费用。\n收费标准2014年11月1日起",
    reading="Personal e-banking cross-border telegraphic transfer: 0.1% of the remittance, min CNY 50 and max CNY 260, plus CNY 150 cable charge outside Hong Kong, Macau and Taiwan. Separate agreements, promotions and local price differences may change the charge.",
    figures={"boc_tt_rate": 0.001, "boc_tt_min_cny": 50, "boc_tt_max_cny": 260, "boc_cable_other_cny": 150, "boc_cable_hmt_cny": 80, "effective_date": "2014-11-01"},
    limits="E-banking schedule only; the linked promotion page now returns a 404 (B31). A branch or another channel may differ; blank where unpublished.",
)
add(
    id="B04", title="Tariff of Accounts and Services for Wealth and Personal Banking Business (v2)", publisher="HSBC Bank (China)",
    url="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf", source_class="bank primary",
    locator="Cover; important notes 3 and 7; items 2.1.1, 2.2.2.1, 2.2.4.1, 2.2.4.2, 2.2.6.1, 2.2.6.2, 2.2.7, 2.2.16.7; embedded 2024 page headers",
    quote="(Effective from 31 Oct 2026)\nLast month’s Total Relationship Balance is not below the Premier Minimum Total Relationship Balance requirement, which is CNY 500,000 or equivalent;\nThe charges shown in this tariff do not include charges collected by other institutions ... or duties, levies, charges or taxes imposed by governmental or regulatory authorities.\nMonthly Service Fee | 2.1.1 | Not Applicable | CNY300 or equivalent* / month | Free\nTelegraphic Transfer Issuance | 2.2.4.1 | For individual customer: Free | 0.1% of remittance amount Min. CNY100 / equivalent per transaction Max. CNY500 / equivalent per transaction Plus Cable Charge | 0.1% of remittance amount Min. CNY100 / equivalent per transaction Max. CNY500 / equivalent per transaction Plus Cable Charge\nCable Charges | 2.2.4.2 | For individual customer: Free | CNY120 / equivalent per cable | CNY120 / equivalent per cable\nFund transfer to self-name HSBC accounts in other countries/ territories via HSBC Global Transfer | 2.2.6.1 | Free | Free | CNY145 * per transaction * This is an indication charge. The actual charge per transaction will be USD20 or equivalent in other foreign currency.\nFund transfer via the \"HSBC International Education Payment\" platform | 2.2.7 | Free | Free | CNY50 * per transaction * This is an indication charge. The actual charge per transaction will be USD7 or equivalent in other foreign currency.\nForeign Currency Notes Withdrawal Over Counter | 2.2.2.1 | Free | Free | Free\nATM cash withdrawals outside Mainland China (per transaction) | 2.2.16.7 | Free | Overseas HSBC Group ATMs: Free Overseas China UnionPay ATMs: CNY20/equivalent+ 1% of withdrawal amount Max. CNY110 / equivalent | Overseas HSBC Group ATMs: CNY20/equivalent+ 1% of withdrawal amount Max. CNY110 / equivalent Overseas China UnionPay ATMs: CNY20/equivalent+ 1% of withdrawal amount Max. CNY110 / equivalent\n财富管理及个人银行业务账户和服务费率（2024年9月12日生效）",
    reading="The current cover says 31 Oct 2026 but embedded table headers say 12 Sep 2024. Outward TT is free for Private Banking individual customers; Premier/Advance pay 0.1% min CNY100 max CNY500 plus CNY120 cable. Same-name Global Transfer is free for Private Banking/Premier and USD20 actual charge for Advance; USD7 belongs to education payments. Overseas UnionPay ATM withdrawals have CNY20 + 1%, capped at CNY110, for Premier/Advance. Foreign-currency notes withdrawal is free. The tariff excludes other institutions' charges and taxes.",
    figures={"hsbc_tt_rate": 0.001, "hsbc_tt_min_cny": 100, "hsbc_tt_max_cny": 500, "hsbc_cable_cny": 120, "hsbc_pb_entity_max_cny": 1000, "hsbc_pb_entity_cable_cny": 140, "hsbc_gt_advance_cny_indicative": 145, "hsbc_gt_advance_usd": 20, "hsbc_education_cny_indicative": 50, "hsbc_education_usd": 7, "hsbc_premier_monthly_cny": 300, "hsbc_premier_min_trb_cny": 500000, "hsbc_pay_exact_cny": 200, "hsbc_atm_fixed_cny": 20, "hsbc_atm_rate": 0.01, "hsbc_atm_max_cny": 110, "notes_reservation_usd": 5000},
    limits="Two different effective-date headers in one PDF; see F-06. Pay Exact CNY200 is not a cap on correspondent-bank shortfalls. Premier CNY300/month is excluded from per-transfer cost. U.S. receiving-side HSBC terms were not read here.",
)
add(
    id="B05", title="Guide to CNY transfers", publisher="Wise",
    url="https://wise.com/help/articles/2955298/guide-to-cny-transfers", source_class="provider primary",
    locator="Sending from CNY: who can send, who can receive, how much can I send, total sending limits, fees, arrival time",
    quote="You can send money from CNY if:\n- You're not mainland Chinese\n- You're working or have worked in China before\n- You have a valid tax record issued by the China tax authority showing taxes paid within the last 3 years\nDue to regulations, you can only send CNY from China to another account you own.\nIf you're sending CNY from your China bank app, the maximum you can send in one transfer is 300,000 CNY.\nIf you are sending CNY from Alipay, the maximum you can send in one transfer is 50,000 CNY.\nThe fees for transfers to CNY differ based on the delivery method ... Set up a transfer and add a recipient to see the exact fees for your transaction.\nYour annual income\nThe amount of tax you have paid in China\nThe number of years you've paid taxes on, proven through tax record(s) submitted.",
    reading="Outbound CNY through Wise is conditional on non-mainland status, past/current China work and a recent official tax record; it can go only to an account the sender owns. Per-transfer caps are published, but the exact fee, conversion rate and personal overall limit are not published on this page.",
    figures={"wise_bank_per_transfer_cny": 300000, "wise_alipay_per_transfer_cny": 50000, "wise_tax_record_years": 3, "wise_verification_days_min": 1, "wise_verification_days_max": 2, "wise_payin_days_max": 1, "wise_conversion_days_max": 2},
    limits="A commercial provider's help page, not a regulator. Exact fee/rate and personal overall limit blank; see F-08.",
)
add(
    id="B06", title="Foreign Exchange Rates - H.10 Weekly", publisher="Board of Governors of the Federal Reserve System",
    url="https://www.federalreserve.gov/releases/h10/current/", source_class="government",
    locator="Release of November 9, 2026; CHINA, P.R. YUAN row; last update",
    quote="Release Date: November 9, 2026\nCHINA, P.R. | YUAN | 6.6480 | 6.6701 | 6.6731 | 6.6680 | 6.6760\nLast Update: November 09, 2026",
    reading="Official weekly CNY-per-USD series; the latest daily column shown is Nov. 6, 2026 at 6.6760. It is not a same-day executable bank quote.",
    figures={"fed_nov2": 6.6480, "fed_nov3": 6.6701, "fed_nov4": 6.6731, "fed_nov5": 6.6680, "fed_nov6": 6.6760},
    limits="Latest release is dated before the 11 Nov bank boards; see F-19.",
)
add(
    id="B07", title="Yearly average currency exchange rates", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates", source_class="government",
    locator="Translating foreign currency into U.S. dollars; Currency exchange rates; China row",
    quote="In general, use the exchange rate prevailing (i.e., the spot rate) when you receive, pay or accrue the item.\nA taxpayer may also need to recognize foreign currency gain or loss on certain foreign currency transactions. See section 988 of the Internal Revenue Code and the regulations thereunder.\nThe Internal Revenue Service has no official exchange rate. Generally, it accepts any posted exchange rate that is used consistently.\nChina | Yuan | 7.129 | 7.189 | 7.075 | 6.730 | 6.452",
    reading="For U.S. tax translation, use the spot rate when the item is received/paid/accrued; the IRS has no official exchange rate and generally accepts a consistently used posted rate. Yearly averages for China are 7.129 (2025), 7.189 (2024), 7.075 (2023), 6.730 (2022), 6.452 (2021). Currency gain may need recognition under §988.",
    figures={"irs_2025": 7.129, "irs_2024": 7.189, "irs_2023": 7.075, "irs_2022": 6.730, "irs_2021": 6.452},
    limits="Yearly averages are not acquisition-basis evidence or an executable rate for an individual's CNY.",
)
add(
    id="B08", title="个人外汇管理办法实施细则 (汇发[2007]1号, as modified)", publisher="State Administration of Foreign Exchange",
    url="https://www.safe.gov.cn/safe/2007/0105/5320.html", source_class="government",
    locator="Articles 2, 3, 12, 13, 14, 15, 30, 31, 39 repeal note and Article 9 amendment note",
    quote="第二条 对个人结汇和境内个人购汇实行年度总额管理。年度总额分别为每人每年等值5万美元。\n第三条 个人所购外汇，可以汇出境外、存入本人外汇储蓄账户，或按照有关规定携带出境。\n第十三条 境外个人经常项目合法人民币收入购汇及未用完的人民币兑回，按以下规定办理：（一）在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的相关证明材料（含税务凭证）办理购汇。\n第十四条 境内个人外汇汇出境外用于经常项目支出，按以下规定办理：外汇储蓄账户内外汇汇出境外当日累计等值5万美元以下（含）的，凭本人有效身份证件在银行办理；超过上述金额的，凭经常项目项下有交易额的真实性凭证办理。\n第十五条 境外个人经常项目外汇汇出境外，按以下规定在银行办理：（一）外汇储蓄账户内外汇汇出，凭本人有效身份证件办理；\n第三十条 个人提取外币现钞当日累计等值1万美元以下（含）的，可以在银行直接办理；超过上述金额的，凭本人有效身份证件、提钞用途证明等材料向银行所在地外汇局事前报备。\n以下内容已被废止：《个人外汇管理办法实施细则》（汇发〔2007〕1号印发）第三十九条。",
    reading="USD 50,000 annual convenience quota applies to domestic individuals' purchase and all individuals' settlement, not automatically to every foreign national. Purchased FX may be remitted, held in the person's own FX savings account, or carried out under the cash rules. Foreign individuals convert lawful current-account RMB income with ID, transaction-amount source documents and tax certificate. Foreign individuals may remit FX from their FX savings account with ID. Cash withdrawal of more than USD 10,000 equivalent in a day requires advance reporting to SAFE. Article 39's penalty has been repealed; Article 9(2) was amended.",
    figures={"annual_quota_usd": 50000, "wire_daily_usd": 50000, "cash_wire_daily_usd": 10000, "cash_withdraw_daily_usd": 10000, "cash_deposit_daily_usd": 5000, "unspent_small_usd": 500, "airport_small_usd": 1000, "exchange_memo_months": 24, "old_bank_fine_cny": 30000, "old_person_fine_cny": 1000},
    limits="The page is marked 已修改 (modified); repealed/amended passages must not be quoted as current without qualification.",
)
add(
    id="B09", title="中华人民共和国外汇管理条例 (国务院令第532号)", publisher="State Council / State Administration of Foreign Exchange",
    url="https://www.safe.gov.cn/safe/2008/0806/5321.html", source_class="government",
    locator="Articles 5, 12, 22, 39, 40, 42, 45 and 52(2)",
    quote="第五条 国家对经常性国际支付和转移不予限制。\n第十二条 经常项目外汇收支应当具有真实、合法的交易基础。经营结汇、售汇业务的金融机构应当按照国务院外汇管理部门的规定，对交易单证的真实性及其与外汇收支的一致性进行合理审查。\n第二十二条 资本项目外汇支出，应当按照国务院外汇管理部门关于付汇与购汇的管理规定，凭有效单证以自有外汇支付或者向经营结汇、售汇业务的金融机构购汇支付。国家规定应当经外汇管理机关批准的，应当在外汇支付前办理批准手续。\n第三十九条 ... 处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款；构成犯罪的，依法追究刑事责任。\n第四十条 ... 处非法套汇金额30%以下的罚款；情节严重的，处非法套汇金额30%以上等值以下的罚款；构成犯罪的，依法追究刑事责任。\n第四十二条 违反规定携带外汇出入境的，由外汇管理机关给予警告，可以处违法金额20%以下的罚款。\n第四十五条 私自买卖外汇、变相买卖外汇、倒买倒卖外汇或者非法介绍买卖外汇数额较大的，由外汇管理机关给予警告，没收违法所得，处违法金额30%以下的罚款；情节严重的，处违法金额30%以上等值以下的罚款；构成犯罪的，依法追究刑事责任。\n（二）境内个人，是指中国公民和在中华人民共和国境内连续居住满1年的外国人",
    reading="Current-account international payments and transfers are not restricted, but underlying transactions must be real and lawful and banks must reasonably review documents. Capital payments need valid documents and approval where required. Evasion, fraudulent FX purchase and private/underground FX dealing carry fines up to 30% of the amount (or, in serious cases, from 30% up to an equal amount) and possible criminal liability. Improperly carrying FX across the border can carry a fine up to 20%. A 'domestic individual' includes a foreigner continuously resident in China for at least one year, excluding certain diplomats.",
    figures={"fine_standard_pct": 30, "cash_violation_pct": 20, "domestic_resident_years": 1},
    limits="The statute does not set a bank's execution rate, a personal eligibility outcome or a tax rate; no tax amount is inferred.",
)
add(
    id="B10", title="2026年外汇管理互联网信息——个人外汇（08）", publisher="SAFE Tianjin Branch",
    url="https://www.safe.gov.cn/tianjin/2026/0713/3088.html", source_class="government",
    locator="Question and answer; quotation of 汇发〔2020〕14号 Article 59",
    quote="境外个人在境内工作期间取得的劳动报酬如何购汇汇出？\n答：根据《国家外汇管理局关于印发〈经常项目外汇业务指引（2020年版）〉的通知》（汇发〔2020〕14号）第五十九条规定，“境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇”。",
    reading="A SAFE branch FAQ confirms that a foreign individual's lawful current-account RMB income earned in China may be used to purchase FX at a bank with valid ID, transaction-amount source materials and tax documentation.",
    figures={"guide_article": 59},
    limits="Branch FAQ; establishes documentary rule, not that the user's particular balance qualifies.",
)
add(
    id="B11", title="2024年经常项目外汇政策问答案例（九）", publisher="SAFE Tianjin Branch",
    url="https://www.safe.gov.cn/tianjin/2024/0621/2529.html", source_class="government",
    locator="境外个人是否享受年度便利化额度购汇？",
    quote="境外个人是否享受年度便利化额度购汇？\n根据《国家外汇管理局关于印发〈经常项目外汇业务指引（2020年版）〉的通知》（汇发〔2020〕14号）第五十九条，境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。",
    reading="Foreign individuals generally use the documented-lawful-income route; holders of a foreign permanent-residence ID card may use the annual convenience quota. A U.S. passport alone does not establish quota eligibility.",
    figures={"guide_article": 59},
    limits="Branch FAQ; local bank implementation and personal status remain unverified.",
)
add(
    id="B12", title="汇发[2014]2号 §VI — simplified personal property transfers (as modified)", publisher="State Administration of Foreign Exchange",
    url="https://www.safe.gov.cn/safe/2014/0124/5476.html", source_class="government",
    locator="Section VI (一)–(四); effective date; 2023 amendment note",
    quote="六、简化个人财产转移售付汇管理\n（一）移民财产转移购付汇核准，由移民原户籍所在地外汇局负责审批。继承财产转移购付汇核准，由被继承人生前户籍所在地外汇局负责审批。取消财产转移总金额超过等值人民币50万元报国家外汇管理局备案的要求。\n（二）取消移民财产转移分次汇出的要求。申请人向原户籍所在地外汇局办理移民财产转移核准手续后，银行可在核准件审批额度内一次或分次汇出相关资金。\n（三）取消继承人从不同被继承人处继承的财产应分别申请、分别汇出的要求。\n（四）取消对有关财产权利文件 ... 进行公证的要求；取消对委托代理协议、代理人身份证明进行公证的要求。\n本通知自2014年2月10日起实施，以前规定与本通知不符的，以本通知为准。",
    reading="The original-hukou SAFE office approves emigrant transfers; the deceased's hukou office approves inheritance transfers. HQ filing above CNY 500,000, the compulsory staged-emigrant-remittance requirement, separate applications for multiple inheritances and notarisation of listed documents were abolished. Banks may remit once or in instalments within the approved amount.",
    figures={"notice_year": 2014, "hq_filing_threshold_cny": 500000, "effective_date": "2014-02-10"},
    limits="This later rule supersedes contradictory staged/HQ-filing wording in PBOC 2004 No.16; see F-18.",
)
add(
    id="B13", title="个人财产对外转移售付汇管理暂行办法 (PBOC 2004 No.16)", publisher="People's Bank of China / State Council Gazette",
    url="https://www.gov.cn/gongbao/content/2005/content_64294.htm", source_class="government",
    locator="Articles 2, 6, 8, 9, 10, 11, 12",
    quote="第二条 本办法所称个人财产对外转移包括移民财产转移（以下简称移民转移）和继承财产转移（以下简称继承转移）。\n第六条 移民转移必须一次性申请拟转移出境的全部财产金额，分步汇出。首次可汇出金额不得超过全部申请转移财产的一半；自首次汇出满1年后，可汇出不超过剩余财产的一半；自首次汇出满2年后，可汇出全部剩余财产。\n第八条 ... 移居外国的，应当提供公安机关出具的中国户籍注销证明 ... （六）申请转移财产所在地或收入来源地主管税务机关开具的税收证明或完税凭证。\n第九条 ... 申请人获得继承财产的证明文件 ... 被继承人财产所在地主管税务机关开具的税收证明或完税凭证。\n第十条 申请财产对外转移总金额在等值人民币50万元以下（含50万元）的，由所在地外汇局审批。... 超过上述金额的，由所在地外汇局初审后，报国家外汇管理局审批。\n第十一条 外汇指定银行办理售汇后，应直接将外汇汇往移民或继承人居住国或地区申请人本人的账户，不得在境内提取外币现钞。\n第十二条 ... 法律规定不得对外转移的财产、不能证明合法来源财产等的对外转移申请，外汇局不予受理。",
    reading="Defines emigrant and inheritance property transfers. Requires ID, hukou cancellation/settlement evidence, source/title documents and tax certificate; the bank must remit to the applicant's own overseas account and may not pay domestic FX cash. Article 6's staged schedule and Article 10's HQ-approval clause have been superseded by B12 §VI and are not used as current instructions.",
    figures={"notice_year": 2004, "article": 6, "old_hq_threshold_cny": 500000, "old_one_off_cny": 200000, "old_first_half": 0.5, "old_wait_years": 2},
    limits="Historical text with later modifications; do not use Article 6 staging as current law.",
)
add(
    id="B14", title="移民财产转移购付汇核准 service guide", publisher="SAFE Hebei Branch",
    url="https://www.safe.gov.cn/hebei/file/file/20240816/86fd609207224d71b23cfda39ebe4bbb.pdf", source_class="government",
    locator="Conditions; application materials; times; fees; approval result; on-site visit",
    quote="（一）准予行政许可的条件\n1. 申请人取得外国永久居留权、外国公民身份或港澳台地区居民身份。\n2.申请汇出资金为申请人在取得外国永久居留权、外国公民身份或港澳台地区居民身份之前在境内拥有的合法财产变现。\n3.申请人收入来源证明以及财产权利证明文件。\n4.主管税务部门出具的税务证明原件（按规定无需提交的除外）\n（一）承诺受理时限：5 个工作日\n（二）法定审批时限：20 个工作日\n（一）办理行政许可是否收费：否\n（二）审批结果名称：《资本项目外汇业务核准件》\n（三）审批结果的有效期限：当次\n（七）到办事现场次数：1",
    reading="A published provincial service guide requires foreign permanent residence/citizenship or HK/Macau/Taiwan resident status and property owned before that status; it lists income-source, title and tax-proof documents. Acceptance is promised in 5 working days, decision in 20 working days, no administrative fee, a single-use approval document and one in-person visit.",
    figures={"accept_working_days": 5, "decision_working_days": 20, "admin_fee": 0, "approval_uses": 1, "onsite_visits": 1, "public_official_referral_cny": 1000000},
    limits="Provincial guide, not a bank tariff. Bank FX rate, wire, intermediary and receiving fees remain blank; see F-09.",
)
add(
    id="B15", title="汇发[2015]49号 — personal FX management and watch list", publisher="State Administration of Foreign Exchange",
    url="https://www.safe.gov.cn/safe/2015/1231/5442.html", source_class="government",
    locator="Sections 2(一)–(三) and effective date",
    quote="二、个人在办理外汇业务时，应当遵守个人外汇管理有关规定，不得以分拆等方式规避额度及真实性管理。国家外汇管理局及其分支局（以下简称外汇局）对规避额度及真实性管理的个人实施“关注名单”管理。\n（二）外汇局对以借用他人额度等方式规避额度及真实性管理的个人，列入“关注名单”管理\n（三）“关注名单”内个人的关注期限为列入“关注名单”的当年及之后连续2年。在关注期限内，“关注名单”内个人办理个人结售汇业务，应凭本人有效身份证件和有交易额的相关证明等材料在银行办理。",
    reading="Splitting or borrowing other people's quotas to evade quota/authenticity management is prohibited; people who do so can be placed on a watch list for the year of listing plus the following two years and must provide full documentation during that period.",
    figures={"watch_following_years": 2, "effective_date": "2016-01-01"},
    limits="No account-specific watch-list status is known.",
)
add(
    id="B16", title="Circular on Regulating Large-sum Overseas Cash Withdrawals with Bank Cards", publisher="State Administration of Foreign Exchange",
    url="https://www.safe.gov.cn/en/2017/1230/1397.html", source_class="government",
    locator="Sections I, IV, VII and translation note",
    quote="In overseas cash withdrawals by individuals with domestic bank cards, the sum of withdrawals using the bank cards under the name of the individual (including supplementary cards) shall not exceed the equivalent of RMB 100,000 in every civil year. In case of overseas cash withdrawals in excess of the annual quota, the individuals will not be allowed to withdraw cash overseas with the domestic bank cards in the current and second years.\nIV. ... the ceiling for every foreign currency card per day is to be adjusted from the equivalent of USD 1,000 to the equivalent of RMB 10,000 ... The RMB card will continue to be subject to the ceiling of the equivalent of RMB 10,000 per card per day\nThe English translation may only be used as a reference. In case a different interpretation of the translated information contained in this website arises, the original Chinese shall prevail.",
    reading="Domestic cards used abroad are capped at RMB 100,000 per person per calendar year and RMB 10,000 per card per day. Exceeding the annual cap blocks overseas cash withdrawals in the current and second years. The English text is a reference translation only.",
    figures={"atm_year_cny": 100000, "atm_day_cny": 10000, "withdrawal_ban_years": 2, "old_daily_usd": 1000},
    limits="This is a cash-withdrawal ceiling, not an FX conversion rate or a fee schedule.",
)
add(
    id="B17", title="携带外币现钞出入境管理暂行办法 (汇发〔2003〕102号)", publisher="SAFE / General Administration of Customs / State Council Gazette",
    url="https://www.gov.cn/gongbao/content/2004/content_63085.htm", source_class="government",
    locator="Notice paragraph 2; Articles 5, 7–11",
    quote="出境人员携带不超过等值5000美元(含5000美元)的外币现钞出境的，无须申领《携带证》，海关予以放行；出境人员携带外币现钞金额在等值5000美元以上至10000美元(含10000美元)的，应向外汇指定银行申领《携带证》... 出境人员原则上不得携带超过等值10000美元的外币现钞出境\n第五条 ... 一、出境人员携出金额在等值5000美元以内(含5000美元)的，不需申领《携带证》... 二、出境人员携出金额在等值5000美元以上至10000美元(含10000美元)的，应当向银行申领《携带证》... 三、出境人员携出金额在等值10000美元以上的，应当向存款或购汇银行所在地国家外汇管理局各分支局 ... 申领《携带证》\n第十一条 《携带证》 ... 自签发之日起30天内一次使用有效。",
    reading="Up to USD 5,000 equivalent in foreign notes may be carried out without a permit; USD 5,000–10,000 requires a bank-issued carry permit; over USD 10,000 is in principle not allowed and requires a SAFE permit in special cases. Each permit is valid 30 days for one use.",
    figures={"no_permit_usd": 5000, "bank_permit_upper_usd": 10000, "permit_valid_days": 30, "same_day_second_usd": 500, "short_trip_second_usd": 1000},
    limits="A permit rule, not a fee, exchange rate or U.S. entry permission. No cash-handling cost is published here.",
)
add(
    id="B18", title="银发〔2026〕42号 — virtual-currency risk notice", publisher="People's Bank of China and other PRC authorities",
    url="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", source_class="government",
    locator="Section I(一), stablecoin paragraph, Section VI(十八)–(十九)",
    quote="虚拟货币相关业务活动属于非法金融活动。在境内开展法定货币与虚拟货币兑换业务、虚拟货币之间的兑换业务、作为中央对手方买卖虚拟货币、为虚拟货币交易提供信息中介和定价服务、代币发行融资以及虚拟货币相关金融产品交易等虚拟货币相关业务活动 ... 一律严格禁止，坚决依法取缔。境外单位和个人不得以任何形式非法向境内主体提供虚拟货币相关服务。\n挂钩法定货币的稳定币在流通使用中变相履行了法定货币的部分功能。未经相关部门依法依规同意，境内外任何单位和个人不得在境外发行挂钩人民币的稳定币。\n违反本通知规定开展虚拟货币、现实世界资产代币化相关非法金融活动，以及为虚拟货币、现实世界资产代币化相关业务提供服务的，依照有关规定予以处罚；构成犯罪的，依法追究刑事责任。\n任何单位和个人投资虚拟货币、现实世界资产代币及相关金融产品，违背公序良俗的，相关民事法律行为无效，由此引发的损失由其自行承担",
    reading="Fiat-to-virtual-currency exchange and related virtual-currency business in China are illegal financial activities and are strictly prohibited. Unapproved offshore issuance of RMB-linked stablecoins and illegal provision of services to domestic parties are prohibited. Penalties follow other rules; losses from covered investments are borne by the investor.",
    figures={"notice_date": "2026-02-06"},
    limits="This page does not publish a numeric fine for a personal conversion attempt; penalties blank; see F-21.",
)
add(
    id="B19", title="国家税务总局 国家外汇管理局公告2013年第40号 (as amended)", publisher="State Taxation Administration / SAFE",
    url="https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", source_class="government",
    locator="Article 1; Article 3(13); Article 4; headnote on 2021 repeals",
    quote="一、境内机构和个人向境外单笔支付等值5万美元以上（不含等值5万美元，下同）下列外汇资金，除本公告第三条规定的情形外，均应向所在地主管税务机关进行税务备案\n（十三）境内个人境外留学、旅游、探亲等因私用汇；\n四、境外个人办理服务贸易、收益和经常转移项下对外支付，应按照个人外汇管理的相关规定办理。\n1.根据《国家税务总局 国家外汇管理局关于服务贸易等项目对外支付税务备案有关问题的补充公告》（国家税务总局 国家外汇管理局公告2021年第19号），自2021年6月29日起，本文第一条第二款、第二条第二款、第五条、第六条、第七条、第八条、第十条和附件2同时废止。",
    reading="A single outward payment above USD 50,000 in listed service-trade/income/current-transfer categories generally requires tax filing, with exemptions including an individual's overseas study, tourism and visiting relatives. Foreign individuals' current-account payments follow personal FX rules. Several clauses of this 2013 notice were repealed in 2021; applicability to a transfer of one's own savings is not determined here.",
    figures={"tax_filing_usd": 50000, "amendment_date": "2021-06-29"},
    limits="Modified text; no conclusion about the user's particular payment purpose or tax filing is inferred.",
)
add(
    id="B20", title="中华人民共和国个人所得税法", publisher="National People's Congress / Shanghai Tax Service",
    url="https://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/201809/t441789.html", source_class="government",
    locator="Articles 1, 2, 3, 10, 13, 19; rate table 1",
    quote="第一条 在中国境内有住所，或者无住所而一个纳税年度内在中国境内居住累计满一百八十三天的个人，为居民个人。\n第三条 个人所得税的税率：（一）综合所得，适用百分之三至百分之四十五的超额累进税率；（二）经营所得，适用百分之五至百分之三十五的超额累进税率；（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。\n第十条 有下列情形之一的，纳税人应当依法办理纳税申报：...（五）因移居境外注销中国户籍；\n第十三条 ... 纳税人因移居境外注销中国户籍的，应当在注销中国户籍前办理税款清算。\n第十九条 纳税人、扣缴义务人和税务机关及其工作人员违反本法规定的，依照《中华人民共和国税收征收管理法》和有关法律法规的规定追究法律责任。",
    reading="PRC individual income tax depends on residence (including the 183-day rule) and income category: comprehensive income 3–45%, business income 5–35%, and interest/dividends/property/other enumerated income 20%. Emigration with hukou cancellation requires tax clearance. This is tax on underlying income/assets, not a separately identified tax on the act of converting currency.",
    figures={"resident_days": 183, "comprehensive_min_pct": 3, "comprehensive_max_pct": 45, "business_min_pct": 5, "business_max_pct": 35, "flat_pct": 20, "annual_deduction_cny": 60000, "nonresident_monthly_deduction_cny": 5000},
    limits="Personal residence, income character, deductions and tax-paid status are unknown; no personal rate or bill is calculated.",
)
add(
    id="B21", title="Report of Foreign Bank and Financial Accounts (FBAR)", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar", source_class="government",
    locator="Who must file; When to file; Penalties; Filing delinquent FBARs",
    quote="A U.S. person, including a citizen, resident, corporation, partnership, limited liability company, trust and estate, must file an FBAR to report: 1. a financial interest in or signature or other authority over at least one financial account located outside the United States if 2. the aggregate value of those foreign financial accounts exceeded $10,000 at any time during the calendar year reported.\nThe FBAR is an annual report, due April 15 following the calendar year reported. You’re allowed an automatic extension to October 15\nCivil FBAR penalty maximums in Title 31 of the United States Code are adjusted annually for inflation.",
    reading="A U.S. citizen with foreign accounts whose combined maximum exceeds USD 10,000 at any time in a year must file FinCEN Form 114; April 15 due date with automatic October 15 extension. It is a reporting duty, not a tax on conversion. Penalties depend on facts and are inflation-adjusted.",
    figures={"fbar_threshold_usd": 10000, "due_month": 4, "due_day": 15, "extension_month": 10, "extension_day": 15, "form": 114, "records_years": 5},
    limits="Prior filing history and account balances are unknown; see F-15.",
)
add(
    id="B22", title="31 CFR 1010.821 — penalty adjustment table", publisher="eCFR / FinCEN, U.S. Treasury",
    url="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", source_class="government",
    locator="Display date; Table 1 entries for 31 U.S.C. 5321(a)(5)(B)(i) and (C)(i)(I); amendment history",
    quote="Displaying title 31, up to date as of 11/09/2026. Title 31 was last amended 11/06/2026.\nForeign Financial Agency Transaction—Non-Willful Violation of Transaction | 10,000 | 16,536\nForeign Financial Agency Transaction—Willful Violation of Transaction | 100,000 | 165,353\n[90 FR 5630](https://www.federalregister.gov/citation/90-FR-5630), Jan. 17, 2025",
    reading="The displayed eCFR table gives adjusted maximum penalties of USD 16,536 for a non-willful foreign financial agency transaction violation and USD 165,353 for a willful violation. The table's displayed amendment history ends with the 17 Jan 2025 Federal Register adjustment.",
    figures={"nonwillful_usd": 16536, "willful_usd": 165353, "display_date": "2026-11-09", "last_amended": "2026-11-06", "latest_fr": "90 FR 5630", "latest_fr_year": 2025},
    limits="The eCFR says its content is authoritative but unofficial. No 2026 inflation adjustment is listed in the quoted amendment history; amounts may be stale; see F-17.",
)
add(
    id="B23", title="Comparison of Form 8938 and FBAR requirements", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", source_class="government",
    locator="Reporting threshold and Penalties rows; Form 8938 and FBAR columns",
    quote="Specified individuals living in the US: - Unmarried individual (or married filing separately): Total value of assets was more than $50,000 on the last day of the tax year, or more than $75,000 at any time during the year.\nSpecified individuals living outside the US: - Unmarried individual (or married filing separately): Total value of assets was more than $200,000 on the last day of the tax year, or more than $300,000 at any time during the year.\nAggregate value of financial accounts exceeds $10,000 at any time during the calendar year.\nUp to $10,000 for failure to disclose and an additional $10,000 for each 30 days of non-filing after IRS notice of a failure to disclose, for a potential maximum penalty of $60,000",
    reading="Form 8938 thresholds depend on residence and filing status; for an unmarried individual in the U.S. they are >USD 50,000 at year end or >USD 75,000 during the year, and abroad >USD 200,000 at year end or >USD 300,000 during the year. FBAR uses >USD 10,000 aggregate accounts. Form 8938 failure-to-disclose penalties can reach USD 60,000. Both forms may be required.",
    figures={"form": 8938, "form8938_us_single_end_usd": 50000, "form8938_us_single_any_usd": 75000, "form8938_abroad_single_end_usd": 200000, "form8938_abroad_single_any_usd": 300000, "form8938_penalty_usd": 10000, "form8938_max_penalty_usd": 60000, "fbar_threshold_usd": 10000},
    limits="Residence, filing status and asset values are unknown; no filing conclusion is made.",
)
add(
    id="B24", title="Gifts from foreign person", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/businesses/gifts-from-foreign-person", source_class="government",
    locator="Reporting requirements; filing due date",
    quote="For gifts or bequests from a nonresident alien or foreign estate, you are required to report the receipt of such gifts or bequests only if the aggregate amount received ... exceeds $100,000 during the taxable year.\nFor purported gifts from foreign corporations or foreign partnerships, you are required to report ... only if the aggregate amount ... exceeds $20,116 for 2025, and $20,573 for 2026 (adjusted annually for inflation).\nIf the gifts or bequests exceed $100,000, you must separately identify each gift in excess of $5,000.\nIf you are a U.S. person ... who received a large gift or bequest from a foreign person, you need to complete Part IV of Form 3520",
    reading="A U.S. person reports large foreign gifts/bequests on Form 3520 Part IV: >USD 100,000 aggregate from a nonresident alien/foreign estate, or >USD 20,573 in 2026 from foreign corporations/partnerships. Gifts from related parties are aggregated. This applies only if the funds are a gift/bequest.",
    figures={"gift_nra_usd": 100000, "gift_entity_2025_usd": 20116, "gift_entity_2026_usd": 20573, "separate_gift_usd": 5000, "form": 3520},
    limits="The origin of the CNY balance is unknown; no gift/bequest characterization is inferred.",
)
add(
    id="B25", title="Instructions for Form 2555 (2026)", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/instructions/i2555", source_class="government",
    locator="What's New — Exclusion amount; Who Qualifies — tax home test",
    quote="For 2026, the maximum exclusion amount has increased to $132,900.\nYou may qualify for the foreign earned income exclusion and the housing exclusion or deduction if both of the following apply. - You meet the tax home test ... - You meet either the bona fide residence test or the physical presence test\nYou aren’t considered to have a tax home in a foreign country for any period during which your abode is in the United States",
    reading="The 2026 foreign earned income exclusion cap is USD 132,900, but eligibility requires a foreign tax home and either bona fide residence or physical presence; an abode in the United States generally defeats the tax-home test.",
    figures={"form": 2555, "feie_2026_usd": 132900},
    limits="Eligibility is fact-specific and unverified; this is earned-income treatment, not a conversion or principal-tax rule.",
)
add(
    id="B26", title="Rev. Proc. 2026-35 — 2027 inflation adjustments", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/pub/irs-drop/rp-26-35.pdf", source_class="government",
    locator="Sections 3.41, 3.46(1), 3.51",
    quote=".41 Foreign Earned Income Exclusion. For taxable years beginning in 2027, the foreign earned income exclusion amount under § 911(b)(2)(D)(i) is $137,300.\n(1) For calendar year 2027, the first $20,000 of gifts to any person ... are not included in the total amount of taxable gifts under § 2503\n.51 Notice of Large Gifts Received from Foreign Persons. For taxable years beginning in 2027, § 6039F authorizes the Secretary ... to require recipients of gifts from certain foreign persons to report these gifts if the aggregate value of gifts received in the taxable year exceeds $21,240.31.",
    reading="For 2027, the FEIE is USD 137,300; the annual gift exclusion is USD 20,000; the §6039F large-foreign-gift notice threshold is USD 21,240.31. These are 2027 amounts, not 2026 transfer figures.",
    figures={"tax_year": 2027, "section": 6039, "feie_2027_usd": 137300, "gift_exclusion_2027_usd": 20000, "foreign_gift_notice_2027_usd": 21240.31},
    limits="Do not apply 2027 figures to a 2026 transaction; prior repository claims that the 2027 FEIE is unverified are conflicts.",
)
add(
    id="B27", title="26 U.S.C. §988 (2024 edition)", publisher="U.S. Government Publishing Office",
    url="https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", source_class="government",
    locator="§988(a)(1)(A), (c)(1)(C), (e)(1)–(3)",
    quote="any foreign currency gain or loss attributable to a section 988 transaction shall be computed separately and treated as ordinary income or loss (as the case may be).\nIn the case of a disposition of any nonfunctional currency— (I) such disposition shall be treated as a section 988 transaction, and (II) any gain or loss from such transaction shall be treated as foreign currency gain or loss\nThe preceding provisions of this section shall not apply to any section 988 transaction entered into by an individual which is a personal transaction.\nno gain shall be recognized for purposes of this subtitle by reason of changes in exchange rates after such currency was acquired by such individual and before such disposition. The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200.",
    reading="Disposition of nonfunctional currency is a §988 transaction; an individual's personal-transaction FX gain is not recognized only when the otherwise recognized gain does not exceed USD 200. Larger personal gains and non-personal transactions are ordinary income/loss, taxed at rates determined elsewhere.",
    figures={"section": 988, "personal_de_minimis_usd": 200},
    limits="Acquisition date/rate, whether the transaction is personal, and the applicable U.S. ordinary rate are unknown; no tax amount is inferred.",
)
add(
    id="B28", title="Money and Other Monetary Instruments", publisher="U.S. Customs and Border Protection",
    url="https://www.cbp.gov/travel/international-visitors/money-monetary-instruments", source_class="government",
    locator="Federal Mandate; Who Must File; What if I don't file?",
    quote="Federal law mandates that when entering or leaving the United States you must report amounts exceeding $10,000 to U.S. Customs and Border Protection (CBP).\nAnyone who brings, sends, or receives currency or monetary instruments totaling more than $10,000 at one time, either into or out of the United States, must report it.\nWhen families or groups are involved, the $10,000 threshold applies to the total amount they are carrying or sending collectively, not per individual.\nAn Individual who fails to file a report or submit false or fraudulent information, risk having their currency or monetary instruments forfeited and seized. In some instances, they may face civil or criminal penalties",
    reading="More than USD 10,000 in currency/monetary instruments entering or leaving the U.S. at one time must be reported on FinCEN Form 105; the threshold is collective for families/groups. Failure risks seizure and civil/criminal penalties. It is a reporting rule, not a tax.",
    figures={"cmir_threshold_usd": 10000, "form": 105},
    limits="No specific personal penalty amount is published here; blank; see F-11.",
)
add(
    id="B29", title="Foreign Tax Credit", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit", source_class="government",
    locator="Opening; How to claim; Compliance issues bullets",
    quote="If you paid or accrued foreign taxes to a foreign country or U.S. possession and are subject to U.S. tax on the same income, you may be able to take either a credit or an itemized deduction for those taxes.\nFile Form 1116, Foreign Tax Credit (Individual, Estate, or Trust)\nIf you elect to exclude either foreign earned income or foreign housing costs, you cannot take a foreign tax credit for taxes on income you exclude.\nThe amount of foreign tax that qualifies as a foreign tax credit is not necessarily the amount of tax withheld by the foreign country. If you are entitled to a reduced rate of foreign tax based on an income tax treaty ... only that reduced tax qualifies for the credit.\nA foreign tax credit may not be claimed for taxes on income that you exclude from U.S. gross income",
    reading="A foreign tax credit under Form 1116 is available only for qualifying foreign taxes on the same income subject to U.S. tax; it is not a blanket dollar-for-dollar offset. No credit is allowed on income excluded under FEIE, and treaty-reduced tax may limit the credit.",
    figures={"form": 1116},
    limits="Treaty text was not line-by-line verified in this session; no FTC amount is computed; see F-16.",
)
add(
    id="B30", title="Streamlined filing compliance procedures", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures", source_class="government",
    locator="Purpose; Eligibility — non-willful certification; IRS Criminal Investigation practice",
    quote="The streamlined filing compliance procedures ... are available to taxpayers certifying that their failure to report foreign financial assets and pay all tax due in respect of those assets did not result from willful conduct on their part.\nNon-willful conduct is conduct that is due to negligence, inadvertence, or mistake or conduct that is the result of a good faith misunderstanding of the requirements of the law\nTaxpayers who are concerned that their failure to report income, pay tax, and submit required information returns was due to willful conduct ... should consider participating in the IRS Criminal Investigation Voluntary Disclosure Practice and should consult with their professional or legal advisers.",
    reading="Streamlined procedures require certification of non-willful conduct; willful conduct requires a different voluntary-disclosure route and professional advice. Prior filing history is a gating fact.",
    figures={},
    limits="No determination about the user's filing history or willfulness is made.",
)
add(
    id="B31", title="BOC promotion link currently returns page-not-found", publisher="Bank of China",
    url="https://www.boc.cn/ebanking/bi3/bi31/202012/t20201231_18853335.html", source_class="bank primary",
    locator="Linked as 优惠活动公告 from B03; page body",
    quote="您访问的中国银行网站页面不存在",
    reading="The official fee schedule's linked promotion announcement is unavailable. Any promotional or local discount cannot be verified from that official destination.",
    figures={}, status="official 404 read 2026-11-11",
    limits="A 404 is not proof that no discount exists; it is proof that this page does not currently publish one. See F-07.",
)
add(
    id="B32", title="中华人民共和国税收征收管理法", publisher="State Taxation Administration taxpayer-service database",
    url="https://12366.chinatax.gov.cn/bzds/120/120-1-4.html", source_class="government",
    locator="Articles 32, 34, 44, 51, 52, 63; page disclaimer",
    quote="本系统内所有内容仅供参考，具体税收政策，办税流程及表单填报要求等以法律法规及相关规定为准。\n第三十二条 纳税人未按照规定期限缴纳税款的 ... 从滞纳税款之日起，按日加收滞纳税款万分之五的滞纳金。\n第三十四条 税务机关征收税款时，必须给纳税人开具完税凭证。\n第四十四条 欠缴税款的纳税人或者他的法定代表人需要出境的，应当在出境前向税务机关结清应纳税款、滞纳金或者提供担保。未结清税款、滞纳金，又不提供担保的，税务机关可以通知出境管理机关阻止其出境。\n第六十三条 ... 是偷税。对纳税人偷税的，由税务机关追缴其不缴或者少缴的税款、滞纳金，并处不缴或者少缴的税款百分之五十以上五倍以下的罚款；构成犯罪的，依法追究刑事责任。",
    reading="Late-paid tax accrues a daily 0.05% surcharge; tax payment certificates are issued; unpaid tax/surcharge can block departure without settlement or guarantee; tax evasion can lead to a fine of 50% to five times the underpaid tax. The hosting page says its contents are for reference and the law prevails.",
    figures={"late_daily_rate": 0.0005, "evasion_fine_min_multiple": 0.5, "evasion_fine_max_multiple": 5, "refund_years": 3, "general_pursuit_years": 3, "special_pursuit_years": 5},
    limits="These are enforcement rules, not a conversion tax; no personal overdue-tax status is known.",
)
add(
    id="B33", title="银发〔2020〕330号 — cross-border RMB policy notice", publisher="People's Bank of China and other PRC authorities",
    url="https://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4693545/4210907/index.html", source_class="government",
    locator="Section IV (十三), (十四), Section V final paragraph",
    quote="四、便利个人经常项目下跨境人民币收付\n（十三）支持个人经常项目下跨境人民币结算业务开展。支持境内银行在“展业三原则”的基础上，为个人办理经常项目下跨境人民币结算业务，进一步便利个人薪酬等合法合规收入的跨境收付业务。\n境内银行应 ... 按照《中华人民共和国反洗钱法》和其他有关规定，在办理跨境人民币业务时，应切实履行反洗钱、反恐怖融资、反逃税义务。",
    reading="Banks are supported in handling current-account cross-border RMB settlement for individuals, including lawful salary/compensation income, under know-your-customer, due-diligence and AML rules. The notice does not publish a general personal route, fee, rate or limit for moving an existing capital/savings balance abroad.",
    figures={"notice_date": "2020-12-31", "effective_date": "2021-02-04"},
    limits="A direct RMB-to-overseas-account route is therefore listed as unverified, with blank costs; see F-12.",
)
add(
    id="B34", title="About Publication 901, U.S. Tax Treaties", publisher="U.S. Internal Revenue Service",
    url="https://www.irs.gov/forms-pubs/about-publication-901", source_class="government",
    locator="Opening description; current revision link",
    quote="Publication 901 will tell you whether a tax treaty between the United States and a particular country offers a reduced rate of, or possibly a complete exemption from, U.S. income tax for residents of that particular country.\nCurrent revision: Publication 901 (09/2024), U.S. Tax Treaties",
    reading="Treaty effects depend on the specific treaty and the taxpayer's residence. The official treaty publication exists and should be checked before claiming a reduced rate or exemption.",
    figures={"publication": 901, "revision": "09/2024"},
    limits="The treaty text was not read line-by-line in this session; no treaty conclusion is made; see F-16.",
)

out = {"generated_by": "guide-be3c20e8/data/make_sources.py", "retrieved": READ, "sources": S}
(HERE / "sources.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {len(S)} sources")
