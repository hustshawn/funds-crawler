import aiohttp
from kafka import KafkaProducer

import asyncio
from contextlib import closing
import logging
import json
import time
from urllib import parse
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
logger = logging.getLogger()

def get_chart_data(code, timespan='month6', full=None):

    CUM_URL_PATTERN = "https://secure.fundsupermart.com.hk/hk/main/fundinfo/generateChartDataSeries.svdo?sedolnumbers={}&timeHorizon={}&getHK=N"
    BID_URL_PATTERN = "https://secure.fundsupermart.com.hk/hk/main/fundinfo/generateChartBidValues.svdo?sedolnumber={}&timeHorizon={}&getHK=N"
    AVG_URL_PATTERN = "https://secure.fundsupermart.com.hk/hk/main/fundinfo/generateChartMovingAverage.svdo?days=20,50,100,200&sedolnumber={}&timeHorizon={}&getHK=N"

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
        urls = [CUM_URL_PATTERN.format(code, span) for span in timespans]
        urls += [BID_URL_PATTERN.format(code, span) for span in timespans]
        urls += [AVG_URL_PATTERN.format(code, span) for span in timespans]
    else:
        urls = [
            URL_PATTERN.format(code, timespan),
            BID_URL_PATTERN.format(code, timespan),
            ] 
    resp = batch_request(urls)
    result = {
        'code': code,
        'chartData': parse_data(resp, urls)
    }
    return result

def parse_data(resp, urls):
    result = {}
    for index, url in enumerate(urls):
        p = parse.urlparse(url)
        path = p.path
        q_params = parse.parse_qs(p.query)
        span = q_params['timeHorizon'][0]
        if 'ChartDataSeries' in path:
            data_field = 'chartData'
            if not result.get('cum_perf'):
                result['cum_perf'] = {}
            result['cum_perf'][span] = json.loads(json.loads(resp[index].strip())[0].get(data_field))
        elif 'ChartMovingAverage' in path:
            data_field = 'MovingAverageData'
            if not result.get('MovingAverageData'):
                result['MovingAverageData'] = {}
            data = json.loads(resp[index].strip())
            r = {
                'avg20': data[0].get(data_field),
                'avg50': data[1].get(data_field),
                'avg100': data[2].get(data_field),
                'avg200': data[3].get(data_field),
                }
            result['MovingAverageData'][span] = r
        else:
            if not result.get('ChartBidValues'):
                result['ChartBidValues'] = {}
            # Bid value
            data_field = ''
            data = json.loads(resp[index].strip())
            result['ChartBidValues'][span] = data
    return result

def batch_request(urls):
    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as session:
        tasks = [fetch_page(session, url) for url in urls]
        resp = loop.run_until_complete(asyncio.gather(*tasks))
    return resp

async def fetch_page(session, url):
    with aiohttp.Timeout(10):
        print("Requesting...", url)
        async with session.get(url) as response:
            assert response.status == 200
            return await response.text()

from settings import KAFKA_HOSTS, TOPIC_FUNDS_CHART_DATA

if __name__ == '__main__':
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_HOSTS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    with open('code_list.txt', 'r') as f:
        for code in f:
            data = get_chart_data(code, full=True)
            producer.send(TOPIC_FUNDS_CHART_DATA, data)
            producer.flush()
            logger.info("Sent chart data for {}".format(code))
