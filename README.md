# athena-dnssplunkapp

## Introduction
An app based on the DNSPython package in python which adds commands to run DNS queries of different types such as MX, TXT, CNAME, A

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

Hence, copy the contents for dnspython from the folders in this repo to the following folders in Splunk:

* For Python 2.X

```
sudo cp -r ./dnspython2/* $SPLUNK_HOME/lib/python2.7/site-packages
chown -R splunk:splunk $SPLUNK_HOME/lib/python2.7/site-packages/dns*
```

* For Python 3.X

```
sudo cp -r ./dnspython3/* $SPLUNK_HOME/lib/python3.7/site-packages
chown -R splunk:splunk $SPLUNK_HOME/lib/python3.7/site-packages/dns*
```

### Install App
Install the Splunk App by downloading the `.tar.gz` file from the Releases section of this repository

Once the app is installed, restart Splunk instance from `Settings` > `Server Controls`

### Testing dnsquery

Go to the DNS App for Splunk app, and run the query to get the TXT records for the domain `www.google.com`:
```
| makeresults
| eval domain="google.com"
| dnsquery domainfield=domain qtype="TXT"
```

## App On Splunkbase
This App has been submitted on Splunkbase and is located (here)[https://splunkbase.splunk.com/app/4879/].

## Development/Contributing 
This section provides misc references/tips that were used in development for this application:

### To login as root user inside splunk container
Use sudo with the following command:
```
sudo /bin/bash 
```

### To execute commands as a splunk user
The following steps will execute command `whoami` as a `splunk` user
```
sudo /bin/bash
    $SPLUNK_HOME/bin/splunk cmd whoami
```

### Packaging the App 
To package the app, we use `slim` tool through the following command which also the generates the app manifest automatically:
```
/opt/splunk/bin/slim package dnssplunkapp
```

### References
The following references were used to develop this app:
* (Creating Custom Search Command)[https://dev.splunk.com/enterprise/docs/developapps/customsearchcommands/createcustomsearchcmd/]
* (Create custom search commands for apps or add-ons in Splunk Enterprise)[https://dev.splunk.com/enterprise/docs/developapps/customsearchcommands/]
* (Testing Custom Splunk Commands inside/outside Splunk)[https://www.splunk.com/en_us/blog/tips-and-tricks/building-custom-search-commands-in-python-part-i-a-simple-generating-command.html]

