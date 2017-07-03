# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import os
import subprocess

from kafka import KafkaProducer
import ujson as json
import _pickle as pickle

from .settings import KAFKA_HOSTS, TOPIC_FUNDS_INFO, TOPIC_FUNDS_DOCS_INCOMING


class LionBasePipeline(object):

    def __init__(self, *args, **kwargs):
        self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_HOSTS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
    @property
    def logger(self):
        logger = logging.getLogger(__name__)
        return logging.LoggerAdapter(logger, {'spider': self})
    
    def process_item(self, item, spider):
        raise NotImplementedError("Please implement process_item() for the pipline")

class FundsCrawlerPipeline(LionBasePipeline):

    def process_item(self, item, spider):
        out_fn = 'result.json'
        item = dict(item)
        docs = item.pop('docs')
        docs_msg = {
            'code': item['code'],
            'docs': docs,
            'lang': item['lang']
        }
        self.producer.send(TOPIC_FUNDS_INFO, dict(item))
        self.producer.send(TOPIC_FUNDS_DOCS_INCOMING, docs_msg)
        self.producer.flush()
        print("DOCS IN PIPLINE {0}, TOPIC: {1}".format(docs_msg, TOPIC_FUNDS_DOCS_INCOMING))
        self.logger.info("##DOCS IN PIPLINE {0}, TOPIC: {1}".format(docs_msg, TOPIC_FUNDS_DOCS_INCOMING))
        return item
