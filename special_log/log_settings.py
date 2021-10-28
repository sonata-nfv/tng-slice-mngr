#!/usr/local/bin/python3.4
 
import os, sys, logging, json, argparse, time, datetime, requests, uuid

def init_logging():
    global deplogger
    
    # Create a custom logger
    deplogger = logging.getLogger('slicemngr_deploylog')
    deplogger.setLevel(logging.DEBUG)
    

    # Create handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    date = datetime.date.today()
    f_handler = logging.FileHandler('sonata_filebeat.log')
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    format = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(lineno)s - %(app_name)s %(message)s')
    c_handler.setFormatter(format)
    f_handler.setFormatter(format)

    # Add handlers to the logger
    deplogger.addHandler(c_handler)
    deplogger.addHandler(f_handler)
    extra = {'app_name':'PROFILING'}
    deplogger = logging.LoggerAdapter(deplogger, extra)

    #2021-09-23 16:33:09,385 DEBUG slicemngr_deploylog:36 - PROFILING SONATA_SLICER_93e37130-76c6-4341-860b-c0e79db1d60c_SONATA_SLICE_INSTANTIATION_START 1632813920.299359"
    # specific content --> SONATA_SLICER_93e37130-76c6-4341-860b-c0e79db1d60c_SONATA_SLICE_INSTANTIATION_START 1632813920.299359