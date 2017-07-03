funds-crawler
===


This project dedicated to crawl the funds info from [fundsupermart.com.hk](http://www.fundsupermart.com.hk/hk/main/fundinfo/generateChartDataSeries.svdo) and other fund site in the future.


Requirements:
---
- docker
- docker-compose

*Since all the project is dockerized, all the requirements are built into the docker container. Just make sure you have docker environment set up.*

Architecture Overview:
---
*To be added*

Run (Dev)
---
- Basic Funds Info
```
docker-compose -f docker-compose.dev.yml up
docker-compose -f docker-compose.dev.yml exec crawler bash run.sh
```
- Fund documents   
(By default, the fund documents is running with the docker compose, and it will collect the docs info once the basic funds are crawled from above step. Or you can just mannualy trigger it by step into the docker container and run it.)
```
docker-compose -f docker-compose.dev.yml exec crawler bash
python funds_crawler/docs.py
```

- Chart Data  
(The crawler for chart data is implemented with asyncio/uvloop/aiohttp.)
```
docker-compose -f docker-compose.dev.yml exec crawler python funds_crawler/async_chart_data.py
```


Funds Output Data Structure (as of 2017/05/02)
---
- Topic: `lion-funds.detail`
```json
{
    "region": "NAU",
    "price_basis": "未知價",
    "cp": {
        "lc": {
            "2y": 5.67,
            "3m": 2.07,
            "1y": 5.65,
            "1m": 1.89,
            "5y": 20.29,
            "ytd": 2.83,
            "since_lch": 135.71,
            "4y": 10.73,
            "3y": 10.53
        },
        "fc": {
            "2y": 5.34,
            "3m": 1.84,
            "1y": 5.39,
            "1m": 1.74,
            "5y": 20.1,
            "ytd": 2.58,
            "since_lch": 136.47,
            "4y": 10.57,
            "3y": 10.25
        }
    },
    "fund_size_val": 1140600000,
    "fund_size_date": "2017-02-28",
    "currency": "USD",
    "code": "HKAB001",
    "min_invest_subs": {
        "lc": 6000,
        "fc": 750
    },
    "company": "HKALLBERN",
    "latest_nav_val": 8.46,
    "latest_nav_date": "2017-04-20",
    "hist_price": {
        "3y_high": 9.02,
        "all_high": 9.34,
        "3y_low": 8.02,
        "all_low": 6.63,
        "1y_low": 8.29,
        "1y_high": 8.69
    },
    "risk_statement": "• 投資於本基金亦可能涉及固定收益證券風險、不流通資產風險、管理風險及信用風險。低評級及無評級工具被視為須承受本金及利息損失的更大風險。基金價格可反覆波動，並可在一段短時期內顯著下跌。閣下於本基金的投資可能會價值全失。• 本基金可使用衍生工具達到對沖及有效基金管理的目的，這可能涉及額外風險。在不利情況下，本基金使用的衍生工具未必能夠有效地達到對沖或有效基金管理的目的，且本基金可能會遭受重大損失。• 本基金可從資本中或實際上以資本撥付派息(此舉可構成部分退回或撤回投資者原本的投資)或來自原本投資應佔的任何資本收益，由此即時減低每股資產淨值。• 投資者不應只依賴本文件而作出投資決定。",
    "min_holding": {
        "lc": 8000,
        "fc": 1000
    },
    "investment_objective": "'本基金主要透過分散投資於以美元計值的固定收益證券，以獲取與保本相符的高收益。本基金只投資於以美元計值的固定收益證券，包括由美國境外及境內註冊發行商發行的投資級別及非投資級別高收益證券。在正常市場情況下，最少50%的投資組合資產將投資於投資級別的證券。而至少有65%之資產，必須由美國境內之機構發行。AB FCP I 旗下的一個投資組合。AB FCP I (即 “AB”)是根據盧森堡法律組成的本互惠投資基金(fonds commun de placement) 。 在 2016 年 2 月 5 日之前，基金的法定名稱為 ACMBernstein，營業名稱為 AllianceBernstein。",
    "min_invest_initial": {
        "lc": 8000,
        "fc": 1000
    },
    "yp": {
        "latest_year": 2016,
        "fc": {
            "2y": -2.58,
            "5y": 9.5,
            "4y": -1.49,
            "1y": 7.76,
            "3y": 5.99
        },
        "lc": {
            "2y": -2.66,
            "5y": 9.22,
            "4y": -1.45,
            "1y": 7.82,
            "3y": 6.03
        }
    },
    "redemption_fee": 100,
    "launch_date": "2002-09-16",
    "category": "FI",
    "sharp_ratio": {
        "lc": 0.91,
        "fc": 0.85
    },
    "volatility": {
        "lc": 3.76,
        "fc": 3.9
    },
    "risk_rating": 3,
    "lang": "ch",
    "min_invest_rsp": {
        "lc": 1000,
        "fc": 150
    },
    "launch_price": 8.04,
    "name": "AB FCP I - 美元收益基金 (美元) AT",
    "sector": "USD"
}
```

- Fund Documents Output (Topic: `lion-funds.docs`)

```json
{"type":"prospectus","ref":"170948","code":"HKABGB2","lang":"ch"}
```


- Chart Data Output(Topic: `lion-funds.charts`)

See: [chart_data.json](https://github.com/hustshawn/funds-crawler/blob/master/chart_data.json)
