#!/usr/bin/python
"""
####################################################################################################

TITLE : HPE XP7 Migration, Monitor

DESCRIPTION :  Monitor daemon alerting in case there is a problem with the CaJ replication
    
AUTHOR : Koen Schets / StorageTeam

VERSION : Based on previous ODR framework
    1.0 Initial version

CONFIG : xpmig.ini

LOG : xpmig_monitor.log

TODO :
    Check all copy-groups in the dedicated HORCM files
    All volumes should be PAIR"ed
    Synchronisation progress should be 95% after 3 days
    Alert by means of email in case replication does not proceed as expected

####################################################################################################
"""
