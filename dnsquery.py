#!/usr/bin/env python

import sys
import os
import dns.resolver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators


@Configuration()
class DnsQueryCommand(StreamingCommand):
    """ Performs a DNS Query on a given domain within the input stream of events, and return the DNS answer in 
        specified answerfield

    ##Syntax
    
        .. code-block::
            | dnsquery domainfield=<field> qtype=<query-type e.g. A|MX|TXT|CNAME> answerfield=[field e.g. 'answer']

    ##Description
    
    Performs a DNS Query on a given domain specified by the domainfield, and returns the response via python's dnspython package

    ##Example
    
    Perform MX query on each domain in input lookup file `domainsfile` in `answerfield`
        | inputlookup domainsfile | dnsquery domainfield=domain qtype=MX answerfield=answer
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
        default="answer")

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

    def query_dns(self, domain, qtype, timeout, retries):

        # var to store the DNS answer
        answer = ""

        # 
        is_answer_obtained = False
        
        # number of attempts made 
        attempt = 0
        while not is_answer_obtained and attempt < retries:
            try:
                # increment attempt as dns resolution about to be attempted
                attempt += 1

                # Perform the DNS query
                answer_objects = dns.resolver.query(domain,
                                                    qtype, lifetime=timeout)
                
                # Get the answers and return
                answer = '\n'.join([answer_object.to_text() for answer_object in answer_objects])

                # Have we obtained the response for DNS resolution
                is_answer_obtained = True
            
            except dns.resolver.Timeout as e:
                error = "Timeout occurred for DNS query: {} -> {}. Error: {}. Command Line: %s".format(qtype, domain, str(e))
                self.logger.debug(error, self) 
                
                # Timeout occurred so we didn't get a response
                is_answer_obtained = False

            except Exception as e:
                # Throw an error and return answer unknown
                error = "Could not execute DNS query: {} -> {}. Error: {}. Command Line: %s".format(qtype, domain, str(e))
                self.logger.debug(error, self) 
                answer = "-"

        return answer

    def stream(self, records):
        
        # Process each record
        for record in records:

            # if no domain value, then provide empty dns answer
            answer = ""

            if self.domainfield in record:
                # Get the domain to resolve from existing streamed record
                domain = record[self.domainfield]

                # Get the DNS query reply for the domain
                answer = self.query_dns(domain, self.qtype, int(self.timeout), int(self.retries))
            
            # Put the response in the output record
            record[self.answerfield] = answer
            
            # Return the record/response to user
            yield record

dispatch(DnsQueryCommand, sys.argv, sys.stdin, sys.stdout, __name__)

