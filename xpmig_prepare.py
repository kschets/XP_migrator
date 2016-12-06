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

####################################################################################################
### VARIABLES
####################################################################################################
####################################################################################################
### FUNCTIONS
####################################################################################################
####################################################################################################
### CLASSES
####################################################################################################
####################################################################################################
### MAIN 
####################################################################################################
configfile = "xpmig.ini"
cfg = ConfigParser()
cfg.read(configfile)

for mandatory_section in ("mapping"):
    if not cfg.has_section(mandatory_section):
        sys.stderr.write("{} section missing in the config file {}, exiting..".format(mandatory_section,configfile))
        sys.exit(1)
        
try:
    map_file_dir = cfg.get("mapping","dir")
except:
    map_file_dir = "/tmp"
    
try:
    loglevel =cfg.getint("log","level")
except:
    loglevel = 30
    
try:
    logfile = cfg.get("log","file")
except:
    logfile = "/tmp/xpmig_prepare.log"
    
try:
    logsize = cfg.getint("log","size")
except:
    logsize = 100000000
    
try:
    logversions = cfg.getint("log","maxversions")
except:
    logversions = 5
    
    