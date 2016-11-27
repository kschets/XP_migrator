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
box_pair_dict = {
    "OS10":["OS10_AB","OS10_HAREN"],
    "OS11":["OS11_AB","OS11_HAREN"],
    "OS12":["OS12_AB","OS12_HAREN"],
    "OS13":["OS13_AB","OS13_HAREN"],
}

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
boxpair_list = sorted(box_pair_dict.keys())
print "Source disk boxes : "
print
for boxpair_nbr,boxpair_name in enumerate(boxpair_list):
    print "    {}   {}".format(boxpair_nbr,boxpair_name)
print
select_nbr = input("Enter box-pair nbr : ")

### instantiate source box object ###
source_box_ab_name = box_pair_dict[boxpair_list[select_nbr]][0]
source_box_haren_name = box_pair_dict[boxpair_list[select_nbr]][1]

source_box_ab_instance_nbr = instance_dict[source_box_ab_name]
source_box_haren_instance_nbr = instance_dict[source_box_haren_name]

source_box_ab_serial_nbr = source_box_dict[source_box_ab_name]
source_box_haren_serial_nbr = source_box_dict[source_box_haren_name]

source_box_ab_collect_file = collect_file_dict[source_box_ab_name]
source_box_haren_collect_file = collect_file_dict[source_box_haren_name]

source_box_ab = xp7.XP7(source_box_ab_name,source_box_ab_instance_nbr,source_box_ab_serial_nbr,"AB",source_box_ab_collect_file)
source_box_haren = xp7.XP7(source_box_haren_name,source_box_haren_instance_nbr,source_box_haren_serial_nbr,"HAREN",source_box_haren_collect_file)

### select hostgroup ###
hg_name_set = set()
hg_name_set = hg_name_set.union([x for x in source_box_ab.get_hostgroups() if not re.match(".*-G00$",x)])
hg_name_set = hg_name_set.union([x for x in source_box_haren.get_hostgroups() if not re.match(".*-G00$",x)])
hg_name_list = list(sorted(hg_name_set))
print "Source HOSTGROUPs : "
print
for hg_nbr,hg_name in enumerate(hg_name_list):
    print "    {}    {}".format(hg_nbr,hg_name)
print
select_hg_nbr = input("Enter hostgroup nbr : ")
select_hg_name = hg_name_list[select_hg_nbr]
print "{} HG selected for migration precheck..".format(select_hg_name)

if source_box_ab.test_hostgroup_exists(select_hg_name):
    print "AB check for {} consistency : {}".format(
        select_hg_name,"V" if source_box_ab.test_hostgroup_consistency(select_hg_name) else "X"
    )
if source_box_haren.test_hostgroup_exists(select_hg_name):
    print "HAREN check for {} consistency : {}".format(
        select_hg_name,"V" if source_box_haren.test_hostgroup_consistency(select_hg_name) else "X"
    )
    
"""
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
"""