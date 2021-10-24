#!/usr/bin/env python

import sys
import os

import logging, logging.handlers
import splunk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators
import dns.resolver

def setup_logging():
    """Setup the logging via the python logging"""
    logger = logging.getLogger('splunk.dnsquery')
    SPLUNK_HOME = os.environ['SPLUNK_HOME']
    
    LOGGING_DEFAULT_CONFIG_FILE = os.path.join(SPLUNK_HOME, 'etc', 'log.cfg')
    LOGGING_LOCAL_CONFIG_FILE = os.path.join(SPLUNK_HOME, 'etc', 'log-local.cfg')
    LOGGING_STANZA_NAME = 'python'
    LOGGING_FILE_NAME = "dnsquery.log"
    BASE_LOG_PATH = os.path.join('var', 'log', 'splunk')
    LOGGING_FORMAT = "%(asctime)s %(levelname)-s\t%(module)s:%(lineno)d - %(message)s"
    splunk_log_handler = logging.handlers.RotatingFileHandler(os.path.join(SPLUNK_HOME, BASE_LOG_PATH, LOGGING_FILE_NAME), mode='a') 
    splunk_log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logger.addHandler(splunk_log_handler)
    splunk.setupSplunkLogger(logger, LOGGING_DEFAULT_CONFIG_FILE, LOGGING_LOCAL_CONFIG_FILE, LOGGING_STANZA_NAME)
    return logger


@Configuration()
class DnsQueryCommand(StreamingCommand):
    """ Performs a DNS Query on a given domain within the input stream of events, and return the DNS answer in 
        specified answerfield

    ##Syntax
    
        .. code-block::
            | dnsquery domainfield=<field> qtype=<query-type e.g. A|MX|TXT|CNAME> [answerfield=<field e.g. 'dns_answer'>] [timeout=<int e.g. 2>] [retries=<int e.g. 2>] [dnserrorfield=<field e.g. 'dns_error'>] [nss=<nameservers e.g. 8.8.8.8,8.8.4.4>]

    ##Description
    
    Performs a DNS Query on a given domain specified by the domainfield, and returns the response via python's dnspython package.
    By default, the default nameservers are used, otherwise, custom nameservers are used for resolution by supplying them with 'nss' argument.

    ##Example
    
    Perform MX query on each domain in input lookup file `domainsfile` in `answerfield`
        | inputlookup domainsfile | dnsquery domainfield=domain qtype=MX answerfield=answer

    Perform MX query on each domain in input lookup file `domainsfile` in `answerfield` using custom nameserver '8.8.8.8'
            | inputlookup domainsfile | dnsquery domainfield=domain qtype=MX answerfield=answer nss=8.8.8.8
    """

    domainfield = Option(
        doc='''
        **Syntax:** **domainfield=***<domainfield>*
        **Description:** Name of the field that will hold domain name for resolution''',
        require=True, 
        validate=validators.Fieldname())

    qtype = Option(
        doc='''
        **Syntax:** **qtype=***<qtype>*
        **Description:** Type of DNS query to perform e.g. A|MX|CNAME|TXT''',
        require=True,)

    answerfield = Option(
        doc='''
        **Syntax:** **domainfield=***<domainfield>*
        **Description:** Name of the field that will hold the answer''',
        default="dns_answer")

    timeout = Option(
        doc='''
        **Syntax:** **timeout=***<timeout>*
        **Description:** Timeout for DNS query resolution''',
        default="2")

    retries= Option(
        doc='''
        **Syntax:** **retries=***<int>*
        **Description:** Number of retries when timeout occurs for DNS resolution''',
        default="2")
    
    dnserrorfield = Option(
        doc='''
        **Syntax:** **dnserrorfield=***<dnserrorfield>*
        **Description:** Name of the field in which to write the DNS resolution error''',
        default="dns_error")

    nss = Option(
        doc='''
        **Syntax:** **nss=***<nameservers>*>
        **Description** Nameserver(s) to use for DNS resolution. By default, default nameservers are used for resolution''',
        default="default"
    )

    # Setup the logging
    logger = setup_logging()

    def query_dns(self, domain, qtype, timeout, retries, nss):

        # Store the DNS reply
        answer = ""

        # Captures the DNS error response
        dns_error_val = ""

        # Tracks if dns resolution occurred
        is_answer_obtained = False
        
        # number of attempts made 
        attempt = 0

        while not is_answer_obtained and attempt < retries:
            try:
                # increment attempt as dns resolution about to be attempted
                attempt += 1
                
                # tell user that we are attempting to perform dns resolution for a domain
                log_message = "Attempting DNS query: {} -> {}, attempt: {} with nameservers: {}".format(qtype, domain, attempt, nss)
                self.logger.info(log_message)
                
                # Set the resolving nameservers, if provided
                if not (nss == "" or nss == "none" or nss == "default"):
                    resolver = dns.resolver.Resolver(configure=False)
                    nss_raw = nss.split(",")
                    nss = [ ns.strip() for ns in nss_raw ]
                    resolver.nameservers = nss
                    # Perform the DNS query with custom resolver with custom nameservers
                    answer_objects = resolver.query(domain,
                                                    qtype, lifetime=timeout)
                else:
                    # Perform the DNS query with default resolver
                    answer_objects = dns.resolver.query(domain,
                                                        qtype, lifetime=timeout)
                
                # Get the answers and return
                answer = '\n'.join([answer_object.to_text() for answer_object in answer_objects])

                # Have we obtained the response for DNS resolution
                is_answer_obtained = True
            
            except dns.resolver.Timeout as e:
                dns_error_val = "Timeout occurred for DNS query: {} -> {}. Error: {}".format(qtype, domain, str(e))
                self.logger.info(dns_error_val) 
                
                # Timeout occurred so we didn't get a response
                is_answer_obtained = False

            except Exception as e:
                # Throw an error and return answer unknown
                dns_error_val = "Could not execute DNS query: {} -> {}. Error: {}".format(qtype, domain, str(e))
                self.logger.info(dns_error_val)
                answer = "-"

        return (answer, dns_error_val)

    def stream(self, records):

        # Process each record
        for record in records:

            # stores dns query resolution response
            answer = ""

            # stores error for dns resolution
            dns_error = ""

            if self.domainfield in record:
                # Get the domain to resolve from existing streamed record
                domain = record[self.domainfield]

                # Get the DNS query reply for the domain
                answer, dns_error = self.query_dns(domain, self.qtype, int(self.timeout), int(self.retries), self.nss)
            
            # Put the response in the output record
            record[self.answerfield] = answer

            # Put the DNS error
            record[self.dnserrorfield] = dns_error
            
            # Return the record/response to user
            yield record

dispatch(DnsQueryCommand, sys.argv, sys.stdin, sys.stdout, __name__)

