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
    Show summary of what is in the mapping file
    Request operator confirmation to proceed with the external storage discovery
    Check external luns :
        - to be not in use already ( no external grp should be defined on it already )
        - all mapped ldevs should have an external lun of at least the same size
    Define external grps
    Add paths to external grps
    Define LDEVs on the external grps
    Define CaJ relations source - target volumes and start the replication

####################################################################################################

raidcom discover external_storage -port CL5-K -I11

root@omep4040:~# raidcom discover external_storage -port CL5-K -I11
PORT     WWN                PM  USED   Serial#  VENDOR_ID PRODUCT_ID
CL5-K    50060e80164ef920   M   NO     85753    HPE       P9500

raidcom discover external_storage -port CL6-K -I11

root@omep4040:~# raidcom discover external_storage -port CL6-K -I11
PORT     WWN                PM  USED   Serial#  VENDOR_ID PRODUCT_ID
CL6-K    50060e80164ef930   M   NO     85753    HPE       P9500

root@oldp4001:~# raidcom discover lun -port CL5-K -external_wwn 50060e80164ef920 -I11
PORT     WWN              LUN  VOL_Cap(BLK)  PRODUCT_ID  E_VOL_ID_C
CL5-K    50060e80164ef920   0     209715200  OPEN-V      R500 00085753012809
CL5-K    50060e80164ef920   1     209715200  OPEN-V      R500 00085753012862
root@oldp4001:~# raidcom discover lun -port CL6-K -external_wwn 50060e80164ef930 -I11
PORT     WWN              LUN  VOL_Cap(BLK)  PRODUCT_ID  E_VOL_ID_C
CL6-K    50060e80164ef930   0     209715200  OPEN-V      R500 00085753012809
CL6-K    50060e80164ef930   1     209715200  OPEN-V      R500 00085753012862

root@oldp4001:~# raidcom add external_grp -path_grp 1 -external_grp_id 1-1 -port CL5-K -external_wwn 50060e80164ef920 -lun_id 0 -I11

root@oldp4001:~# raidcom get external_grp -I11
T GROUP  Num_LDEV  U(%)  AV_CAP(GB) R_LVL  E_TYPE     SL  CL  DRIVE_TYPE
E 1-1           0    0          202 -      OPEN-V      0   0  OPEN-V

root@oldp4001:~# raidcom get external_grp -external_grp_id 1-1 -I11
T GROUP  P_NO  LDEV#   STS         LOC_LBA        SIZE_LBA            Serial#
E 1-1       0      -   NML  0x000000000000  0x0000194a6000             358832

--------------------------------------------------------------------------------------------
Add all to migrate external luns as external_grp
================================================
root@oldp4001:~# raidcom add external_grp -path_grp 1 -external_grp_id 1-2 -port CL5-K -external_wwn 50060e80164ef920 -lun_id 1 -I11

root@oldp4001:~# raidcom get external_grp -I11
T GROUP  Num_LDEV  U(%)  AV_CAP(GB) R_LVL  E_TYPE     SL  CL  DRIVE_TYPE
E 1-1           0     0         202 -      OPEN-V      0   0  OPEN-V
E 1-2           0     0         101 -      OPEN-V      0   0  OPEN-V

--------------------------------------------------------------------------------------------
Add paths on all new external_grp
=================================

root@oldp4001:~# raidcom get path -path_grp 1 -I11
PHG GROUP STS CM IF MP# PORT   WWN                 PR LUN PHS  Serial# PRODUCT_ID LB PM DM
  1 1-1   NML E  D    0 CL5-K  50060e80164ef920     1   0 NML    85753 P9500      N  M  D
  1 1-2   NML E  D    1 CL5-K  50060e80164ef920     1   1 NML    85753 P9500      N  M  D

root@oldp4001:~# raidcom add path -path_grp 1 -port CL6-K -external_wwn 50060e80164ef930 -I11

root@oldp4001:~# raidcom get path -path_grp 1 -I11
PHG GROUP STS CM IF MP# PORT   WWN                 PR LUN PHS  Serial# PRODUCT_ID LB PM DM
  1 1-1   NML E  D    0 CL5-K  50060e80164ef920     1   0 NML    85753 P9500      N  M  D
  1 1-1   NML E  D    0 CL6-K  50060e80164ef930     2   0 NML    85753 P9500      N  M  D
  1 1-2   NML E  D    1 CL5-K  50060e80164ef920     1   1 NML    85753 P9500      N  M  D
  1 1-2   NML E  D    1 CL6-K  50060e80164ef930     2   1 NML    85753 P9500      N  M  D
---------------------------------------------------------------------------------------------
Create ldev's on external_grp's exact same size as original lun on IBM
======================================================================

root@oldp4001:~# raidcom discover lun -port CL5-K -external_wwn 50060e80164ef920 -I11
PORT     WWN              LUN  VOL_Cap(BLK)  PRODUCT_ID  E_VOL_ID_C
CL5-K    50060e80164ef920   0     424304640  OPEN-V      R500 00085753012308
CL5-K    50060e80164ef920   1     212152320  OPEN-V      R500 00085753012309

root@oldp4001:~# raidcom add ldev -external_grp_id 1-1 -ldev_id 64:00 -capacity 424304640  -I11
root@oldp4001:~# raidcom add ldev -external_grp_id 1-2 -ldev_id 64:01 -capacity 212152320  -I11

root@oldp4001:~# raidcom get ldev -ldev_id 64:00 -fx -I11
Serial#  : 358832
LDEV : 6400
SL : 0
CL : 0
VOL_TYPE : OPEN-V-CVS
VOL_Capacity(BLK) : 424304640
NUM_PORT : 0
PORTs :
F_POOLID : NONE
VOL_ATTR : CVS : ELUN
E_VendorID : HP
E_ProductID : OPEN-V
E_VOLID : 523530302030303038353735333031323330382000000000000000000000000000000000
E_VOLID_C : R500 00085753012308 ................
NUM_E_PORT : 2
E_PORTs : CL5-K-0 0 50060e80164ef920 : CL6-K-0 0 50060e80164ef930
LDEV_NAMING :
STS : NML
OPE_TYPE : NONE
OPE_RATE : 100
MP# : 0
SSID : 000E
ALUA : Disable
RSGID : 0

root@oldp4001:~# raidcom get ldev -ldev_id 64:01 -fx -I11
Serial#  : 358832
LDEV : 6401
SL : 0
CL : 0
VOL_TYPE : OPEN-V-CVS
VOL_Capacity(BLK) : 212152320
NUM_PORT : 0
PORTs :
F_POOLID : NONE
VOL_ATTR : CVS : ELUN
E_VendorID : HP
E_ProductID : OPEN-V
E_VOLID : 523530302030303038353735333031323330392000000000000000000000000000000000
E_VOLID_C : R500 00085753012309 ................
NUM_E_PORT : 2
E_PORTs : CL5-K-0 1 50060e80164ef920 : CL6-K-0 1 50060e80164ef930
LDEV_NAMING :
STS : NML
OPE_TYPE : NONE
OPE_RATE : 100
MP# : 1
SSID : 000E
ALUA : Disable
RSGID : 0

root@oldp4001:~# raidcom get external_grp -I11
T GROUP  Num_LDEV  U(%)  AV_CAP(GB) R_LVL  E_TYPE     SL  CL  DRIVE_TYPE
E 1-1           1   100           0 -      OPEN-V      0   0  OPEN-V
E 1-2           1   100           0 -      OPEN-V      0   0  OPEN-V

------------------------------------------------------------------------------------------------
Name all created external ldevs
===============================

root@oldp4001:~# raidcom modify ldev -ldev_id 64:00 -ldev_name AP0758_6400 -I11
root@oldp4001:~# raidcom modify ldev -ldev_id 64:01 -ldev_name AP0758_6401 -I11

root@oldp4001:~# raidcom get ldev -ldev_id 64:00 -fx -cnt 2 -I11
Serial#  : 358832
LDEV : 6400
SL : 0
CL : 0
VOL_TYPE : OPEN-V-CVS
VOL_Capacity(BLK) : 424304640
NUM_PORT : 0
PORTs :
F_POOLID : NONE
VOL_ATTR : CVS : ELUN
E_VendorID : HP
E_ProductID : OPEN-V
E_VOLID : 523530302030303038353735333031323330382000000000000000000000000000000000
E_VOLID_C : R500 00085753012308 ................
NUM_E_PORT : 2
E_PORTs : CL5-K-0 0 50060e80164ef920 : CL6-K-0 0 50060e80164ef930
LDEV_NAMING : AP0758_6400
STS : NML
OPE_TYPE : NONE
OPE_RATE : 100
MP# : 0
SSID : 000E
ALUA : Disable
RSGID : 0

Serial#  : 358832
LDEV : 6401
SL : 0
CL : 0
VOL_TYPE : OPEN-V-CVS
VOL_Capacity(BLK) : 212152320
NUM_PORT : 0
PORTs :
F_POOLID : NONE
VOL_ATTR : CVS : ELUN
E_VendorID : HP
E_ProductID : OPEN-V
E_VOLID : 523530302030303038353735333031323330392000000000000000000000000000000000
E_VOLID_C : R500 00085753012309 ................
NUM_E_PORT : 2
E_PORTs : CL5-K-0 1 50060e80164ef920 : CL6-K-0 1 50060e80164ef930
LDEV_NAMING : AP0758_6401
STS : NML
OPE_TYPE : NONE
OPE_RATE : 100
MP# : 1
SSID : 000E
ALUA : Disable
RSGID : 0

Delete external ldevs:

raidcom delete ldev -ldev_id 94:00 -I11
raidcom delete ldev -ldev_id 94:01 -I11

Delete external_grp's:

raidcom disconnect external_grp -external_grp_id 1-1 -I11
raidcom disconnect external_grp -external_grp_id 1-2 -I11



raidcom delete external_grp -external_grp_id 1-1 -I11
raidcom delete external_grp -external_grp_id 1-2 -I11


"""
import curses
from curses import panel
import re
import logging
import logging.handlers
from ConfigParser import ConfigParser
import sys
import os
import os.path
import csv
import string
import xp7
import miglog
import collections

####################################################################################################
### VARIABLES
####################################################################################################
linelen = 100
Mig_tuple = collections.namedtuple("Mig_tuple",["hostgroup","source_box_sn","source_ldev_nbr","source_ldev_size","target_box_sn","target_ldev_nbr"])
mig_list = []
target_storage_dict = {}
comment_re = re.compile("^#")
name_by_serial_dict = {}
serial_by_name_dict = {}
instance_dict = {}

####################################################################################################
### FUNCTIONS
####################################################################################################
####################################################################################################
### CLASSES
####################################################################################################
class Menu(object):
    
    def __init__(self,window,items,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.position = 0
        self.items = items
        self.items.append(("exit","exit"))
        
    def navigate(self,n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1
            
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        
        while True:
            self.window.refresh()
            curses.doupdate()
            for index,item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_STANDOUT
                else:
                    mode = curses.A_NORMAL
                # line = "{}: {}".format(index,item[0])
                line = "{}".format(item[0])
                if len(line) >= self.width:
                    line = line[:self.width-1]
                self.window.addstr(1+index,2,line,mode)
            
            key = self.window.getch()
            
            if key in [curses.KEY_ENTER,ord("\n"),ord("B"),ord("b")]:
                if self.position == len(self.items) - 1:
                    break
                else:
                    ### call the next menu item ###
                    self.items[self.position][1]()
            elif key == curses.KEY_UP:
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
                
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        
class Map_menu(object):
    
    def __init__(self,window,map_dir,selection,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.map_file_list = []
        self.slice_start = 0
        self.slice_end = 0
        self.slice_len = 0
        self.position = 0
        self.map_dir = map_dir
        self.selection = selection
        
    def update(self):
        """
        Read the map_dir and fill the list of map files
        """
        if os.path.exists(self.map_dir):
            del(self.map_file_list[:])
            self.map_file_list = [f for f in os.listdir(self.map_dir) if os.path.isfile(os.path.join(self.map_dir,f)) and re.match(".+\.map$",f,flags=re.IGNORECASE)]
            self.map_file_list.append("exit")
            self.slice_len = min(len(self.map_file_list)-1, self.heigth-6)
            self.slice_start = 0
            self.slice_end = self.slice_start + self.slice_len
            self.position = 0
        
    def navigate(self,n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.map_file_list):
            self.position = len(self.map_file_list)-1
        if n < 0:
            if self.position - self.slice_start < 2 and self.slice_start >= 1:
                ### slide slice up ###
                self.slice_start += n
                if self.slice_start < 0:
                    self.slice_start = 0
                self.slice_end = self.slice_start + self.slice_len
        elif n > 0:
            if self.slice_end - self.position < 2 and self.slice_end < len(self.map_file_list) - 1:
                ### slide slice down ###
                self.slice_end += n
                if self.slice_end > len(self.map_file_list) - 1:
                    self.slice_end = len(self.map_file_list) - 1
                self.slice_start = self.slice_end - self.slice_len
    
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.update()
        
        while True:
            self.window.clear()
            self.window.refresh()
            curses.doupdate()
            ### show the list of map files ###
            for index,item in enumerate(self.map_file_list):
                if index == self.position:
                    mode = curses.A_STANDOUT
                else:
                    mode = curses.A_NORMAL
                line = "{}".format(item)
                if len(line) >= self.width:
                    line = line[:self.width-1]
                ### only add lines in the slice ###
                if self.slice_start <= index <= self.slice_end:
                    self.window.addstr(1+(index-self.slice_start),2,line,mode)
            key = self.window.getch()
            if key in [ord("b"),ord("B")]:
                break
            elif key in [curses.KEY_ENTER,ord("\n")]:
                if self.position == len(self.map_file_list)-1:
                    break
                else:
                    logger.info("MAP FILE: {} select for processing".format(self.map_file_list[self.position]))
                    self.window.clear()
                    self.window.refresh()
                    ### read & parse the map file ### 
                    map_file = os.path.join(self.map_dir,self.map_file_list[self.position])
                    self.window.addstr(2,2,"Processing {}".format(map_file))
                    map_file_ok = True
                    line_nbr = 0
                    with open(map_file,"rt") as f:
                        map_file_reader = csv.reader(f)
                        for row in map_file_reader:
                            line_nbr += 1
                            if not comment_re.match(row[0]):
                                if len(row) == 6:
                                    mig_tuple = Mig_tuple._make(row)
                                    mig_list.append(mig_tuple)
                                    logger.debug("added {}".format(mig_tuple))
                                else:
                                    map_file_ok = False
                                    logger.error("{} map file contains invalid data, please correct & re-run".format(map_file))
                                    logger.error("{}: {}".format(line_nbr,row))
                                    self.window.addstr(3,2,"Map file contains an invalid line, please correct & re-run")
                                    self.window.addstr(4,2,"{}: {}".format(line_nbr,row))
                                    key = self.window.getch()
                                    break
                    if map_file_ok:
                        self.window.addstr(3,2,"Map file read OK, {} source - target relations discovered".format(len(mig_list)))
                    else:
                        self.window.addstr(3,2,"Map file could not be processed, please correct & re-run")
                        key = self.window.getch()
                        break
                    ### request confirmation to proceed with external storage discovery ###
                    self.window.addstr(4,2,"Are all target volumes mapped to XP7 ? (y/N)")
                    key = self.window.getch()
                    if key in [ord("y"),ord("Y")]:
                        ### proceed with external storage discovery ###
                        self.window.addstr(5,2,"Proceeding with target storage discovery..")
                        ### check which target storage is in scope ###
                        target_sn_set = set([x.target_box_sn for x in mig_list])
                        for target_sn in target_sn_set:
                            if target_sn in name_by_serial_dict:
                                target_name = name_by_serial_dict[target_sn]
                                ### now we're able to find the IO ports to scan
                                if target_name in target_storage_dict:
                                    ext_storage_ports = target_storage_dict[target_name]
                                    for external_storage_port in external_storage_ports:
                                        ### get the wwn ###
                                        self.window.addstr(6,2,"External storage discovery on port {}".format(external_storage_port))

                                    
                                else:
                                    logger.error("No target IO ports defined for target {},skipping..".format(target_name))
                            else:
                                logger.error("Unknown target box S/N {}, skipping".format(target_sn)
                    else:
                        logger.info("MAP FILE: exit processing {}, target storage not mapped..".format(map_file))
                        break
            elif key == curses.KEY_UP:
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
            elif key == curses.KEY_PPAGE:
                self.navigate(-10)
            elif key == curses.KEY_NPAGE:
                self.navigate(10)
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        
class Selection(object):
    
    def __init__(self,window,title,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.title = title
        self.selection = []
        
    def display(self):
        self.window.clear()
        line = "{} : {}".format(self.title, ",".join(["{}-{}".format(x[0],x[1]) for x in self.selection]))
        if len(line) >= self.width:
            line = line[:self.width-1]
        self.window.addstr(1,2,line)
        self.window.border()
        self.window.refresh()
        curses.doupdate()
        
    def add(self,item):
        current_set = set(self.selection)
        current_set.add(item)
        self.selection = list(sorted(current_set))
        self.display()
        
    def clear(self):
        del self.selection[:]
        self.display()
        
    def get(self):
        return self.selection
        
####################################################################################################
### MAIN 
####################################################################################################
def main(stdscr):
    ### clear screen ###
    stdscr.clear()
    
    ### check window height and width ###
    if curses.COLS < 20 and curses.LINES < 20:
        sys.stderr.write("Window not large enough, exiting..\n")
        sys.exit(1)
        
    ### define title_win ###
    title_win = stdscr.subwin(3,curses.COLS,0,0)
    title_win.addstr(1,2,"HPE P9500 to XP7 MIGRATION PREPARE")
    title_win.border()
    
    ### define selection_win ###
    select_win = stdscr.subwin(3,curses.COLS,curses.LINES-4,0)
    selection = Selection(select_win,"SELECTED HOSTGROUP(s)",stdscr)
    selection.display()
    
    ### define menu_win ###
    menu_win = stdscr.subwin(curses.LINES-7,curses.COLS,3,0)
    main_menu_items = []
    
    map_menu = Map_menu(menu_win,map_file_dir,selection,stdscr)
    main_menu_items.append(("Process MAP file",map_menu.display))
    
    ### define status_win ###
    # status_win = stdscr.subwin(3,curses.COLS,curses.LINES-4,0)
    # status_win.addstr(1,2,"STATUS:")
    # status_win.border()
    
    ### fire up the main menu ###
    main_menu = Menu(menu_win,main_menu_items,stdscr)
    main_menu.display()
    
    ### getting here means we exited the menu ###
    stdscr.refresh()
    
configfile = "xpmig.ini"
cfg = ConfigParser()
cfg.read(configfile)

for mandatory_section in ("dir","target"):
    if not cfg.has_section(mandatory_section):
        sys.stderr.write("{} section missing in the config file {}, exiting..".format(mandatory_section,configfile))
        sys.exit(1)
        
for name,value in cfg.items("target"):
    target_storage_dict[name] = value.split(",")
    
try:
    map_file_dir = cfg.get("dir","map")
except:
    map_file_dir = "/tmp"
    
try:
    loglevel =cfg.getint("log","level")
except:
    loglevel = 30
    
try:
    logdir = cfg.get("dir","log")
except:
    logdir = "/tmp/log"
    
try:
    logsize = cfg.getint("log","size")
except:
    logsize = 100000000
    
try:
    logversions = cfg.getint("log","maxversions")
except:
    logversions = 5
    
for name,value in cfg.items("serialnbr"):
    serial_by_name_dict[name] = value
    name_by_serial_dict[value] = name
    
for name,value in cfg.items("instance"):
    instance_dict[name] = value
    
#####################
### start logging ###
#####################
logger = logging.getLogger("xpmig_prepare")
logger.setLevel(loglevel)
logfile = os.path.join(logdir,"xpmig_prepare.log")
fh = logging.handlers.RotatingFileHandler(logfile,maxBytes=logsize,backupCount=logversions)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s","%Y/%m/%d-%H:%M:%S")
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info("#" * linelen)
logger.info("XPMIG PREPARE started")
logger.info("#" * linelen)

logger.info("Configuration settings :")
logger.info("MAPPING dir: {}".format(map_file_dir))
    
miglog = miglog.Miglog(logdir,"PREPARE")

#####################
### start menu    ###
#####################
curses.wrapper(main)
#####################
### stop  logging ###
#####################
logger.info("#" * linelen)
logger.info("XPMIG PREPARE ended")
logger.info("#" * linelen)