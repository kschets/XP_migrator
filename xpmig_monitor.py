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
import sys
import os
import os.path
import logging
import logging.handlers
from ConfigParser import ConfigParser
import atexit
import signal
import time

#################################################################
### Variables 
#################################################################
name_to_serial_dict = {}
serial_to_name_dict = {}
name_to_instance_dict = {}

#################################################################
### Function daemonize
#################################################################
def daemonize( pid_file, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    
    # Turn to a daemon
    if os.path.exists( pid_file ):
        raise RuntimeError("Already running...")

    # First fork detaches from parent
    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError("First fork failed ...")

    os.chdir('/')
    os.umask(0)
    os.setsid()

    # Second fork
    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError("Second fork failed...")

    # Flush I/O buffers
    sys.stdout.flush()
    sys.stderr.flush()

    # Replace file descriptors for stdin, stdout and stderr
    with open(stdin, 'rb', 0) as f:
        os.dup2( f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab', 0) as f:
        os.dup2( f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab', 0) as f:
        os.dup2( f.fileno(), sys.stderr.fileno())

    # Write the PID file
    with open(pid_file,'w') as f:
        f.write( str(os.getpid()) )

    # Arrange to have the PID file removed on exit/signal
    atexit.register(lambda: os.remove(pid_file))

    # Signal handler for termination
    def sigterm_handler(signo, frame):
        sigStat.set()
        logger.info("Received SIGTERM, starting cleanup ...")

    signal.signal( signal.SIGTERM, sigterm_handler)

#################################################################
### Class sigReceived
#################################################################
class sigReceived:
    #Set the signal flag as the TERM SIGNAL is received
    def __init__(self):
        self.sig = 0

    def set(self):
        self.sig = 1

    def get(self):
        if ( self.sig == 1):
            return True
        else:
            return False

#################################################################
### MAIN
#################################################################
linelen = 120
sigstat = sigReceived()
pid_file = "/home/koen/XP_migrator/log/xpmig_monitor.pid"
config_file = "/home/koen/XP_migrator/xpmig.ini"

if len(sys.argv) != 2:
    sys.stderr.write("Usage: {} [start|stop|status]\n".format(sys.argv[0]))
    sys.stderr.flush()
    raise SystemExit(1)
                     
if sys.argv[1] == "start":
    
    try:
        daemonize(pid_file,stdout="/home/koen/XP_migrator/log/xpmig_monitor.stdout",stderr="/home/koen/XP_migrator/log/xpmig_monitor.stderr")
    except RuntimeError as e:
        sys.stderr.write(str(e))
        sys.stderr.flush()
        raise SystemExit(1)
    
    ### parse configuration ###
    cfg = ConfigParser()
    cfg.read(config_file)
    
    for mandatory_section in ("serialnbr","instance"):
        if not cfg.has_section(mandatory_section):
            sys.stderr.write("{} section missing in config file {},exiting..\n".format(mandatory_section,config_file))
            sys.exit(1)
            
    for name,value in cfg.items("serialnbr"):
        name_to_serial_dict[name] = value
        serial_to_name_dict[value] = name
        
    for name,value in cfg.items("instance"):
        name_to_instance_dict[name] = value
    
    try:
        log_dir = cfg.get("dir","log")
    except:
        log_dir = "/tmp/log"
        
    try:
        log_level = cfg.getint("log","level")
    except:
        log_level = 30
        
    try:
        log_size = cfg.getint("log","size")
    except:
        log_size = 10000000
        
    try:
        log_versions = cfg.getint("log","maxversions")
    except:
        log_versions = 5
        
    ### start logging ###
    logger = logging.getLogger("xpmig_monitor")
    logger.setLevel(log_level)
    log_file = os.path.join(log_dir,"xpmig_monitor.log")
    fh = logging.handlers.RotatingFileHandler(log_file,maxBytes=log_size,backupCount=log_versions)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s","%Y/%m/%d-%H:%M:%S")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    logger.info("#" * linelen)
    logger.info("XPMIG MONITOR started")
    logger.info("#" * linelen)
    
    logger.info("Configuration settings :")
    
    ### start the eternal loop ###
    while True:
        logger.info("start LOOP")
        ### get all P9500 instance nbrs ###
        
        ### get all copygroups/devicegroups ###
        
        ### query each copygroup status and % complete ###
        
        ### raise alert in case of suspend/simplex/late replication ###
        
        time.sleep(15)
        ### check if SIGTERM was received ###
        if sigstat.get():
            logger.info("#" * linelen)
            logger.info("XPMIG MONITOR ending")
            logger.info("#" * linelen)
            raise SystemExit(0)
                     
elif sys.argv[1] == "stop":
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            os.kill( int(f.read()), signal.SIGTERM)
    else:
        sys.stderr.write("Not running..\n")
        sys.stderr.flush()
        raise SystemExit(1)
    
elif sys.argv[1] == "status":
    if os.path.exists(pid_file):
        sys.stderr.write("running..\n")
        sys.stderr.flush()
    else:
        sys.stderr.write("not running..\n")
        sys.stderr.flush()
        
else:
    sys.stderr.write("Unknown command {}\n".format(sys.argv[1]))
    sys.stderr.flush()
    raise SystemExit(1)
    
