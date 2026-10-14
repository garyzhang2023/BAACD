# Supplementary S3 — Anonymized Derived Dataset: codebook

**Files**

| File | Content |
|---|---|
| `S3_postings_derived_anonymized.csv` | 524 rows × 19 variables, UTF-8, comma-separated |
| `S3_postings_derived_anonymized.xlsx` | the same data in Excel |

One row per analytic record. The dataset contains no company name, no company identifier, no
posting URL, no contact detail and no posting text. Every reported statistic in the manuscript
can be computed from these 19 variables.

## 1. Variable list

| # | Variable | Type | Values / range | Notes |
|---:|---|---|---|---|
| 1 | `anon_id` | string | `P0001`–`P0524` | re-identified per record; contains no information about platform order or source |
| 2 | `city_category` | categorical | Guangzhou 88, Shenzhen 105, Dongguan 65, Foshan 45, Zhuhai 42, Huizhou 42, Zhongshan 39, Shantou 35, Jiangmen 35, Zhaoqing 28 | the ten cities listed in Appendix A.1 |
| 3 | `job_family` | categorical | see §2 | six families, ascending code 1–6 |
| 4 | `education_requirement` | categorical | Bachelor 318, Junior college 103, No requirement 56, Master 23, Doctorate 10, Secondary vocational 10, High school 2, Junior high or below 2 | as stated in the posting |
| 5 | `education_group` | categorical | Bachelor 318, Junior college or below 117, No requirement 56, Master 23, Doctorate 10 | collapsed version used in the education contingency tables |
| 6 | `experience_requirement` | categorical | 1-3 years 143, 3-5 years 120, No requirement 113, 5-10 years 65, Student/graduate 31, 10+ years 19, <1 year 9, blank 24 | as stated; blank means the field was absent in the posting |
| 7 | `salary_midpoint_k_cny_per_month` | numeric | 70 distinct values | midpoint of the posted salary band, thousand CNY per month; the dependent variable of the wage models is its natural logarithm |
| 8 | `company_size_band` | categorical | 100-499 123, 20-99 107, 10000+ 59, 1000-9999 56, 500-999 36, 0-20 101, blank 42 | size band as displayed on the platform |
| 9 | `dim_understand_business` | binary 0/1 | 1 = 279, 0 = 245 | four dimensions of the capability framework (Table 3) |
| 10 | `dim_master_models` | binary 0/1 | 1 = 268, 0 = 256 | as above |
| 11 | `dim_know_security` | binary 0/1 | 1 = 8, 0 = 516 | mutually exclusive primary specification |
| 12 | `dim_can_deliver` | binary 0/1 | 1 = 343, 0 = 181 | as above |
| 13 | `sec_T1_general_infosec` | binary 0/1 | 1 = 14 | Table 7, T1: cybersecurity, classified protection, access control, confidentiality |
| 14 | `sec_T2_data_governance` | binary 0/1 | 1 = 32 | Table 7, T2: data security, desensitization, privacy, authorization, audit |
| 15 | `sec_T3_ai_model_safety` | binary 0/1 | 1 = 7 | Table 7, T3 (automated regex): AI or large-model security, agent security, prompt injection, jailbreak, alignment, hallucination governance |
| 16 | `sec_T4_ethics_governance` | binary 0/1 | 1 = 6 | Table 7, T4: AI ethics, responsible AI, algorithmic fairness, explainability, value alignment |
| 17 | `sec_T5_business_compliance` | binary 0/1 | 1 = 56 | Table 7, T5: compliance, legal affairs, regulatory requirements |
| 18 | `sec_ai_specific_candidate_T3orT4` | binary 0/1 | 1 = 12 | automated candidate pool: T3 or T4, before manual verification |
| 19 | `sec_any_T1toT5` | binary 0/1 | 1 = 78 | any security semantics at any level |

The five security levels **overlap and cannot be summed**; `sec_any_T1toT5` is the union rather
than the total. `sec_ai_specific_candidate_T3orT4` is the automated candidate pool; after manual
verification the strict result is 6 records (Table 7).

## 2. Job-family codes

The six families are ordered as they appear in the manuscript's tables. The code below is the
canonical identifier used throughout this package (including the blind coding form, where the
coder saw only the code and the short label).

| Code | Family |
|---|---|
| 1 | Delivery and implementation (FDE type) |
| 2 | Solutions and pre-sales |
| 3 | Research, development and algorithms |
| 4 | Product and operations |
| 5 | AI applications and tools |
| 6 | Other related roles |

Frequencies in the analytic sample: code 1 = 170, code 3 = 122, code 6 = 103, code 5 = 57,
code 2 = 41, code 4 = 31.

## 3. Coding values that were translated

The source postings are Chinese, so the categorical values were translated for this package.
The mapping is one-to-one and reversible; no value was collapsed, merged or dropped.

| Variable | Original value → value in this package |
|---|---|
| `city_category` | 广州→Guangzhou, 深圳→Shenzhen, 东莞→Dongguan, 佛山→Foshan, 珠海→Zhuhai, 惠州→Huizhou, 中山→Zhongshan, 汕头→Shantou, 江门→Jiangmen, 肇庆→Zhaoqing |
| `job_family` | ①交付实施族（FDE型）→1 Delivery and implementation (FDE-type); ②解决方案/售前族→2 Solutions and pre-sales; ③研发算法族→3 Research, development and algorithms; ④产品运营族→4 Product and operations; ⑤AI应用/工具族→5 AI applications and tools; ⑥其他→6 Other related roles |
| `education_requirement`, `education_group` | 本科→Bachelor, 大专→Junior college, 学历不限→No requirement, 硕士→Master, 博士→Doctorate, 高中→High school, 中专/中技→Secondary vocational, 初中及以下→Junior high or below, 专科及以下→Junior college or below |
| `experience_requirement` | 1-3年→1-3 years, 3-5年→3-5 years, 5-10年→5-10 years, 10年以上→10+ years, 经验不限→No requirement, 1年以内→<1 year, 在校/应届→Student/graduate |
| `company_size_band` | 0-20人→0-20, 20-99人→20-99, 100-499人→100-499, 500-999人→500-999, 1000-9999人→1000-9999, 10000人以上→10000+ |

## 4. Withheld fields

Of the 23 fields stored per record during collection, four were withheld from this package
because they can identify a firm or a person: company name, company identifier, posting URL and
posting text. Job title, skill tags and salary were retained in coded or numeric form only; the
free-text job title and skill tags appear exclusively in the two adjudicated records in
`S4_Second_Coder_Reliability/Returned/S4_third_adjudication_table.csv`, where they are needed to
make the coding decision intelligible.

## 5. Ethics

The records were collected from publicly visible job postings. No applicant or employee data
were collected, and no human participant was involved; see the Institutional Review Board and
Informed Consent statements in the manuscript.
