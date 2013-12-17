import httplib
import xml.dom.minidom
import logging
import sys
import datetime
from django.conf import settings

if hasattr(settings, 'ICAT_DOMAIN'):
    ICAT_DOMAIN = settings.ICAT_DOMAIN
    ICAT_PORT = settings.ICAT_PORT
else:
    logging.error("App settings does not contain ICAT server info: using icat.sns.gov:2080")
    ICAT_DOMAIN = 'icat.sns.gov'
    ICAT_PORT = 2080

def get_text_from_xml(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def decode_time(timestamp):
    """
        Decode timestamp and return a datetime object
    """
    try:
        tz_location = timestamp.rfind('+')
        if tz_location<0:
            tz_location = timestamp.rfind('-')
        if tz_location>0:
            date_time_str = timestamp[:tz_location]
            tz_str = timestamp[tz_location:]
            try:
                return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S")
    except:
        logging.error("Could not parse timestamp '%s': %s" % (timestamp, sys.exc_value))
        return None

def get_ipts_info(instrument, ipts):
    run_info = {}
    
    # Get basic run info
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/%s/meta' % (instrument.upper(),
                                                                         ipts.upper()))
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        metadata = dom.getElementsByTagName('metadata')
        if len(metadata)>0:
            for n in metadata[0].childNodes:
                # Run title
                if n.nodeName=='title' and n.hasChildNodes():
                    run_info['title'] = get_text_from_xml(n.childNodes)
                # IPTS
                if n.nodeName=='proposal' and n.hasChildNodes():
                    run_info['proposal'] = get_text_from_xml(n.childNodes)
                # Time
                if n.nodeName=='createTime' and n.hasChildNodes():
                    timestr = get_text_from_xml(n.childNodes)
                    run_info['createTime'] = decode_time(timestr)
    except:
        logging.error("Communication with ICAT server failed: %s" % sys.exc_value)
    
    # Get the range of runs
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/%s/' % (instrument.upper(),
                                                                     ipts.upper()))
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        runs = dom.getElementsByTagName('runs')
        if len(runs)>0:
            for n in runs[0].childNodes:
                # Run title
                if n.nodeName=='runRange' and n.hasChildNodes():
                    run_info['run_range'] = get_text_from_xml(n.childNodes)
    except:
        logging.error("Communication with ICAT server failed: %s" % sys.exc_value)
    return run_info
    
def get_instruments():
    """
    http://icat-testing.sns.gov:2080/icat-rest-ws/experiment/SNS
    """
    instruments = []
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/')
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        elements = dom.getElementsByTagName('instrument')
        for element in elements:
            instr = get_text_from_xml(element.childNodes)
            if not instr.upper().endswith('A'):
                instruments.append(instr)
    except:
        logging.error("Could not get list of instruments from ICAT: %s" % sys.exc_value)
    return instruments
    

def get_experiments(instrument):
    """
    http://icat-testing.sns.gov:2080/icat-rest-ws/experiment/SNS
    """
    experiments = []
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/' % instrument.upper())
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        elements = dom.getElementsByTagName('proposal')
        for element in elements:
            expt = get_text_from_xml(element.childNodes)
            experiments.append(expt)
    except:
        logging.error("Could not get list of instruments from ICAT: %s" % sys.exc_value)
    return experiments
    
    
def get_ipts_runs(instrument, ipts):
    """
        Get the list of runs and basic meta data for
        a given experiment
        @param instrument name [string]
        @param ipts: experiment name [string]
        
        <run id="12801">
            <title>Blank scanRT</title>
            <startTime>2013-04-05T16:17:56.246-04:00</startTime>
            <endTime>2013-04-05T16:40:12.938-04:00</endTime>
            <duration>1336.6914</duration>
            <protonCharge>1.20244649808e+12</protonCharge>
            <totalCounts>1.3197872E7</totalCounts>
        </run>
    """
    run_data = []
    # Get the range of runs
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=1.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/%s/all/' % (instrument.upper(),
                                                                     ipts.upper()))
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        for r in dom.getElementsByTagName('run'):
            run_info = {'id': r.attributes['id'].value}
            for n in r.childNodes:
                if n.hasChildNodes():
                    if n.nodeName in ['title']:
                        run_info[n.nodeName] = get_text_from_xml(n.childNodes)
                    elif n.nodeName in ['duration', 'protonCharge', 'totalCounts']:
                        text_value = get_text_from_xml(n.childNodes)
                        try:
                            run_info[n.nodeName] = "%.4G" % float(text_value)
                        except:
                            run_info[n.nodeName] = text_value
                    elif n.nodeName in ['startTime', 'endTime']:
                        text_value = get_text_from_xml(n.childNodes)
                        run_info[n.nodeName] = decode_time(text_value)
            run_data.append(run_info)
    except:
        logging.error("Communication with ICAT server failed: %s" % sys.exc_value)
    return run_data