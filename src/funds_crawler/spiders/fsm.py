# -*- coding: utf-8 -*-
import scrapy
import requests

from datetime import datetime
import locale
import logging
import traceback

from funds_crawler.items import FundsCrawlerItem


DT_FORMAT_EN = "%B %d, %Y"
OUTPUT_DATE_FORMAT = "%Y-%m-%d"
RE_NUMBER = "(:?^|\s)(?=.)((?:0|(?:[1-9](?:\d*|\d{0,2}(?:,\d{3})*)))?(?:\.\d*[1-9])?)(?!\S)"
# This defines whether to generate funds-code list or not
GEN_CODE_LIST = True

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

class FsmSpider(scrapy.Spider):
    """
    The spider to crawl fundsupermart.com.hk
    """
    name = "fsm"
    allowed_domains = ["fundsupermart.com.hk"]
    start_urls = ['http://www.fundsupermart.com.hk/hk/main/fundinfo/generateTable.svdo?lang=en&returns=performanceTable']

    def log(self, message, level=logging.INFO, **kw):
        self.logger.log(level, message, **kw)

    def start_requests(self):
        return [scrapy.Request(url) for url in self.start_urls]

    def parse(self, response):
        XPATH_ENTRY = "//table[2]/tr[position()>4]"
        REL_XPATH_LINK = "*/a/@href"
        REL_XPATH_CURRENCY = "td[4]/font/text()"
        REL_XPATH_CODE = "td[1]/input/@value"
        entry_selectors = response.xpath(XPATH_ENTRY)
        f = open('code_list.txt', 'w')
        for lang in ('ch', 'zh', 'en'):
            for row in entry_selectors:
                link = ''.join(row.xpath(REL_XPATH_LINK).extract())
                code = ''.join(row.xpath(REL_XPATH_CODE).extract()).strip()
                if GEN_CODE_LIST:
                    f.write(code + '\n')
                currency = ''.join(row.xpath(REL_XPATH_CURRENCY).extract()).strip()
                # self.log("CURRENCY: {0}, LINK: {1}".format(currency, link))
                yield scrapy.Request(
                    self._make_request_url(response, link, lang), callback=self.parse_fund_page, 
                    meta={
                        'key': link.split('/')[-1],
                        'lang': lang,
                        'currency': currency,
                        'code': code
                })
        f.close()

    def _make_request_url(self, response, link, lang='zh'):
        return response.urljoin(link) + '?lang=' + lang

    def _extract_lc_fc(self, response, xpath_raw, regex):
        """
        A general shortcut function to extract fc and lc values.
        It always return a two factor tuple, eg. (a, b)
        If only one value extracted, then the two factors are same.
        eg. (a, a)
        """
        values = None
        values = response.xpath(xpath_raw).re(regex)
        values = [locale.atoi(v.strip()) for v in values]
        if len(values) == 2:
            return (values[0], values[1])
        elif len(values) == 1:
            return (values[0], values[:][0])
        else:
            self.logger.error("No valid values extracted.")
        return values

    def _dates_string_handler(self, dt_arr):
        if len(dt_arr) == 3:
            if len(dt_arr[1]) == 1:
                dt_arr[1] = '0' + dt_arr[1]
            if len(dt_arr[2]) == 1:
                dt_arr[2] = '0' + dt_arr[2]
        return '-'.join(dt_arr)

    def _get_fund_name(self, response, item):
        XPATH_NAME = "//div[@class='articlepg_title']/text()"
        item['name'] = ''.join(response.xpath(XPATH_NAME).extract()).strip()

    def _get_invest_obj(self, response, item):
        XPATH_INVEST_OBJ = "//font/table/tr/td/table[1]/tr/td/table/tr[1]/td/span[2]/font/text()"
        item['investment_objective'] = ''.join(response.xpath(XPATH_INVEST_OBJ).extract()).strip()

    def _get_risk_statement(self, response, item):
        XPATH_RISK_STATEMENT = "//font/table/tr/td/table[1]/tr/td/table/tr[1]/td/table/tr/td/span[2]/font/text()"
        item['risk_statement'] = ''.join(list(map(lambda x: x.strip(), response.xpath(XPATH_RISK_STATEMENT).extract()[:-1])))

    def _get_category(self, response, item):
        XPATH_CATEGORY = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[1]/td[2]/a/@href"
        RE_CATEGORY = "=(.+)"
        item['category'] = ''.join(response.xpath(XPATH_CATEGORY).re(RE_CATEGORY)).strip()

    def _get_min_invest_initial(self, response, item):
        XPATH_MIN_INVEST_INITIAL = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[1]/td[4]/text()"
        RE_MIN_INVEST_INITIAL = "\xa0(\w+,?\w+)"
        values = self._extract_lc_fc(response, XPATH_MIN_INVEST_INITIAL, RE_MIN_INVEST_INITIAL)
        item['min_invest_initial'] = {
            'lc': values[0] if values else None,
            'fc': values[1] if values else None 
        }
    def _get_sector(self, response, item):
        XPATH_SECTOR = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[2]/td[2]/a/@href"
        RE_SECTOR = "=(.+)"
        item['sector'] = ''.join(response.xpath(XPATH_SECTOR).re(RE_SECTOR)).strip()

    def _get_min_invest_subsequent(self, response, item):
        XPATH_MIN_INVEST_SUBS = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[2]/td[4]/text()"
        RE_MIN_INVEST_SUBS = "\xa0(\w+,?\w+)"
        values = self._extract_lc_fc(response, XPATH_MIN_INVEST_SUBS, RE_MIN_INVEST_SUBS)
        item['min_invest_subs'] = {
            'lc': values[0] if values else None,
            'fc': values[1] if values else None 
        }
    def _get_region(self, response, item):
        XPATH_REGION = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[3]/td[2]/a/@href"
        RE_REGION = "=(.+)"
        item['region'] = ''.join(response.xpath(XPATH_REGION).re(RE_REGION))

    def _get_min_invest_rsp(self, response, item):
        XPATH_MIN_INVEST_RSP = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[3]/td[4]/text()"
        RE_MIN_INVEST_RSP = "\xa0(\d+,?\d+)"
        values = self._extract_lc_fc(response, XPATH_MIN_INVEST_RSP, RE_MIN_INVEST_RSP)
        self.log("MIN INVEST VAL{}".format(values))
        item['min_invest_rsp'] = {
            'lc': values[0] if values else None,
            'fc': values[1] if values else None 
        }

    def _get_launch_info(self, response, item):
        XPATH_LAUNCH_DT = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[4]/td[2]/text()"
        RE_LAUNCH_DT = "(\d+)年(\d+)月(\d+)日"
        DT_FORMAT_EN = "%B %d, %Y"
        OUTPUT_DATE_FORMAT = "%Y-%m-%d"
        XPATH_LAUNCH_PRICE = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[5]/td[2]/text()"
        # RE_LAUNCH_PRICE = "(\d+\.\d+)"
        lang = response.meta['lang']
        try:
            lch_dt_raw = response.xpath(XPATH_LAUNCH_DT).extract()  
            launch_dt = datetime.strptime(lch_dt_raw[0], DT_FORMAT_EN).strftime(OUTPUT_DATE_FORMAT)
        except:
            self.log("PARSE CH DATE")
            lch_dt_raw = response.xpath(XPATH_LAUNCH_DT).re(RE_LAUNCH_DT)
            launch_dt = self._dates_string_handler(lch_dt_raw)
        
        # For debug only
        raw = response.xpath(XPATH_LAUNCH_DT).extract()
        self.log("PARSED RAW LAUNCH DATE: %s" %raw)
        
        launch_price = ''.join(response.xpath(XPATH_LAUNCH_PRICE).re(RE_NUMBER)).strip()
        self.log("LAUNCH PRICE: {}".format(launch_price))
        launch_price = locale.atof(launch_price) if launch_price else None
        item['launch_date'] = launch_dt
        item['launch_price'] = launch_price

    def _get_redemption_fee(self, response, item):
        XPATH_REDEMPTION_FEE = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[4]/td[4]/text()"
        # RE_REDEMPTION_FEE = "(\d+,?\d+)"
        redemption_fee = ''.join(response.xpath(XPATH_REDEMPTION_FEE).re(RE_NUMBER)).strip()
        item['redemption_fee'] = locale.atoi(redemption_fee) if redemption_fee else None

    def _get_min_holding(self, response, item):
        XPATH_MIN_HOLDING = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[5]/td[4]/text()"
        RE_MIN_HOLDING = "(\d+,?\d+)"
        values = self._extract_lc_fc(response, XPATH_MIN_HOLDING, RE_MIN_HOLDING)
        item['min_holding'] = {
            'fc': values[0] if values else None,
            'lc': values[1] if values else None
        }

    def _get_price_basis(self, response, item):
        XPATH_PRICE_BASIS = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[6]/td[2]/text()"
        item['price_basis'] = ''.join(response.xpath(XPATH_PRICE_BASIS).extract())

    def _get_latest_nav(self, response, item):
        XPATH_LATEST_NAV = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[6]/td[4]"
        RE_LATEST_NAV_VAL = "\s(\d+\.?\d+)<br>"
        RE_LATEST_NAV_DT = "as of\s(.+)\)|(\d+)年(\d+)月(\d+)日"
        nav_val = ''.join(response.xpath(XPATH_LATEST_NAV).re(RE_LATEST_NAV_VAL))
        nav_dt_raw = list(filter(lambda x: x, response.xpath(XPATH_LATEST_NAV).re(RE_LATEST_NAV_DT)))
        try:
            self.log("NAV DT RAW: %s" % nav_dt_raw)
            nav_dt = datetime.strptime(''.join(nav_dt_raw), DT_FORMAT_EN).strftime(OUTPUT_DATE_FORMAT)
        except:
            if len(nav_dt_raw) == 3:
                if len(nav_dt_raw[1]) == 1:
                    nav_dt_raw[1] = '0' + nav_dt_raw[1]
                if len(nav_dt_raw[2]) == 1:
                    nav_dt_raw[2] = '0' + nav_dt_raw[2]
            nav_dt = self._dates_string_handler(nav_dt_raw)
        item["latest_nav_val"] = locale.atof(nav_val)
        item["latest_nav_date"] = nav_dt

    def _get_risk_rating(self, response, item):
        XPATH_RISK_RATIING = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[7]/td[2]/a/@href"
        RE_RISK_RATING = "fsmRiskRating=(\d+)"
        item['risk_rating'] = locale.atoi(''.join(response.xpath(XPATH_RISK_RATIING).re(RE_RISK_RATING)))

    def _get_fund_size(self, response, item):
        XPATH_FUND_SIZE = "//td[@class='table_bdtext_style']/table/tr/td[@class='table_bdtext_style']/table/tr[3]/td/table/tr[7]/td[4]"
        RE_FUND_SIZE_VAL = "\w+\s(.+)<br>"
        RE_FUND_SIZE_DT = "as of\s(.+)\)|(\d+)年(\d+)月(\d+)日"
        fund_size_val = ''.join(response.xpath(XPATH_FUND_SIZE).re(RE_FUND_SIZE_VAL))
        fund_size_dt_raw = list(filter(lambda x: x, response.xpath(XPATH_FUND_SIZE).re(RE_FUND_SIZE_DT)))
        try:
            self.log("FUND DT RAW: %s" % fund_size_dt_raw)
            fund_size_dt = datetime.strptime(''.join(fund_size_dt_raw), DT_FORMAT_EN).strftime(OUTPUT_DATE_FORMAT)
        except:
            fund_size_dt = self._dates_string_handler(fund_size_dt_raw)

        self.log("FUND SIZE VAL {}".format(fund_size_val))
        if 'million' in fund_size_val:
            fund_size_val = locale.atof(fund_size_val.split(' million')[0]) * 10**6
        elif 'billion' in fund_size_val:
            fund_size_val = locale.atof(fund_size_val.split(' billion')[0]) * 10**9
        else:
            fund_size_val = locale.atoi(fund_size_val) if fund_size_val else None
        item['fund_size_val'] = fund_size_val
        item['fund_size_date'] = fund_size_dt


    def _get_cum_perf(self, response, item):

        XPATH_CUM_M_PERF = "//table/tr[2]/td/table/tr[3]/td/table[2]/tr/td/table/tr/td/font/table/tr/td/table[1]/tr/td/table/tr[16]/td/table"
        mon_base = response.xpath(XPATH_CUM_M_PERF)
        cum_mon_lc = mon_base.xpath('tr[3]')
        cum_mon_fc = mon_base.xpath("tr[4]")

        XPATH_CUM_YEAR_PERF = "//table/tr[2]/td/table/tr[3]/td/table[2]/tr/td/table/tr/td/font/table/tr/td/table[1]/tr/td/table/tr[17]/td/table"
        year_base = response.xpath(XPATH_CUM_YEAR_PERF)
        cum_year_lc = year_base.xpath('tr[2]')        
        cum_year_fc = year_base.xpath("tr[3]")

        item['cp'] = {
            'lc': {},
            'fc': {}
        }
        mon_map = {
            '1m': "td[2]/text()",
            '3m': "td[3]/text()",
            'ytd': "td[4]/text()",
            'since_lch': "td[5]/text()",
            }
        year_map = {
            '1y': "td[2]/text()",
            '2y': "td[3]/text()",
            '3y': "td[4]/text()",
            '4y': "td[5]/text()",
            '5y': "td[6]/text()"
        }

        for k, v in mon_map.items():
            lc_val = ''.join(cum_mon_lc.xpath(v).re("(\d+\.?\d+)")).strip()
            fc_val = ''.join(cum_mon_fc.xpath(v).re("(\d+\.?\d+)")).strip()
            item['cp']['lc'][k] = locale.atof(lc_val) if lc_val else None
            item['cp']['fc'][k] = locale.atof(fc_val) if fc_val else None

        for k, v in year_map.items():
            lc_val = ''.join(cum_year_lc.xpath(v).re("(\d+\.?\d+)")).strip()
            fc_val = ''.join(cum_year_fc.xpath(v).re("(\d+\.?\d+)")).strip()
            item['cp']['lc'][k] = locale.atof(lc_val) if lc_val else None
            item['cp']['fc'][k] = locale.atof(fc_val) if fc_val else None

    def _get_yearly_perf(self, response, item):
        XPATH_YEAR_PERF = "//table/tr[2]/td/table/tr[3]/td/table[2]/tr/td/table/tr/td/font/table/tr/td/table[2]"
        yp_base = response.xpath(XPATH_YEAR_PERF)
        yp_lc = yp_base.xpath("tr[3]")
        yp_fc = yp_base.xpath("tr[4]")

        latest_year = ''.join(yp_base.xpath("tr[2]/td[2]/text()").re("(\d{4})")).strip()
        item['yp'] = {
            'latest_year': locale.atoi(latest_year),
            'lc': {},
            'fc': {}
        }

        map_tb = {
            "1y": "td[2]/text()",
            "2y": "td[3]/text()",
            "3y": "td[4]/text()",
            "4y": "td[5]/text()",
            "5y": "td[6]/text()",
        }

        for k, v in map_tb.items():
            lc_val = ''.join(yp_lc.xpath(v).extract()).strip()
            item['yp']['lc'][k] = locale.atof(lc_val) if lc_val and lc_val != '-' else None
            fc_val = ''.join(yp_fc.xpath(v).extract()).strip()
            item['yp']['fc'][k] = locale.atof(fc_val) if fc_val and fc_val != '-' else None

    def _get_hist_price(self, response, item):
        XPATH_HIST_PRICE_BASE = "//table/tr[2]/td/table/tr[3]/td/table[2]/tr/td/table/tr/td/font/table/tr/td/table[3]/tr[3]"
        hp_row = response.xpath(XPATH_HIST_PRICE_BASE)

        mp = {
            '1y_high': "td[2]/a/text()",
            '1y_low': "td[3]/a/text()",
            '3y_high': "td[4]/a/text()",
            '3y_low': "td[5]/a/text()",
            'all_high': "td[6]/a/text()",
            'all_low': "td[7]/a/text()",
        }
        item['hist_price'] = {}
        for k, v in mp.items():
            val = ''.join(hp_row.xpath(v).extract()).strip()
            item['hist_price'][k] = locale.atof(val) if val else None
    
    def _get_volatil_n_sharp_ratio(self, response, item):
        XPATH_VOLATIL_N_SHARP_RATIO = "//table/tr[2]/td/table/tr[3]/td/table[2]/tr/td/table/tr/td/font/table/tr/td/table[1]/tr/td/table/tr[23]/td/table/tr[2]"
        # RE_VOTAIL_N_SHARP_RATIO = "(\d+\.?\d+%)"
        RE_VOLATIL_N_SHARP_RATIO = "(\d+\.?\d+)%\s\(|(\d+.?\d+)\s\("
        vot_sharp_raw = response.xpath(XPATH_VOLATIL_N_SHARP_RATIO).re(RE_VOLATIL_N_SHARP_RATIO)
        vals = list(filter(lambda x:x, vot_sharp_raw))
        if len(vals) == 4:
                
            item['volatility'] = {
                'lc': locale.atof(vals[0]),
                'fc': locale.atof(vals[1])
            }
            item['sharp_ratio'] = {
                'lc': locale.atof(vals[2]),
                'fc': locale.atof(vals[3])
            }
        elif len(vals) == 2:
            item['volatility'] = {
                'lc': locale.atof(vals[0]),
                'fc': locale.atof(vals[0])
            }
            item['sharp_ratio'] = {
                'lc': locale.atof(vals[1]),
                'fc': locale.atof(vals[1])
            }

    def _get_company_code(self, response, item):
        XPATH_COMP_CODE = "//tr[5]/td/p/a/@href"
        RE_COMP_CODE = "amgId=(\w+)"
        item['company'] = ''.join(response.xpath(XPATH_COMP_CODE).re(RE_COMP_CODE))
    
    def _get_funds_doc(self, response, item):
        XPATH_DOCS = "//td/table[4]/tr/td[2]/a/@href"
        item['docs'] = [ response.urljoin(link) for link in response.xpath(XPATH_DOCS).extract()]

    def parse_fund_page(self, response):
        self.log("Parse fund page: %s" % response.url)
        lang = response.meta.get('lang')
        code = response.meta.get('code')
        currency = response.meta.get('currency')

        item = FundsCrawlerItem()
        item['code'] = code
        item['lang'] = lang
        item['currency'] = currency
        self._get_fund_name(response, item)
        self._get_invest_obj(response, item)
        self._get_risk_statement(response, item)
        self._get_category(response, item)
        self._get_min_invest_initial(response, item)
        self._get_sector(response, item)
        self._get_min_invest_subsequent(response, item)
        self._get_region(response, item)
        self._get_min_invest_rsp(response, item)
        self._get_launch_info(response, item)
        self._get_redemption_fee(response, item)
        self._get_min_holding(response, item)
        self._get_price_basis(response, item)
        self._get_latest_nav(response, item)
        self._get_price_basis(response, item)
        self._get_risk_rating(response, item)
        self._get_fund_size(response, item)
        # Fund Performance
        self._get_cum_perf(response, item)
        self._get_yearly_perf(response, item)
        self._get_hist_price(response, item)
        self._get_volatil_n_sharp_ratio(response, item)
        self._get_company_code(response, item)
        self._get_funds_doc(response, item)
        yield item
