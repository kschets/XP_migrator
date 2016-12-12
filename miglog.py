"""
####################################################################################################

TITLE : HPE XP7 Migration, miglog module

DESCRIPTION :  Provides per box/hostgroup logging
    
AUTHOR : Koen Schets / StorageTeam

VERSION : Based on previous ODR framework
    1.0 Initial version

CONFIG : xpmig.ini

LOG : 

TODO :

####################################################################################################
"""
import os
import os.path
import datetime

class Miglog(object):
    
    def __init__(self,log_dir,log_prefix):
        self.log_dir = log_dir
        self.log_prefix = log_prefix

    def log(self,box_name,hostgroup_name,severity,message):
        """
        log the message to the box/hostgroup logfile
        """
        ### make sure directory structure exists ###
        log_dir = os.path.join(self.log_dir,box_name,hostgroup_name)
        try:
            os.makedirs(log_dir)
        except OSError:
            if not os.path.isdir(self.log_dir):
                raise
        ### log file is called xp_migrate.log ###
        log_file = os.path.join(log_dir,"xp_migrate.log")
        try:
            lfh = open(log_file,"at")
        except:
            raise
        ### set timestamp to be used ###
        timestamp = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        ### and finally write the message ###
        lfh.write("{} {} {}\n".format(timestamp,severity,message))
        lfh.close()
        
        
