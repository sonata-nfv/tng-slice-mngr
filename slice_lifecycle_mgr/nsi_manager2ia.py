#!/usr/local/bin/python3.4

"""
## Copyright (c) 2015 SONATA-NFV, 2017 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).
"""
# # List of topics that are used by the Network Slice Manager for its rabbitMQ communication

import os, sys, logging, datetime, uuid, time, json, pika

# Topics in the infrastructure adaptor (IA)
IA_VIM_LIST = 'infrastructure.management.compute.list'
IA_NSI_PREP = 'infrastructure.slice.prepare'
IA_NSI_REMO = 'infrastructure.slice.remove'

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}


def return_vim_list(msg, vim_list):
  LOG.info("This is the msg from the IA.msg: " + str(msg))
  vim_list.append(msg)
  return vim_list

# Coonnects and subscribes to receive the latest information about the VIM list within the IA
def get VIM_list():
  #list with all the VIMs information associated to the SP
  vim_list = []

  # Access the IA environment variable and parse it
  url = os.environ.get("SONATA_IA_BROKER_URI")
  params = pika.URLParameters(url)
  connection = pika.BlockingConnection(params)
  channel = connection.channel() # start a channel
  channel.queue_declare(queue=IA_VIM_LIST) # Declare a queue

  # create a function which is called on incoming messages
  def callback(ch, method, properties, body):
      return_vim_list(body, vim_list)

  # set up subscription on the queue
  channel.basic_consume(callback, queue=IA_VIM_LIST, no_ack=True)

  # start consuming (blocks)
  channel.start_consuming()

  # when there are no more messages, closes the connection
  connection.close()

  LOG.info("This is the msg from the IA.vim_list: " + str(vim_list))
  return vim_list