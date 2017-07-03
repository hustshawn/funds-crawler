# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FundsCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    lang = scrapy.Field()
    code = scrapy.Field()
    name = scrapy.Field()
    investment_objective = scrapy.Field()
    risk_statement = scrapy.Field()
    category = scrapy.Field()
    min_invest_initial = scrapy.Field()
    sector = scrapy.Field()
    min_invest_subs = scrapy.Field()
    region = scrapy.Field()
    min_invest_rsp = scrapy.Field()
    launch_price = scrapy.Field()
    launch_date = scrapy.Field()
    redemption_fee = scrapy.Field()
    min_holding = scrapy.Field()
    price_basis = scrapy.Field()
    latest_nav_val = scrapy.Field()
    latest_nav_date = scrapy.Field()
    fund_size_date = scrapy.Field()
    fund_size_val = scrapy.Field()
    volatility = scrapy.Field()
    sharp_ratio = scrapy.Field()
    risk_rating = scrapy.Field()
    company = scrapy.Field()
    currency = scrapy.Field()
    # Cumulative performance
    cp = scrapy.Field()
    # Yearly performance
    yp = scrapy.Field()
    # Historical price
    hist_price = scrapy.Field()
    docs = scrapy.Field()
    # Chart data
    chart_data = scrapy.Field()

    # Currently not required
    total_net_assets = scrapy.Field()
    manager_name = scrapy.Field()
    management_fee = scrapy.Field()
    front_load_fee = scrapy.Field()
    switching_fee = scrapy.Field()
    min_invest_additional = scrapy.Field()