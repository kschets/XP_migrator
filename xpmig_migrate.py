#!/usr/bin/python
"""
####################################################################################################

TITLE : HPE XP7 Migration, Migrate

DESCRIPTION :  Migrate the data to the new server
    
AUTHOR : Koen Schets / StorageTeam

VERSION : Based on previous ODR framework
    1.0 Initial version

CONFIG : xpmig.ini

LOG : xpmig_migrate.log

TODO :
    Check CaJ replication is > 90%
    Wait for the source host to logout
    Remove hba_wwns to prevent re-login
    Wait for the syncrate to be 100%
    Request operator confirmation before split
    Stop CaJ replication
    Detach external storage raidgroups
    Show the overview of the migration in a foot-window

####################################################################################################
"""
import curses
