#!/usr/bin/python
"""
####################################################################################################

TITLE : HPE XP7 Migration, Precheck

DESCRIPTION :  Precheck to examine hostgroup is ready for migration
    
AUTHOR : Koen Schets / StorageTeam

VERSION : Based on previous ODR framework
    1.0 Initial version

CONFIG :

LOG :

TODO :

####################################################################################################
"""
import xp7

os10_ab = xp7.XP7("OS10_AB",10,65100,"AB","XPC51_collect.txt")
os10_haren = xp7.XP7("OS10_HAREN",11,65200,"HAREN","XPM22_collect.txt")
