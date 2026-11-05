# Taipower Open Government Data License notice

Taiwan Power Company / 台灣電力股份有限公司 — 2026 retrieval —
台灣電力公司再生能源各場址資料, official dataset17141, CSV snapshot SHA256
`366e7f928e60c9c1dc531eb5d9f39b6f3b02c88417e7ac0edabc8dbbd14b49c6`.
No release version or data-effective date is asserted from the retrieval year.

This Open Data is made available under the Open Government Data License v1.0.
Users may use it subject to that licence's conditions and attribution obligation.

- Dataset: <https://data.gov.tw/dataset/17141>
- Publisher CSV: <https://service.taipower.com.tw/data/opendata/apply/file/d693002/001.csv>
- Licence: <https://data.gov.tw/license>

The current factual derivative is a review ledger and candidate reader:
71 photovoltaic site rows in45 station groups. No Taipower canonical plants,
nameplate ratings or OEM equipment models have been accepted. Addresses and
portal personal contact details are excluded. Station/site groups are not
independent plant identities. Application labels and HTTP modification dates
are not current operational evidence. See the dated source and candidate reviews.

## 4 November 2026, 20:30 review update

The earlier paragraph describes the initial 20:00 staging outcome. The subsequent
manual review accepts one canonical Longjing plant (station6), grouping three
source site/bid rows into the two printed I/II phases, and qualifies station
contexts for two existing projects. It does not accept every station as a plant.

Additional attributed Open Data:

- Taiwan Power Company / 台灣電力股份有限公司 — 2026 retrieval —
  台灣電力公司太陽光電發電量及平均單位裝置容量每日發電量統計表,
  dataset29938; source period2016-01 through2026-09, selected Q3 2026.
  CSV SHA256 `5457bccb865d9829d61f431b01a14d959021f1d82e73b76c99a1bcb5028848ab`.
  <https://data.gov.tw/dataset/29938>, licence <https://data.gov.tw/license>.
- Tainan City Government / 臺南市政府 — 2021-03-31 —
  南市全國最大太陽光電場啟用 年產2億度綠電 黃偉哲力推台南成為智慧綠能典範城市.
  <https://www.tainan.gov.tw/News_Content.aspx?n=13370&s=7755003>.
  Source-specific reuse declaration: <https://www.tainan.gov.tw/cp.aspx?n=13612>.
- Taiwan Power Company, published by Ministry of Economic Affairs — 2023-01-06 —
  綠能+儲能！台電台南鹽田光電場打造全台最大20MW儲能系統.
  <https://www.moea.gov.tw/MNS/populace/news/News.aspx?kind=1&menu_id=40&news_id=104232>.
- Changhua County Government / 彰化縣政府 — 2018-02-08 —
  魏縣長出席台電彰濱太陽光電工程動土典禮 年發1.3億度 打造全國最大光電場.
  <https://www.chcg.gov.tw/ch2/print_all.aspx?bull_id=267703>.

The Ministry and Changhua explicitly adopt Taiwan OGDL v1.0 with attribution:
<https://www.moea.gov.tw/MNS/populace/content/ContentFoot.aspx?menu_id=13863>
and <https://www.chcg.gov.tw/ch2/copyright.aspx>. Tainan's own declaration permits
reuse and adaptation with source attribution. No photos, logos or personal
contacts are reproduced. No publisher endorsement is claimed. Two conflicting
historical station-period pairs remain held in full; no preferred value, month
repair, annual sum, AC/DC basis or current operating state is inferred.

## 4 November 2026, 21:55 review update

Two further wholeplants are manually accepted: Yongan Salt Flats (PV station14,
site29) and Taipower Tainan Qigu (PV station12, sites24/25 grouped as phases I/II).
Six Q3 2026 station-month observations retain their native scope; September
installed kW becomes unspecified-basis MW, without summing rounded site values.
Conditional HEAD requests returned304 for both cached CSVs. Current operation,
AC/DC ratings, coordinates and verified OEM equipment assignments remain unknown.

Independent identity evidence has its own source-specific government licence:

- Office of the President, 2 June 2013, named Taipower Yongan station:
  <https://english.president.gov.tw/NEWS/4173>.
  Reuse declaration: <https://english.president.gov.tw/Page/18>.
- MOEA, 28 July 2023 transmittal, Qigu reference-case phase arrangement on physical
  PDF page5 (printed page3):
  <https://www.moea.gov.tw/Mns/CNC/content/wHandMenuFile.ashx?file_id=34487>.
  Reuse declaration:
  <https://www.moea.gov.tw/MNS/populace/content/ContentFoot.aspx?menu_id=13863>.

Both declarations provide OGDL Taiwan v1.0 reuse with attribution. Only factual
plant identity/phase context is represented; personal contacts, third-party maps,
photographs and full documents are excluded. Historical visit/construction
observations are not commissioning dates or current lifecycle claims.
