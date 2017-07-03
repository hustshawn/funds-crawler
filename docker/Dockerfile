FROM python:3.5
MAINTAINER Shawn Zhang <shawnzhang@lionfin.com.hk> @ Lion Finance

# Basic envrionment settings
RUN apt-get clean && apt-get update && mkdir -p /usr/src/ && apt-get install locales
RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && locale-gen
RUN echo "LC_ALL=en_US.UTF-8" >> /etc/environment 
WORKDIR /usr/src/app
COPY src/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Project setup
WORKDIR /usr/src/app/
# COPY docker/settings.py local_settings.py

CMD ["bash", "run.sh"]
