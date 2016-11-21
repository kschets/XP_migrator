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
import re

####################################################################################################
#  VARIABLES 
####################################################################################################
source_box_dict = {
    "OS10_AB":65101,
    "OS10_HAREN":65102,
    "OS11_AB":65201,
    "OS11_HAREN":65202,
    "OS12_AB":65301,
    "OS12_HAREN":65302,
    "OS13_AB":65401,
    "OS13_HAREN":65402
}

instance_dict = {
    "OS10_AB":10,
    "OS10_HAREN":11,
    "OS11_AB":12,
    "OS11_HAREN":13,
    "OS12_AB":14,
    "OS12_HAREN":15,
    "OS13_AB":16,
    "OS13_HAREN":17,
}

site_dict = {
    "OS10_AB":"AB",
    "OS10_HAREN":"HAREN",
    "OS11_AB":"AB",
    "OS11_HAREN":"HAREN",
    "OS12_AB":"AB",
    "OS12_HAREN":"HAREN",
    "OS13_AB":"AB",
    "OS13_HAREN":"HAREN",
}

collect_file_dict = {
    "OS10_AB":"XPC51_collect.txt",
    "OS10_HAREN":"XPM22_collect.txt",
    "OS11_AB":"XPC52_collect.txt",
    "OS11_HAREN":"XPM24_collect.txt",
    "OS12_AB":"XPC51_collect.txt",
    "OS12_HAREN":"XPM22_collect.txt",
    "OS13_AB":"XPC52_collect.txt",
    "OS13_HAREN":"XPM24_collect.txt",
}

### read xpinfo file if provided ###

### select source box ###
source_box_list = sorted(source_box_dict.keys())
print "Source disk boxes : "
print
for box_nbr,source_box_name in enumerate(source_box_list):
    print "    {}   {}".format(box_nbr,source_box_name)
print
select_nbr = input("Enter box nbr : ")

### instantiate source box object ###
source_box_name = source_box_list[select_nbr]
source_box_instance_nbr = instance_dict[source_box_name]
source_box_serial_nbr = source_box_dict[source_box_name]
source_box_site = site_dict[source_box_name]
source_box_collect_file = collect_file_dict[source_box_name]
source_box = xp7.XP7(source_box_name,source_box_instance_nbr,source_box_serial_nbr,source_box_site,source_box_collect_file)

### select hostgroup ###
hostgroup_name_list = [ x for x in source_box.get_hostgroups() if not re.match(".*-G00$",x)]
print "Source HOSTGROUPs : "
print
for hg_nbr,hg_name in enumerate(hostgroup_name_list):
    print "    {}    {}".format(hg_nbr,hg_name)
print
select_hg_nbr = input("Enter hostgroup nbr : ")
select_hg_name = hostgroup_name_list[select_hg_nbr]
print "{}/{} HG selected for migration precheck..".format(source_box.name,select_hg_name)
source_box.print_hostgroup_noluns(select_hg_name)

### consistency check hostgroup ###
hostgroup_consistency_check_result = source_box.test_hostgroup_consistency(select_hg_name)
print "{} consistency check : {}".format(select_hg_name,"V" if hostgroup_consistency_check_result else "X")

### get hostgroup ldevs ###
ldev_list = source_box.get_hostgroup_ldevs(select_hg_name)
print "LDEVs : {}".format(",".join(ldev_list))

### check if any CA is defined on LDEVs in scope ###
ca_found = False
for ldev in ldev_list:
    if "HORC" in source_box.get_ldev(ldev).attr_set:
        ca_found = True
        
if ca_found:
    ### check CA ###
    source_box.print_horcm_ldev(select_hg_name,"CA_CHECK")
else:
    ### all SMPL ###
    print "LDEVs are SIMPLEX, no need to check CA.."

### generate horcm files for hostgroup ###


### pairdisplay hostgroup ldevs, CA OK ? ###

### output hostgroup ldevs for BP2I provisioning input ###
print "Provision these target volumes : "
for ldev_nbr in ldev_list:
    ldev = source_box.get_ldev(ldev_nbr)
    if ldev.is_cmd_device():
        print "{} : CMD device".format(ldev_nbr)
    else:
        print "{} : {} blocks ( {} )".format(
            ldev.nbr, ldev.size, ldev.convert_size()
        )