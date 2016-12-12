#!/usr/bin/python
#
# StorageTeam XP provisioning toolkit
#
# Collect XP configuration data
#
import subprocess
import re
import sys
import os
import os.path

################################
# CLASSes
################################
class Port:

    def __init__(self,name,wwpn):
        self.name = name
        self.wwpn = wwpn

    def __repr__(self):
        return "PORT,%s,%s" % (self.name,self.wwpn)

class Hostgroup:

    def __init__(self,port,name,hostmode,hostmode_opt,gid):
        self.port = port
        self.name = name
        self.hostmode = hostmode
        hmo = hostmode_opt.lstrip().rstrip()
        self.hostmode_opt = hmo.split()
        self.gid = gid

    def __repr__(self):
        return "HOSTGROUP,%s,%s,%s,%s,%s" % (self.port,self.name,self.hostmode,";".join(self.hostmode_opt),self.gid)

class Lun:

    def __init__(self,port,hostgroup,lun,ldev):
        self.port = port
        self.hostgroup = hostgroup
        self.lun = lun_id
        self.ldev = ldev_id

    def __repr__(self):
        return "LUN,%s,%s,%s,%s" % (self.port,self.hostgroup,self.lun,self.ldev)

class Ldev:

    def __init__(self,ldev_id,ldev_type,capacity,pool,status,attr):
        self.id = ldev_id
        self.type = ldev_type
        self.status = status
        self.cap = capacity
        self.pool = pool
        self.attr = attr

    def __repr__(self):
        return "LDEV,%s,%s,%s,%s,%s,%s" % (
                self.id,self.type,self.status,self.cap,self.pool,self.attr
            )

class Wwn:

    def __init__(self,port,group,wwn,nickname):
        self.port = port
        self.group = group
        self.wwn = wwn
        self.nickname = nickname

    def __repr__(self):
        return "WWN,%s,%s,%s,%s" % ( self.port,self.group,self.wwn,self.nickname )

class Login:

    def __init__(self,port,wwn):
        self.port = port
        self.wwn = wwn

    def __repr__(self):
        return "LOGIN,%s,%s" % (self.port,self.wwn)

################################
# VARs
################################
raidcom_cmd = os.path.join("c:",os.sep,"HORCM","usr","bin","raidcom.exe")

### START box config ###

raidcom_inst = "-I10"
box_name = "OS10_AB"
box_serial = "86000"

# raidcom_inst = "-I110"
# box_name = "OS10_X"
# box_serial = "86009"

# raidcom_inst = "-I11"
# box_name = "OS11_AB"
# box_serial = "85952"

# raidcom_inst = "-I111"
# box_name = "OS11_X"
# box_serial = "85983"

# raidcom_inst = "-I12"
# box_name = "OS12_AB"
# box_serial = "86580"

# raidcom_inst = "-I112"
# box_name = "OS12_X"
# box_serial = "86553"

# raidcom_inst = "-I13"
# box_name = "OS13_AB"
# box_serial = "86572"

# raidcom_inst = "-I113"
# box_name = "OS13_X"
# box_serial = "86587"

### END box config ###

get_resource_re = re.compile("^meta_resource\s+0\s+(\w+)\s+\S+\s+\S+\s+(\S+)")
get_port_re = re.compile("^(CL\S+)\s+FIBRE\s+TAR\s+\S+\s+\S+\s+Y\s+PtoP\s+Y\s+\d\s+\d+\s+(\S+)\s+")
get_hostgroup_re = re.compile("CL\S+\s+(\d+)\s+(\S+)\s+\d+\s+(\S+)\s+(.+)$")
get_lun_re = re.compile("^CL\S+\s+\d+\s+\S+\s+(\d+)\s+\S+\s+(\S+)\s+")
get_hba_wwn_re = re.compile("^CL\S+\s+\S+\s+\S+\s+(\S+)\s+\S+\s+(\S+)")
get_login_re = re.compile("^CL\S+\s+(\S+)")
get_ldev_serial_re = re.compile("^Serial#\s+:")
get_ldev_id_re = re.compile("^LDEV\s+:\s+(\S+)")
get_ldev_vol_type_re = re.compile("^VOL_TYPE\s+:\s+(\S+)")
get_ldev_vol_cap_re = re.compile("^VOL_Capacity\(BLK\)\s+:\s+(\d+)")
get_ldev_ports_re = re.compile("^PORTs\s+:\s+(\S+)")
get_ldev_pool_re = re.compile("^B_POOLID\s+:\s+(\d+)")
get_ldev_status_re = re.compile("^STS\s+:\s+(\S+)")
get_ldev_vol_attr_re = re.compile("^VOL_ATTR\s+:\s+(.+)$")

empty_re = re.compile("^$")

port_list = []
hostgroup_list = []
lun_list = []
ldev_list = []
wwn_list = []
login_list = []

hostgroup_dict = {}

outdir = os.path.join("c:",os.sep,"TEMP","Tools")
outfile = "%s_collect.txt" % box_name

################################
# MAIN
################################

print "COLLECT started for box %s, serial %s, raidcom instance %s" % (box_name,box_serial,raidcom_inst)

### check the S/N and the resource lock/unlock status ###
get_resource_out = subprocess.Popen([raidcom_cmd,"get","resource",raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
for l in get_resource_out.splitlines():
    if get_resource_re.match(l):
        status = get_resource_re.match(l).group(1)
        serial = get_resource_re.match(l).group(2)
        if serial != box_serial:
            print "ERROR serial number does not match ! "
            sys.exit(1)
        if status != "Unlocked":
            print "ERROR resource locked ! "
            # sys.exit(1)

print "Starting collect on %s" % box_name

### get PORTS ###
get_port_out = subprocess.Popen([raidcom_cmd,"get","port",raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
for l in get_port_out.splitlines():
    if get_port_re.match(l):
        port_name = get_port_re.match(l).group(1)
        port_wwn = get_port_re.match(l).group(2)
        port = Port(port_name,port_wwn)
        port_list.append(port)

### get HOSTGROUPS ###
for port in port_list:
    print "collecting HOSTGROUPS on PORT %s" % port.name
    ### init ###
    if port.name not in hostgroup_dict:
        hostgroup_dict[port.name] = []
    get_hostgroup_out = subprocess.Popen([raidcom_cmd,"get","host_grp","-port",port.name,raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
    for l in get_hostgroup_out.splitlines():
        if get_hostgroup_re.match(l):
            group_id = get_hostgroup_re.match(l).group(1)
            group_name = get_hostgroup_re.match(l).group(2)
            host_mode = get_hostgroup_re.match(l).group(3)
            host_mode_opt = get_hostgroup_re.match(l).group(4)
            hostgroup = Hostgroup(port.name,group_name,host_mode,host_mode_opt,group_id)
            hostgroup_dict[port.name].append(group_name)
            hostgroup_list.append(hostgroup)

### get HBA_WWN ###
for port in port_list:
    for hostgroup_name in hostgroup_dict[port.name]:
        print "collecting WWNs on PORT %s, HOSTGROUP %s" % ( port.name,hostgroup_name )
        get_hba_wwn_out = subprocess.Popen([raidcom_cmd,"get","hba_wwn","-port",port.name,hostgroup_name,raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
        for l in get_hba_wwn_out.splitlines():
            if get_hba_wwn_re.match(l):
                wwn = get_hba_wwn_re.match(l).group(1)
                nick = get_hba_wwn_re.match(l).group(2)
                hba_wwn = Wwn(port.name,hostgroup_name,wwn,nick)
                wwn_list.append(hba_wwn)

### get LUNs ###
for port in port_list:
    for hostgroup_name in hostgroup_dict[port.name]:
        print "collecting LUNs on PORT %s, HOSTGROUP %s" % (port.name,hostgroup_name)
        get_lun_out = subprocess.Popen([raidcom_cmd,"get","lun","-port",port.name,hostgroup_name,raidcom_inst,"-fx"],stdout=subprocess.PIPE).communicate()[0]
        for l in get_lun_out.splitlines():
            if get_lun_re.match(l):
                lun_id = get_lun_re.match(l).group(1)
                ldev_id = get_lun_re.match(l).group(2)
                lun = Lun(port.name,hostgroup_name,lun_id,ldev_id)
                lun_list.append(lun)

### get LOGINs ###
for port in port_list:
    print "collecting LOGINs on PORT %s" % port.name
    get_login_out = subprocess.Popen([raidcom_cmd,"get","port","-port",port.name,raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
    for l in get_login_out.splitlines():
        if get_login_re.match(l):
            wwn = get_login_re.match(l).group(1)
            login = Login(port.name,wwn)
            login_list.append(login)

### get LDEV ###
print "collecting LDEVs "
get_ldev_out = subprocess.Popen([raidcom_cmd,"get","ldev","-ldev_list","defined",raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
# get_ldev_out = subprocess.Popen([raidcom_cmd,"get","ldev","-ldev_list","pool","-pool_id","27",raidcom_inst],stdout=subprocess.PIPE).communicate()[0]
for l in get_ldev_out.splitlines():
    # process ldev output 
    if get_ldev_serial_re.match(l):
        curr_ldev_id_hex = ""
        curr_ldev_vol_type = ""
        curr_ldev_vol_cap = ""
        curr_ldev_pool = ""
        curr_ldev_status = ""
        curr_ldev_vol_attr = ""
    if get_ldev_id_re.match(l):
        curr_ldev_id_dec = int(get_ldev_id_re.match(l).group(1))
        curr_ldev_id_hex = "%04x" % curr_ldev_id_dec
        # curr_ldev_id_hex = "%s:%s" % (curr_ldev_id_hex[0:2],curr_ldev_id_hex[2:4])
    if get_ldev_vol_type_re.match(l):
        curr_ldev_vol_type = get_ldev_vol_type_re.match(l).group(1)
    if get_ldev_vol_cap_re.match(l):
        curr_ldev_vol_cap = get_ldev_vol_cap_re.match(l).group(1)
    if get_ldev_vol_attr_re.match(l):
        curr_ldev_vol_attr = get_ldev_vol_attr_re.match(l).group(1)
    if get_ldev_pool_re.match(l):
        curr_ldev_pool = get_ldev_pool_re.match(l).group(1)
    if get_ldev_status_re.match(l):
        curr_ldev_status = get_ldev_status_re.match(l).group(1)
        ldev = Ldev(curr_ldev_id_hex,curr_ldev_vol_type,curr_ldev_vol_cap,curr_ldev_pool,curr_ldev_status,curr_ldev_vol_attr)
        ldev_list.append(ldev)

### REPORT ###
cf = open(os.path.join(outdir,outfile),"wt")

for port in port_list:
    cf.write("%s\n" % port )

for hostgroup in hostgroup_list:
    cf.write("%s\n" % hostgroup )

for wwn in wwn_list:
    cf.write("%s\n" % wwn )

for lun in lun_list:
    cf.write("%s\n" % lun )

for ldev in ldev_list:
    cf.write("%s\n" % ldev )

for login in login_list:
    cf.write("%s\n" % login )

cf.close()
