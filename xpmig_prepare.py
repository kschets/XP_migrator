#!/usr/bin/python
"""
####################################################################################################

TITLE : HPE XP7 Migration, Prepare

DESCRIPTION :  Prepare does the setup and start of the CaJ replication
    
AUTHOR : Koen Schets / StorageTeam

VERSION : Based on previous ODR framework
    1.0 Initial version

CONFIG : xpmig.ini

LOG : xpmig_prepare.log

TODO :
    Read the source - target mapping file (source box,source ldev,target box,target volume)
    Discover external storage and compare against the provided mapping
    Make sure the external storage luns are not in use yet on the XP7
    Exit in case of anomalies
    Define target LDEVs on the external storage raidgroups
    Define CaJ relations source - target volumes and start the replication

####################################################################################################
"""
