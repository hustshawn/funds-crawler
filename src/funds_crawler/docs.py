# -*- coding: utf-8 -*-

# Handle the funds docs here
#
import requests
from retrying import retry
from kafka import KafkaConsumer, KafkaProducer
import ujson as json

import logging
from multiprocessing import Process, Pool
import os
import re
import subprocess
import traceback

from logger import get_logger
from settings import KAFKA_HOSTS, TOPIC_FUNDS_DOCS, CMS_HOST, TOPIC_FUNDS_DOCS_INCOMING, CMS_TOKEN

CMS_ENDPOINT = '/wp-json/lion-cms/v1/fund_document'
QUERY_ENDPOINT = '/wp-json/lion-cms/v1/posts'
MEDIA_ENDPOINT = '/wp-json/lion-cms/v1/media'

CMS_MEDIA_URL = 'http://' + CMS_HOST + MEDIA_ENDPOINT
CMS_POST_URL = 'http://' + CMS_HOST + CMS_ENDPOINT
CMS_QUERY_URL = 'http://' + CMS_HOST + QUERY_ENDPOINT


def download_doc(url):
    fn = url.split('/')[-1]
    try:
        logger.debug("Downloading {}...".format(url))
        r = requests.get(url, stream=True)
        with open(fn, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
        logger.debug("Download finished. {}".format(fn))
        return fn
    except Exception as err:
        msg = "Downloading file from url %s has some error, begin to retry...".format(url)
        logger.error(msg)
        pass

def doc_exists(slug):
    url = CMS_QUERY_URL
    try:
        r = requests.get(url, params={'slug': slug})
        if r.status_code == 200 and r.json():
            logger.info("DOC EXISTS: {}".format(slug))
            return r.json()[0].get('id'), True
    except Exception as err:
        logger.error(err)
        traceback.print_exc()
    logger.info("DOC DOES NOT EXISTS! {}".format(slug))
    return None, False

def get_headers(filename):
    f_type = filename.split('.')[-1].lower()
    c_type = 'multipart/form-data'
    content_disposition = 'attachment; filename=\"' + filename +'\"'
    headers = {
        'content-type': c_type,
        'content-disposition':content_disposition
    }
    return headers

@retry(stop_max_attempt_number=3)
def upload_doc(doc_name):
    upload_fail = False
    with open(doc_name, 'rb') as f:
        url = CMS_MEDIA_URL
        logger.debug("Uploading url: {}".format(url))
        headers = get_headers(doc_name)
        try:
            logger.debug("Uploading doc {0}".format(doc_name))
            r = requests.post(url, headers=headers, data=f, params={'access_token': CMS_TOKEN})
            # logger.debug("Uploading request: {0} , Response: {1}".format(r.url, r.json()))
            if r.status_code == 201:
                media_id = r.json().get('id')
                logger.info("Upload {0} successful, Media ID:{1}".format(doc_name, media_id))
                return media_id, upload_fail
            else:
                logger.warning("File upload not successful, may blocked by remote server somehow. Code: {0} {1}".format(r.status_code ,r.text))
                upload_fail = True
        except Exception as err:
            logger.error("Upload file error: {0}  Response: {1}".format(err, r.text))
            traceback.print_exc()
            upload_fail = True
    media_id = None
    try:
        os.remove(doc_name)
    except Exception as err:
        self.logger.error(err)
        pass
    return media_id, upload_fail

def prepare_post_data(code, slug, doc_id):
    return {
        'slug': slug,
        'title': slug,
        'content': slug,
        'funds': [code],
        'attachments': [doc_id],
        'status': 'publish'
    }

def post_cms(code, slug, doc_id):
    data = prepare_post_data(code, slug, doc_id)
    url = CMS_POST_URL
    # http://cms-sit-feeding.lionfin.co/wp-json/lion-cms/v1/fund_document?access_token=BuAOiwR1xWRbuXjWXGQkDt9LBy0YMD
    try:
        logger.info("Posting data to CMS: {}".format(data))
        r = requests.post(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'}, params={'access_token': CMS_TOKEN})
        if r.status_code == 200 | 201:
            post_id = r.json().get('id')
            logger.info("CMS POST OK! ID:{}".format(post_id))
        elif r.status_code == 400:
            res_msg = r.json().get('data')
            if res_msg:
                post_id = res_msg.get('postId', '')
            else:
                post_id = ''
            logger.error("[CMS POST] Response code: %s" % r.json().get('code', ''))
        else:
            post_id = ''
            logger.error("[CMS POST] Response with other status code: {}".format(r.status_code))
    except Exception as error:
        logger.error("POST ERROR  DATA: {0}  Response:{1}".format(json.dumps(data), r.text))
        logger.debug("Response: {}".format(r.text))
        post_id = ''
    return post_id

def handle_document(url, code, lang):
    # logger.info("Handling msg")
    doc_type = ''.join(re.findall('buy/(\w+)/*.*', url)).strip()
    fname = url.split('/')[-1]
    slug = '-'.join([code, lang, doc_type, fname.split('.')[0]])
    ref, has_doc = doc_exists(slug)
    if not has_doc:
        ref = None
        doc_name = download_doc(url)
        doc_id, upload_fail = upload_doc(doc_name)
        if upload_fail:
            return
        if doc_id:
            ref = post_cms(code, slug, doc_id)
    if ref:
        msg = {
            'type': doc_type,
            'code': code,
            'lang': lang,
            'ref': str(ref)
        }
        producer = KafkaProducer(bootstrap_servers=KAFKA_HOSTS, \
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        future = producer.send(TOPIC_FUNDS_DOCS, msg)
        logger.info("TOPIC: {1}; Send Message: {0},  Future value: {2}, Succeed: {3}".format(msg, TOPIC_FUNDS_DOCS, future.value, future.succeeded()))
        producer.flush()

if __name__ == "__main__":
    logger = get_logger('docs', 'docs.log')
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_HOSTS, \
        value_deserializer=lambda x: json.loads(x)
        )
    consumer.subscribe(TOPIC_FUNDS_DOCS_INCOMING)
    logger.info("Listenning to the KAFKA_HOSTS: {0} with TOPIC: {1}".format(KAFKA_HOSTS, TOPIC_FUNDS_DOCS_INCOMING))

    for msg in consumer:
        logger.info("Recieved msg: {}".format(msg.value))
        code = msg.value.get('code')
        lang = msg.value.get('lang')
        docs_url = msg.value.get('docs')

        # Use process pool
        doc_names = []
        pool = Pool(len(docs_url))
        for url in docs_url:
            procs = []
            pool.apply_async(handle_document, args=(url, code, lang))
            doc_names.append(url.split('/')[-1])
        pool.close()
        pool.join()
