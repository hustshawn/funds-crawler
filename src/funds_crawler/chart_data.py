from kafka import KafkaProducer
import ujson as json
import logging
import os
import requests
import traceback
from settings import KAFKA_HOSTS, TOPIC_FUNDS_CHART_DATA
from multiprocessing import Pool
from multiprocessing import Manager, Process
from logger import get_logger
# TOPIC_FUNDS_CHART_DATA = 'test'
class ChartDataCrawler(object):

    def __init__(self, *args, **kwargs):
        self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_HOSTS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        self.logger = get_logger('Charts', 'charts.log')
        self.logger.info("Ready to send msg to KAFKA_HOSTS: {}".format(KAFKA_HOSTS))

    def _get_chart_data(self, code, timespan='month6', full=None):
        """
        Get the chart data

        if full was given, then query all timespans chart data
        if full was not given or none, query by timespan, the timespan is 
        'month6' by default.
        """
        data = []
        if full:
            timespans = [
                'ytd',
                'lastyear',
                'week1',
                'month1',
                'month3',
                'month6',
                'year1',
                'year2',
                'year3',
                'year5',
                'year10',
            ]
            jobs = []
            manager = Manager()
            return_dict = manager.dict()
            for span in timespans:
                # data.append(p.apply_async(self._make_chart_request_per_span, args=(code, span, return_dict)))
                p = Process(target=self._make_chart_request_per_span, args=(code, span, return_dict))
                jobs.append(p)
                p.start()
            for proc in jobs:
                proc.join()
            return return_dict.values()
            # self.logger.info(json.dumps(return_dict.values()))

        else:
            timespan = timespan if timespan else 'month6'
            data.append(self._make_chart_data_request(code, timespan))
        return data

    def _make_chart_request_per_span(self, code, span, return_dict):
        result = self._make_chart_data_request(code, span)
        result['type'] = span
        # return result
        return_dict[span] = result

    def _make_chart_data_request(self, code, timespan):
        data = {}
        urls_map = {
            'cum_perf': "http://www.fundsupermart.com.hk/hk/main/fundinfo/generateChartDataSeries.svdo",
            'bid_val': 'http://www.fundsupermart.com.hk/hk/main/fundinfo/generateChartBidValues.svdo',
            'avg_val': 'http://www.fundsupermart.com.hk/hk/main/fundinfo/generateChartMovingAverage.svdo'
        }
        result = {
            'type': timespan
        }
        avg_spans = '20,50,100,200'
        for key, url in urls_map.items():
            params = {
                "sedolnumber": code,
                "timeHorizon": timespan,
                "getHK": "N"
            }
            data_field = None
            # print("####### URL TO REQUEST {}".format(url))
            if key == 'cum_perf':
                params['sedolnumbers'] = params.pop('sedolnumber')
                data_field = 'chartData'
            elif key == 'avg_val':
                data_field = 'MovingAverageData'
                params['days'] = avg_spans

            fc_data = self._make_request(url, params, data_field=data_field)
            params['getHK'] = 'Y'
            lc_data = self._make_request(url, params, data_field=data_field)
            if key == 'avg_val':
                avg = {}
                for index, val in enumerate(avg_spans.split(',')):
                    avg = {
                        'fc': fc_data[index],
                        'lc': lc_data[index]
                    }
                    data['avg' + val] = avg
            elif key == 'bid_val':
                data[key] = {
                    'fc': json.dumps(fc_data),
                    'lc': json.dumps(lc_data),
                }
            else:
                data[key] = {
                    'fc': fc_data[0],
                    'lc': lc_data[0],
                }
        return data

    def _make_request(self, url, params, data_field=None):
        try:
            r = requests.get(url, params=params)
            msg = "[Make Request]#### URL: {}".format(r.url)
            self.logger.info(msg)
            res = r.json()
            if data_field:
                res = [d.get(data_field) for d in res]
            return res
        except Exception as err:
            self.logger.error(err)
            traceback.print_exc()
            return {}

    def _handle_fund(self, code):
        code = code.strip()
        chart_data = self._get_chart_data(code, full=True)
        out_data = {
            'code': code,
            'chart_data': chart_data
        }
        self.producer.send(TOPIC_FUNDS_CHART_DATA, out_data)
        self.logger.info("Sent chart data for {}".format(code))

    def process(self, code):
        code = code.strip()
        chart_data = self._get_chart_data(code, full=True)
        out_data = {
            'code': code,
            'chart_data': chart_data
        }
        self.producer.send(TOPIC_FUNDS_CHART_DATA, out_data)
        self.producer.flush()
        self.logger.info("Sent chart data for {}".format(code))


if __name__ == '__main__':
    crawler = ChartDataCrawler()
    with open('code_list.txt', 'r') as f:
        for code in f:
            crawler.process(code)
