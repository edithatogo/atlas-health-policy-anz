# Viral hepatitis: national programmes and epidemiology evidence

Research snapshot reviewed 10 September 2026. This public, aggregate evidence supplement supports examination of GO8554. It is not an application, approved HHS position, clinical audit or partner commitment.

## Contents

- `sources.csv`: 25 source/access records, with dates, locators and limitations.
- `national_programmes.csv`: 8 participation routes.
- `hbv_regional_2024.csv`: 15 PHN/SA3 rows, including suppressed values.
- `hcv_treatment_monthly_average.csv`: 20 rounded monthly-average observations.
- `hcv_australia_cascade_2024.csv`: 12 national modelled indicators with denominators.
- `aihw_prison_indicators.csv`: 9 indicators; AusHep and NPHDC kept separate.
- `aihw_liver_cancer_indicators.csv`: 10 indicators separating projections and observed periods.
- `aihw_api_observations.json`: 2 observed metadata responses, semantically reconstructed.
- `access_and_validation.json`: execution boundaries and checks.

## Important interpretation rules

1. PHN, SA3 and HHS geographies are not interchangeable. Do not sum overlapping parent/child rows. Cairns North/South and Far North are statistical areas, not HHS performance units.
2. HBV care/treatment uptake uses estimated chronic infection as denominator, not treatment-eligible patients. The 2024 table supplements administrative data with laboratory data. Published percentages are not a clinical audit.
3. Empty care/treatment cells mean suppressed, never zero. The source suppresses where the number receiving treatment or care is <=10; no suppressed value is reconstructed.
4. HCV monthly values are rounded averages. 2025 covers January-May; 2016 covers March-December. Do not convert them to exact annual totals or infer unmet need solely from declining treatment counts.
5. The 2024 HCV cascade uses different denominators for diagnosis, RNA confirmation, annual treatment and cure. Preserve those definitions.
6. AIHW's 2025 prison report includes 2022-2023 laboratory prevalence from AusHep. Its 2025 self-reported discharge testing item excludes Queensland. Neither dataset establishes current prevalence or care performance in a particular Queensland prison.
7. Liver cancer indicators cover all causes. The 2025 First Nations incidence/mortality figures are projections. They are not measured 2025 outcomes or hepatitis-attributable cases. Survival comparisons use the publisher's age-adjustment.
8. Programme pages establish a programme or public participation route. They do not establish GO8554 consortium recruitment, local participation, new funding or agreement to partner.

## Capture and medallion boundary

The three epidemiology PDF tables were checked against rendered page images. AIHW HTML table values and notes were read directly. The two small API responses were visible as JSON through the web tool. CSV and JSON here are curated source-derived representations, not original publisher files or byte-exact HTTP captures.

Public original PDF/XLSX downloads into the working container failed because network DNS was unavailable. The Queensland Q2 report URL also failed revalidation through the web tool. Its previous-review numbers are not included among newly verified observations. No ABS population observation response was obtained.

This is quarantined research evidence, outside the canonical Bronze/Silver/Gold/Platinum release pipeline. It does not change source-packet registry membership, qualified holdings, corpus denominators or release gates. No native SourceRight, CiteWeft or Authentext execution is claimed. No confidential application, patient data or operational records are included.

## Source use

Numeric facts are attributed through `source_id` references to `sources.csv`. Publisher rights remain with publishers; public availability is not asserted to be a redistribution licence for entire works. API JSON metadata includes its publisher-returned version timestamps.

## Outstanding acquisition and application work

Full publisher originals and cancer workbooks; current Queensland notification series; an agreed HHS/PHN/SA3 geographic crosswalk; current local mother-infant and adult care cascades; existing programme/site participation; eligible national lead; costed additionality and partner agreement remain to be established.
