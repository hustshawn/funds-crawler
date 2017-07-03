#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:/usr/src/app/funds-crawler"
scrapy crawl fsm
