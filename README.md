# athena-dnssplunkapp

## Introduction
An app based on the DNSPython package in python which adds commands to run DNS queries of different types

## Setup
Note that the instructions below assume that `athena-dnssplunkapp` has been git cloned in the /opt directory on a Linux host.

## Install Splunk Docker container (Optional)
Optional step to setup a Splunk environment for testing. If you already have a Splunk Search-head/indexer, this step is not required.

* Pull Docker image

```
docker pull splunk/splunk:latest
```

* Build the container with password `Splunk123$`

```
docker run -v /opt/athena-dnssplunkapp:/opt/athena-dnssplunkapp -d -p 8000:8000 -e "SPLUNK_START_ARGS=--accept-license" -e "SPLUNK_PASSWORD=Splunk123$" --name splunk splunk/splunk:latest
```

### Pre-requisite: Installing dnspython
Before installing the app, it is mandatory that `dnspython` package is installed on the Splunk server/container as the commands that this Splunk App introduces rely on that. 

```
sudo python -m pip install dnspython
```

If using `python3`, it is  recommended to also run the command below:
```
sudo python3 -m pip install dnspython
```

## Development/Contributing 

### To login as root user inside splunk
Use sudo with the following command:
```
sudo /bin/bash 
```

### Testing dnsquery

Go to the DNS App for Splunk app, and run the query
```
| makeresults | eval domain="www.google.com" | dnsquery domainfield=domain qtype="A"
```

### References
The following references were used to develop this app:
* (Creating Custom Search Command)[https://dev.splunk.com/enterprise/docs/developapps/customsearchcommands/createcustomsearchcmd/]
* (Create custom search commands for apps or add-ons in Splunk Enterprise)[https://dev.splunk.com/enterprise/docs/developapps/customsearchcommands/]
* (Testing Custom Splunk Commands inside/outside Splunk)[https://www.splunk.com/en_us/blog/tips-and-tricks/building-custom-search-commands-in-python-part-i-a-simple-generating-command.html]
