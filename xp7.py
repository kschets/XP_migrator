#!/usr/bin/python
""" XP7 Module
"""
import sys
import os.path
import csv
import string
import re
import copy

####################################################################################################
### Functions
####################################################################################################
def standard_format_ldev(ldev_nbr):
    ### remove : ###
    res = ldev_nbr.translate(None,":")
    res = res.translate(None,string.whitespace)
    ### lower case ###
    return res.lower()

def standard_format_wwn(wwn):
    ### remove : ###
    res = wwn.translate(None,":")
    res = res.translate(None,string.whitespace)
    ### lower case ###
    return res.lower()

def long_format_ldev(ldev_nbr):
    res = standard_format_ldev(ldev_nbr)
    res = "{}:{}".format(res[0:2].upper(),res[2:4].upper())
    return res

def long_format_wwn(wwn):
    res = standard_format_wwn(wwn)
    res = "{}:{}:{}:{}:{}:{}:{}:{}".format(res[0:2],res[2:4],res[4:6],res[6:8],res[8:10],res[10:12],res[12:14],res[14:16])
    return res.upper()

def convert_size(size):
    if size > 1024 ** 4:
        return "{0:d} TB".format( size / 1024**4 )
    elif size > 1024 ** 3:
        return "{0:d} GB".format( size / 1024**3 )
    elif size > 1024 ** 2:
        return "{0:d} MB".format( size / 1024**2 )
    elif size > 1024:
        return "{0:d} KB".format( size / 1024 )
    else:
        return "{0:d} B".format(size)
    
def port_nbr_even(port_name):
    if re.match("CL\d-\w",port_name):
        port_nbr = int(re.match("CL(\d)",port_name).group(1))
        if port_nbr % 2 == 0:
            return True
        else:
            return False
    else:
        return None
    
def get_port_fabric_nbr(port_name):
    if re.match("CL\d-\w",port_name):
        port_nbr = int(re.match("CL(\d)",port_name).group(1))
        if port_nbr % 2 == 0:
            return 2
        else:
            return 1
    else:
        return None
    
def short_port_name(port_name):
    if re.match("CL\d-\w",port_name):
        return "{}{}".format(re.match("CL(\d)",port_name).group(1),re.match("CL\d-(\w)",port_name).group(1))
    else:
        return None
    
####################################################################################################
### Class XP7 
####################################################################################################
class XP7:
    
    def __init__(self,name,instance_nbr,serial_nbr,location,collect_file):
        self.name = name
        self.peer_box = None
        self.target_box = None
        self.source_box = None
        self.collect_file = collect_file
        self.instance_nbr = int(instance_nbr)
        self.bc_instance_nbr = int(instance_nbr) + 10
        self.serial_nbr = serial_nbr
        self.location = location
        self.ldevs = []
        self.ioports = []
        self.hostgroups = []
        self.hba_wwns = []
        self.ldevs = []
        self.luns = []
        self.logins = []
        ### load collect file ###
        if os.path.exists(self.collect_file):
            with open(self.collect_file,"rt") as f:
                collect_file_reader = csv.reader(f,delimiter=",",quotechar="'")
                for row in collect_file_reader:
                    if row[0] == "PORT":
                        io_port = IO_Port(*row[1:3])
                        self.ioports.append(io_port)
                    if row[0] == "HOSTGROUP":
                        hostgroup = Hostgroup(*row[1:6])
                        self.hostgroups.append(hostgroup)
                    if row[0] == "WWN":
                        hba_wwn = HBA_Wwn(*row[1:5])
                        self.hba_wwns.append(hba_wwn)
                    if row[0] == "LDEV":
                        ldev = Ldev(*row[1:7])
                        self.ldevs.append(ldev)
                    if row[0] == "LUN":
                        lun = Lun(*row[1:5])
                        self.luns.append(lun)
                    if row[0] == "LOGIN":
                        login = Login(*row[1:3])
                        self.logins.append(login)
        else:
            print "ERROR could not find collect file {}".format(self.collect_file)
        ### sort the ldev list ###
        self.ldevs.sort(key=lambda x: x.nbr)
        ### define hostgroup_name_list ###
        self.hostgroup_name_list = list(sorted(set([x.name for x in self.hostgroups])))
        
    def __repr__(self):
        res ="{0:<30s} : {1:<10s}\n".format("BOX NAME",self.name)
        res +="{0:<30s} : {1:<10d}\n".format("SERIAL NBR",self.serial_nbr)
        res +="{0:<30s} : {1:<10d}\n".format("INSTANCE NBR",self.instance_nbr)
        res +="{0:<30s} : {1:<10s}\n".format("LOCATION",self.location)
        res +="{0:<30s} : {1:<10s}\n".format("COLLECT FILE",self.collect_file)
        res +="{0:<30s} : {1:<10s}\n".format("PEER BOX","" if self.peer_box is None else self.peer_box.name)
        res +="{0:<30s} : {1:d}\n".format("NBR of IO PORTs",len(self.ioports))
        res +="{0:<30s} : {1:d}\n".format("NBR of HOSTGROUPs",len(self.hostgroups))
        res +="{0:<30s} : {1:d}\n".format("NBR of HBA WWNs",len(self.hba_wwns))
        res +="{0:<30s} : {1:d}\n".format("NBR of LDEVs",len(self.ldevs))
        res +="{0:<30s} : {1:d}\n".format("NBR of LUNs",len(self.luns))
        res +="{0:<30s} : {1:d}\n".format("NBR of LOGINs",len(self.logins))
        return res
    
    def print_ldevs(self):
        """
        print the list of LDEVs 
        """
        for ldev in self.ldevs:
            print ldev
            
    def print_luns(self):
        """
        print the list of LUNs
        """
        for lun in self.luns:
            print lun
            
    def print_hostgroups(self):
        """
        print the list of hostgroups
        """
        for hostgroup in self.hostgroups:
            print hostgroup
            
    def print_ioports(self):
        """
        print the list of ioports
        """
        for ioport in self.ioports:
            print ioport
            
    def print_logins(self):
        """
        print the list of logins
        """
        for login in self.logins:
            print login
            
    def print_logins_per_port(self):
        for port_name in sorted([x.port_name for x in self.ioports]):
            logins_per_port = [x.wwn for x in self.logins if x.port_name == port_name]
            nicknames_per_port = []
            for wwn in logins_per_port:
                nickname = self.get_nickname(wwn)
                if nickname == "":
                    nicknames_per_port.append(wwn)
                else:
                    nicknames_per_port.append(nickname)
            print "{} : {}".format(port_name,",".join(nicknames_per_port))
        
    def get_nickname(self,wwn):
        res = ""
        for hba_wwn in self.hba_wwns:
            if hba_wwn.wwn == wwn:
                res = hba_wwn.nickname
        return res
    
    def test_ldev_free(self,ldev_id):
        ldev_set = set([x.nbr] for x in self.ldevs)
        if ldev_id in ldev_set:
            return False
        else:
            return True
        
    def test_logged_in(self,port_name,wwn):
        res = False
        for login in self.logins:
            if login.port_name == port_name and login.wwn == wwn:
                res = True
        return res
    
    def print_hostgroup(self,hostgroup_name=None):
        """
        print ports / hba_wwn / luns per hostgroup
        """
        if hostgroup_name is None:
            ### list all hostgroups ###
            hostgroup_name_list = self.hostgroup_name_list
        elif hostgroup_name in self.hostgroup_name_list:
            ### list only the requested hostgroup ###
            hostgroup_name_list = [hostgroup_name]
        else:
            hostgroup_name_list = []
        ### report on the hostgroups in the list ###
        for hostgroup_name in hostgroup_name_list:
            print "{:{fill}{align}{width}s}".format("=",fill="=",width=100,align="^")
            print "{:{fill}{align}{width}s}".format(hostgroup_name,fill="=",width=100,align="^")
            print "{:{fill}{align}{width}s}".format("=",fill="=",width=100,align="^")
            print
            ### ports ###
            hostgroup_list = [x for x in self.hostgroups if x.name == hostgroup_name]
            hostgroup_list.sort(key=lambda x: x.port_name)
            print "{:<50s} {:<10s} {:<10s} {:<20s} {:<10s}".format("HOSTGROUP","PORT","HOST MODE","HOST MODE OPTIONS","NBR")
            print "{:=<50s} {:=<10s} {:=<10s} {:=<20s} {:=<10s}".format("","","","","")
            for hostgroup in hostgroup_list:
                print "{:<50s} {:<10s} {:<10s} {:<20s} {:<10d}".format(hostgroup.name,hostgroup.port_name,hostgroup.mode,",".join(hostgroup.options),hostgroup.nbr)
            print
            ### hba_wwns ###
            hba_wwn_list = [x for x in self.hba_wwns if x.hostgroup_name == hostgroup_name]
            hba_wwn_list.sort(key=lambda x: x.port_name)
            print "{:<10s} {:<10s} {:<20s} {:<20s} {:<10s}".format("HBA_WWN","PORT","WWN","NICKNAME","LOGGED IN")
            print "{:=<10s} {:=<10s} {:=<20s} {:=<20s} {:=<10s}".format("","","","","")
            for hba_wwn in hba_wwn_list:
                print "{:<10s} {:<10s} {:<20s} {:<20s} {:<1s}".format("",hba_wwn.port_name,hba_wwn.wwn,hba_wwn.nickname,"V" if self.test_logged_in(hba_wwn.port_name,hba_wwn.wwn) else "X")
            print
            ### luns ###
            lun_list = [x for x in self.luns if x.hostgroup_name == hostgroup_name]
            lun_list.sort(key=lambda x: x.port_name)
            print "{:<10s} {:<10s} {:<10s} {:<10s}".format("LUN","PORT","LUN_ID","LDEV")
            print "{:=<10s} {:=<10s} {:=<10s} {:=<10s}".format("","","","","")
            for lun in lun_list:
                print "{:<10s} {:<10s} {:<10s} {:<10s}".format("",lun.port_name,lun.lun_id,lun.ldev_nbr)
            print
            
    def print_hostgroup_noluns(self,hostgroup_name=None):
        """
        print ports / hba_wwn per hostgroup
        """
        if hostgroup_name is None:
            ### list all hostgroups ###
            hostgroup_name_list = self.hostgroup_name_list
        elif hostgroup_name in self.hostgroup_name_list:
            ### list only the requested hostgroup ###
            hostgroup_name_list = [hostgroup_name]
        else:
            hostgroup_name_list = []
        ### report on the hostgroups in the list ###
        for hostgroup_name in hostgroup_name_list:
            print "{:{fill}{align}{width}s}".format("=",fill="=",width=100,align="^")
            print "{:{fill}{align}{width}s}".format(hostgroup_name,fill="=",width=100,align="^")
            print "{:{fill}{align}{width}s}".format("=",fill="=",width=100,align="^")
            print
            ### ports ###
            hostgroup_list = [x for x in self.hostgroups if x.name == hostgroup_name]
            hostgroup_list.sort(key=lambda x: x.port_name)
            print "{:<50s} {:<10s} {:<10s} {:<20s} {:<10s}".format("HOSTGROUP","PORT","HOST MODE","HOST MODE OPTIONS","NBR")
            print "{:=<50s} {:=<10s} {:=<10s} {:=<20s} {:=<10s}".format("","","","","")
            for hostgroup in hostgroup_list:
                print "{:<50s} {:<10s} {:<10s} {:<20s} {:<10d}".format(hostgroup.name,hostgroup.port_name,hostgroup.mode,",".join(hostgroup.options),hostgroup.nbr)
            print
            ### hba_wwns ###
            hba_wwn_list = [x for x in self.hba_wwns if x.hostgroup_name == hostgroup_name]
            hba_wwn_list.sort(key=lambda x: x.port_name)
            print "{:<10s} {:<10s} {:<20s} {:<20s} {:<10s}".format("HBA_WWN","PORT","WWN","NICKNAME","LOGGED IN")
            print "{:=<10s} {:=<10s} {:=<20s} {:=<20s} {:=<10s}".format("","","","","")
            for hba_wwn in hba_wwn_list:
                print "{:<10s} {:<10s} {:<20s} {:<20s} {:<1s}".format("",hba_wwn.port_name,hba_wwn.wwn,hba_wwn.nickname,"V" if self.test_logged_in(hba_wwn.port_name,hba_wwn.wwn) else "X")
            print
            ### luns ###
            lun_list = [x for x in self.luns if x.hostgroup_name == hostgroup_name]
            port_set = set([x.port_name for x in lun_list])
            print "{:<10s} {:<10s}".format("PORT","# LUNs")
            for port_name in sorted(port_set):
                print "{:<10s} {}".format(port_name,len([x for x in lun_list if x.port_name == port_name]))
            print
            
    def print_hostgroup_summary(self,hostgroup_name,indent=0):
        """
        print hostgroup name / host_mode / host_mode_options / nbr
        """
        if hostgroup_name not in self.hostgroup_name_list:
            return
        ### report on the hostgroups in the list, first match will do ###
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name:
                ### print summary ###
                print "{:{fill}{align}{width}} {:<30s} {:<20s} {:<10s}".format("",hostgroup.name,hostgroup.mode,",".join(hostgroup.options),fill=" ",align="<",width=indent)
                return
            
    def get_ldev_nbrs(self):
        """
        return all ldev nbrs
        """
        return sorted([x.nbr for x in self.ldevs])
        
    def get_ldev_mapping(self,ldev_nbr):
        """
        return the list of port / hostgroup_name / lun_id mappings found
        """
        res = []
        all_ldev_nbrs = set([x.nbr for x in self.ldevs])
        if ldev_nbr in all_ldev_nbrs:
            ### run the list of all luns ###
            for lun in self.luns:
                if lun.ldev_nbr == ldev_nbr:
                    ### we got a mapping ###
                    res.append(lun)
        ### sort the result per port ###
        res.sort(key=lambda x: x.port_name)
        return res
    
    def check_ldev_mapping(self,ldev_nbr):
        """
        return True if ldev mapping ok
        """
        res = True
        lun_list = self.get_ldev_mapping(ldev_nbr)
        hg_dict = {}
        ### arrange the luns per hostgroup ###
        for lun in lun_list:
            if lun.hostgroup_name not in hg_dict:
                hg_dict[lun.hostgroup_name] = []
            hg_dict[lun.hostgroup_name].append(lun)
        ### lun_ids should be the same per hostgroup ###
        for hg_name in hg_dict:
            lun_ids = set([x.lun_id for x in hg_dict[hg_name]])
            if len(lun_ids) > 1:
                res = False
        return res
    
    def get_hostgroups(self):
        return self.hostgroup_name_list
            
    def get_hostgroup_ldevs(self,hostgroup_name,port_name=None):
        """
        return the list of ldevs in the hostgroup
        """
        ldev_set = set()
        for lun in self.luns:
            if port_name is None and lun.hostgroup_name == hostgroup_name:
                ldev_set.add(lun.ldev_nbr)
            elif port_name is not None and lun.hostgroup_name == hostgroup_name and lun.port_name == port_name:
                ldev_set.add(lun.ldev_nbr)
        return list(sorted(ldev_set))
    
    def get_ldev(self,ldev_nbr):
        for ldev in self.ldevs:
            if ldev.nbr == ldev_nbr:
                return ldev
        return None
    
    def get_ldev_hostgroups(self,ldev_nbr):
        """
        return the list of hostgroups in which the ldev is mapped
        """
        res = set()
        lun_list = self.get_ldev_mapping(ldev_nbr)
        for lun in lun_list:
            res.add(lun.hostgroup_name)
        return list(sorted(res))
    
    def set_ldev_ca_bc(self,ldev_nbr,ca="SMPL",bc_1="SMPL",bc_2="SMPL",bc_3="SMPL"):
        """
        set the ldev CA and BC to SMPL,PVOL or SVOL
        """
        for ldev in self.ldevs:
            if ldev.nbr == ldev_nbr:
                if ca in ("SMPL","PVOL","SVOL"):
                    ldev.ca = ca
                if bc_1 in ("SMPL","PVOL","SVOL"):
                    ldev.bc_1 = bc_1
                if bc_2 in ("SMPL","PVOL","SVOL"):
                    ldev.bc_2 = bc_2
                if bc_3 in ("SMPL","PVOL","SVOL"):
                    ldev.bc_3 = bc_3
                    
    def get_ioport_wwn(self,port_name):
        """
        return the port wwn for zoning purposes
        """
        for ioport in self.ioports:
            if ioport.port_name == port_name:
                return ioport.port_wwn
            
    def test_hostgroup_consistency(self,hostgroup_name):
        """
        check hostgroup definitions on each port for consistent host_mode and host_mode_options
        """
        hm_set = set()
        hmo_set = set()
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name:
                hm_set.add(hostgroup.mode)
                hmo_set.add(",".join(hostgroup.options))
        ### each set should contain one element only ###
        if len(hm_set) == 1 and len(hmo_set) == 1:
            return True
        else:
            return False
        
    def get_hostgroup_hostmode(self,hostgroup_name):
        """
        return the hostmode
        """
        hm_set = set()
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name:
                hm_set.add(hostgroup.mode)
        ### set should contain one element only ###
        if len(hm_set) == 1:
            return list(hm_set)[0]
        else:
            return None
        
    def get_hostgroup_hostmode_options(self,hostgroup_name):
        """
        return the hostmode options
        """
        hmo_set = set()
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name:
                hmo_set.add(";".join(hostgroup.options))
        ### set should contain one element only ###
        if len(hmo_set) == 1:
            return list(hmo_set)[0]
        else:
            return None
        
    def get_hostgroups_per_portgroup(self,portgroup):
        """
        return the list of hostgroup names present on the ports listed in portgroup
        """
        hostgroup_name_set = set()
        for port_name in portgroup:
            for hostgroup in self.hostgroups:
                if hostgroup.port_name == port_name:
                    hostgroup_name_set.add(hostgroup.name)
        return list(sorted(hostgroup_name_set))
    
    def get_hosts_per_hostgroup(self,hostgroup_name):
        """
        return the list of hostnames found by examining the hba_wwns
        """
        res_set = set()
        for hba_wwn in self.hba_wwns:
            if hba_wwn.hostgroup_name == hostgroup_name:
                try:
                    hostname = hba_wwn.nickname.split("_")[0].lower()
                except:
                    print "ERROR in HBA_WWN nickname {} {} {}".format(self.name,hostgroup_name,hba_wwn.nickname)
                else:
                    res_set.add(hostname)
        return list(sorted(res_set))
            
    def assign_cluster_names(self,cluster_file):
        """
        read the cluster file and assign hostgroups the proper cluster names
        """
        cluster_re = re.compile("^(vcs\S+)\s+")
        host_re = re.compile("^(\S+)")
        comment_re = re.compile("--------")
        empty_re = re.compile("^$")
        
        if not os.path.exists(cluster_file):
            print "ERROR cluster file not found, exiting .."
            sys.exit(1)
        
        host_dict = {}
        cluster_dict = {}
        
        ### fill the host and cluster dict first ###
        with open(cluster_file,"rt") as f:
            for l in f:
                l = l.rstrip()
                if cluster_re.match(l):
                    current_cluster = cluster_re.match(l).group(1).upper()
                elif empty_re.match(l):
                    current_cluster = ""
                elif comment_re.match(l):
                    pass
                elif host_re.match(l):
                    current_host = host_re.match(l).group(1).lower()
                    host_dict[current_host] = current_cluster
                    if not current_cluster in cluster_dict:
                        cluster_dict[current_cluster] = set()
                    cluster_dict[current_cluster].add(current_host)
        ### then walk all hostgroups and set cluster names ###
        for hostgroup in self.hostgroups:
            cluster_name = None
            host_list = self.get_hosts_per_hostgroup(hostgroup.name)
            for host in host_list:
                if host in host_dict and cluster_name is None:
                    cluster_name = host_dict[host]
            if cluster_name is not None:
                hostgroup.cluster_name = cluster_name
            #     print "DBG set hostgroup {} to cluster name {}".format(hostgroup.name,hostgroup.cluster_name)
            # else:
            #     print "DBG no cluster name found for {}".format(hostgroup.name)
            
    def assign_ldev_xlate(self,ldevmap_file):
        """
        read the ldevmap file and assign old_ldev_nbr properties to migrated ldevs
        """
        xlate_dict = {}
        ### load the LDEV translation into a dict ###
        with open(ldevmap_file,"rt") as f:
            ldevmap_file_reader = csv.reader(row for row in f if not row.startswith('#'))
            for row in ldevmap_file_reader:
                source_box,source_ldev,target_box,target_ldev,owner = row
                if self.name == target_box:
                    xlate_dict[target_ldev] = source_ldev
        ### then update the source ldev on local ldevs ###
        for ldev in self.ldevs:
            if ldev.nbr in xlate_dict:
                ldev.old_ldev_nbr = xlate_dict[ldev.nbr]
                # print "DBG {} {} updated with source ldev {}".format(self.name,ldev.nbr,ldev.old_ldev_nbr)
        
    def get_cluster_name(self,hostgroup_name):
        """
        return the cluster name found for requested hostgroup
        """
        cluster_name = None
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name and cluster_name is None:
                if hostgroup.cluster_name is not None:
                    cluster_name = hostgroup.cluster_name
        return cluster_name
            
    def print_hostgroups_per_portgroup(self):
        """
        print the list of hostgroups per portgroup
        """
        for portgroup in portgroup_dict[self.name]:
            hostgroups_on_portgroup_list = self.get_hostgroups_per_portgroup(portgroup)
            print "PORTGROUP {:<10s} {:<20s} ( # {} )".format(self.name, "/".join(portgroup),len(hostgroups_on_portgroup_list))
            for hostgroup_name in hostgroups_on_portgroup_list:
                self.print_hostgroup_summary(hostgroup_name,indent=4)
                
    def get_new_hostgroups(self):
        """
        return hostgroup names which have new == True
        """
        res = []
        for hostgroup in self.hostgroups:
            if hostgroup.new == True:
                res.append(hostgroup.name)
        return res
                
    def add_hostgroup(self,hostgroup):
        """
        add hostgroup to the list and update hostgroup_name_list
        """
        if isinstance(hostgroup,Hostgroup):
            ### correct hostmode from LINUX/IRIX to LINUX ###
            if hostgroup.mode == "LINUX/IRIX":
                hostgroup.mode = "LINUX"
            self.hostgroups.append(hostgroup)
        ### update hostgroup_name_list ###
        self.hostgroup_name_list = list(sorted(set([x.name for x in self.hostgroups])))
        
    def add_ldev(self,ldev):
        """
        add a new ldev to this box
        """
        if isinstance(ldev,Ldev):
            ### does the new ldev exist already ? ###
            migrated_ldev_nbrs = set([x.old_ldev_nbr for x in self.ldevs])
            if ldev.nbr in migrated_ldev_nbrs:
                logger.debug("add_ldev : LDEV {} {} migrated already ..".format(self.name,ldev.nbr))
            else:
                ### create a new ldev object ###
                new_ldev = copy.copy(ldev)
                new_ldev.old_ldev_nbr = ldev.nbr
                ### find a free new ldev nbr ###
                if self.peer_box.xlate_ldev_nbr(ldev.nbr) is None:
                    self_free = self.get_next_ldev(environment)
                    peer_free = self.peer_box.get_next_ldev(environment)
                    new_ldev.nbr = "{:04x}".format(max(int(self_free,16),int(peer_free,16)))
                else:
                    ### it concerns an LDEV which is CA SVOL and the peer LDEV has been assigned a new LDEV nbr already ###
                    new_ldev.nbr = self.peer_box.xlate_ldev_nbr(ldev.nbr)
                ### pool depends on the environment ###
                new_ldev.pool = pool_dict[environment]
                new_ldev.mp_blade = mp_blade_cycle[environment].next()
                new_ldev.clpr = clpr_dict[environment]
                ### set the new attribute ###
                new_ldev.new = True
                ### append to the ldev list ###
                if ldev.ca == "SMPL":
                    ### Add on the local box only ###
                    self.ldevs.append(new_ldev)
                    self.ldevs.sort(key=lambda x: x.nbr)
                    logger.debug("add_ldev : LDEV {} {} is SMPL, new assigned ldev nbr is {}".format(self.name,ldev.nbr,new_ldev.nbr))
                elif ldev.ca == "PVOL":
                    ### Add on the local and peer box ###
                    # new_ca_svol = copy.copy(new_ldev)
                    # new_ca_svol.ca = "SVOL"
                    # new_ca_svol.bc_1 = "SMPL"
                    self.ldevs.append(new_ldev)
                    # self.peer_box.ldevs.append(new_ca_svol)
                    self.ldevs.sort(key=lambda x: x.nbr)
                    # self.peer_box.ldevs.sort(key=lambda x: x.nbr)
                    logger.debug("add_ldev : LDEV {} {} is CA PVOL, new assigned ldev nbr is {}".format(self.name,ldev.nbr,new_ldev.nbr))
                elif ldev.ca == "SVOL":
                    self.ldevs.append(new_ldev)
                    self.ldevs.sort(key=lambda x: x.nbr)
                    logger.debug("add_ldev : LDEV {} {} is CA SVOL, new assigned ldev nbr is {}".format(self.name,ldev.nbr,new_ldev.nbr))
                else:
                    logger.error("add_ldev : LDEV {} {} has unknown CA value {}".format(self.name,ldev.nbr,ldev.ca))
                ### if the ldev is a BC PVOL then add a new BC SVOL ###
                if ldev.bc_1 == "PVOL":
                    new_bc_svol = copy.copy(new_ldev)
                    new_bc_svol.bc_pvol = new_ldev.nbr
                    new_bc_svol.bc_1 = "SVOL"
                    new_bc_svol.ca = None
                    new_bc_svol.nbr = self.get_next_ldev("BC")
                    ### point the BC PVOL to the new BC SVOL ###
                    new_ldev.bc_svol = new_bc_svol.nbr
                    logger.debug("add_ldev : LDEV {} {} is BC PVOL, BC SVOL {} created".format(self.name,ldev.nbr,new_bc_svol.nbr))
                    self.ldevs.append(new_bc_svol)
                    self.ldevs.sort(key=lambda x: x.nbr)
        else:
            logger.error("{} not an LDEV".format(ldev))
            print "ERROR {} not an ldev".format(ldev)
            sys.exit(1)
            
    def get_new_ldevs(self):
        """
        return the list of new ldev nbrs
        """
        self.ldevs.sort(key=lambda x: x.nbr)
        res = []
        for ldev in self.ldevs:
            if ldev.new:
                res.append(ldev.nbr)
        return res
    
    def print_add_ldev_cmds(self,fh=None):
        """
        print the raidcom add ldev commands
        """
        res = "#\n"
        res += "# ADD LDEV on {}\n".format(self.name)
        res += "#\n"
        self.ldevs.sort(key=lambda x: x.nbr)
        cnt = 0
        for ldev in self.ldevs:
            if ldev.new:
                res += "raidcom add ldev -pool {} -capacity {} -mp_blade_id {} -clpr {} -ldev_id {} -I{}\n".format(
                    ldev.pool,ldev.size,ldev.mp_blade,ldev.clpr,long_format_ldev(ldev.nbr),self.instance_nbr
                )
                cnt += 1
                if cnt % 10 == 0:
                    res += "\n"
        ### issue modify ldev commands for cmd devices ###
        res += "\n"
        for ldev in self.ldevs:
            if ldev.new and "CMD" in ldev.attr_set:
                res += "raidcom modify ldev -ldev_id {} -command_device y -I{}\n".format(
                    long_format_ldev(ldev.nbr),self.instance_nbr
                )
        res += "\n"
        if fh is None:
            print res
        else:
            fh.write(res)
        
    def print_add_hostgroup_cmds(self,fh=None):
        """
        print the raidcom add hostgroup cmds
        """
        res = "#\n"
        res += "# ADD HOST_GRP on {}\n".format(self.name)
        res += "#\n"
        new_hostgroups = [x for x in self.hostgroups if x.new]
        hostgroup_set = set([x.name for x in new_hostgroups])
        new_hostgroups.sort(key=lambda x: x.port_name)
        for hostgroup_name in sorted(hostgroup_set):
            res += "#\n"
            res += "# ADD HOST_GRP {}\n".format(hostgroup_name)
            res += "#\n"
            for hostgroup in new_hostgroups:
                if hostgroup.name == hostgroup_name:
                    res += "raidcom add host_grp -port {} -host_grp_name {} -I{}\n".format(
                        hostgroup.port_name,hostgroup.name,self.instance_nbr
                    )
                    hmo = " ".join(hostgroup.options)
                    if hmo in (""," "):
                        res += "raidcom modify host_grp -port {} {} -host_mode {} -I{}\n".format(
                            hostgroup.port_name,hostgroup.name,hostgroup.mode,self.instance_nbr
                        )
                    else:
                        res += "raidcom modify host_grp -port {} {} -host_mode {} -host_mode_opt {} -I{}\n".format(
                            hostgroup.port_name,hostgroup.name,hostgroup.mode,hmo,self.instance_nbr
                        )
        if fh is None:
            print res
        else:
            fh.write(res)
                    
    def print_header(self,fh=None):
        """
        print the header for the provisioning script
        """
        res = "#\n"
        res += "# MIGRATION SCRIPT \n"
        res += "#\n"
        new_ldev_set = set()
        lcl_cap = 0
        peer_cap = 0
        lcl_ldevs = [x for x in self.ldevs if x.new]
        peer_ldevs = [x for x in self.peer_box.ldevs if x.new]
        for ldev in lcl_ldevs:
            new_ldev_set.add(ldev.nbr)
            lcl_cap += ldev.size
        for ldev in peer_ldevs:
            new_ldev_set.add(ldev.nbr)
            peer_cap += ldev.size
        ### summary ###
        res += "{0:<10s} # new ldevs : {1:d}\n".format(self.name,len(lcl_ldevs))
        res += "{0:<10s} # new ldevs : {1:d}\n".format(self.peer_box.name,len(peer_ldevs))
        res += "\n"
        res += "{0:<10s} added cap   : {1:<10s}\n".format(self.name,convert_size(lcl_cap * 512))
        res += "{0:<10s} added cap   : {1:<10s}\n".format(self.peer_box.name,convert_size(peer_cap * 512))
        res += "\n"
        ### new hostgroups ###
        res += "{0:<10s} HOSTGROUPS :\n".format(self.name)
        for hostgroup in self.hostgroups:
            if hostgroup.new:
                res += "{0:<10s} {1:<30s} {2:<10s} {3:<10s}\n".format(
                    hostgroup.port_name,hostgroup.name,hostgroup.mode,",".join(hostgroup.options)
                )
        res += "\n"
        res += "{0:<10s} HOSTGROUPS :\n".format(self.peer_box.name)
        for hostgroup in self.peer_box.hostgroups:
            if hostgroup.new:
                res += "{0:<10s} {1:<30s} {2:<10s} {3:<10s}\n".format(
                    hostgroup.port_name,hostgroup.name,hostgroup.mode,",".join(hostgroup.options)
                )
        res += "\n"
        ### new ldevs ###
        res += "{0:<10s}  {1:<4s}  {2:^10s} {3:<10s}  {4:<4s}\n".format(
            self.name,"LDEV","CA",self.peer_box.name,"LDEV"
        )
        for ldev in self.ldevs:
            if ldev.new:
                new_ldev_set.add(ldev.nbr)
        for ldev in self.peer_box.ldevs:
            if ldev.new:
                new_ldev_set.add(ldev.nbr)
        for ldev_nbr in sorted(new_ldev_set):
            lcl_ldev = self.get_ldev(ldev_nbr)
            peer_ldev = self.peer_box.get_ldev(ldev_nbr)
            ### set the CA arrow ###
            if lcl_ldev is not None and lcl_ldev.ca == "PVOL":
                ca_direction = "==>>"
            elif peer_ldev is not None and peer_ldev.ca == "PVOL":
                ca_direction = "<<=="
            else:
                ca_direction = "    "
            ### print a line per ldev pair ###
            res += "{0:<10s} ({1:<4s}) {2:^10s} {3:<10s} ({4:<4s})\n".format(
                "" if lcl_ldev is None else lcl_ldev.nbr,
                "" if lcl_ldev is None else lcl_ldev.old_ldev_nbr,
                ca_direction,
                "" if peer_ldev is None else peer_ldev.nbr,
                "" if peer_ldev is None else peer_ldev.old_ldev_nbr,
            )
        if fh is None:
            print res
        else:
            fh.write(res)
            
    def xlate_ldev_nbr(self,old_ldev_nbr):
        """
        return the new ldev nbr
        """
        for ldev in self.ldevs:
            if ldev.old_ldev_nbr == old_ldev_nbr:
                return ldev.nbr
        return None
    
    def add_lun(self,lun):
        """
        add lun to the new hostgroups
        """
        if isinstance(lun,Lun):
            ### check if the hostgroup changes names ###
            if self.source_box.get_cluster_name(lun.hostgroup_name) is not None:
                new_hostgroup_name = self.source_box.get_cluster_name(lun.hostgroup_name)
            else:
                new_hostgroup_name = lun.hostgroup_name
            # print "DBG add_lun, new hostgroup name is {},old hostgroup name is {}".format(new_hostgroup_name,lun.hostgroup_name)
            ### do the old to new ldev translation ###
            new_ldev_nbr = self.xlate_ldev_nbr(lun.ldev_nbr)
            if new_ldev_nbr is None:
                logger.error("add_lun : old lun {}, could not find new ldev nbr for {}".format(lun,lun.ldev_nbr ))
            else:
                # print "DBG add_lun, {} => {}".format(lun.ldev_nbr,new_ldev_nbr)
                ### check if the ldev is not mapped already in the hostgroup ###
                ### WRONG check : check if the ldev is already mapped in the hostgroup on this port !! ###
                # new_ldev_list = self.get_hostgroup_ldevs(new_hostgroup_name,port_name=lun.port_name)
                new_ldev_list = self.get_hostgroup_ldevs(new_hostgroup_name)
                if new_ldev_nbr in new_ldev_list:
                    logger.info("add_lun : old lun {}, ldev mapped in hostgroup {} already".format(lun,new_hostgroup_name))
                else:
                    ### map the ldev in the new hostgroup ###
                    port_list = self.get_hostgroup_ports(new_hostgroup_name)
                    logger.debug("add_lun : old lun {}, new mapping for ldev {} on ports {}".format(lun,new_ldev_nbr,",".join(port_list)))
                    for port in port_list:
                        new_lun = Lun(port,new_hostgroup_name,9999,new_ldev_nbr,new=True)
                        # print "DBG add_lun, new lun appended {}".format(new_lun)
                        self.luns.append(new_lun)
        else:
            logger.error("{} not a lun".format(lun))
            print "ERROR {} not a lun".format(lun)
            sys.exit(1)
                
    def get_hostgroup_ports(self,hostgroup_name):
        """
        return the list of ports on which hostgroup occurs
        """
        res_set = set()
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name:
                res_set.add(hostgroup.port_name)
        return list(sorted(res_set))
        
    def print_add_lun_cmds(self,fh=None):
        """
        print the raidcom add lun cmds
        """
        res = "#\n"
        res += "# ADD LUN on {}\n".format(self.name)
        res += "#\n"
        cnt = 0
        new_luns = [x for x in self.luns if x.new]
        hostgroup_set = set([x.hostgroup_name for x in new_luns])
        new_luns.sort(key=lambda x: x.port_name)
        ### issue the add lun cmds per hostgroup ###
        for hostgroup_name in sorted(hostgroup_set):
            res += "#\n"
            res += "# ADD LUN cmds for {}\n".format(hostgroup_name)
            res += "#\n"
            for lun in new_luns:
                if lun.hostgroup_name == hostgroup_name:
                    res += "raidcom add lun -port {} {} -ldev_id {} -I{}\n".format(
                        lun.port_name,lun.hostgroup_name,long_format_ldev(lun.ldev_nbr),self.instance_nbr
                    )
                    cnt += 1
                    if cnt % 10 == 0:
                        res += "\n"
            res += "\n"
        if fh is None:
            print res
        else:
            fh.write(res)
            
    def get_hostgroup_hba_wwns(self,hostgroup_name):
        """
        return the list of hba_wwns in the hostgroup
        """
        res = []
        for hba_wwn in self.hba_wwns:
            if hba_wwn.hostgroup_name == hostgroup_name:
                res.append(hba_wwn)
        return res
    
    def get_hostgroup_luns(self,hostgroup_name):
        """
        return the list of luns in the hostgroup
        """
        lun_list = [x for x in self.luns if x.hostgroup_name == hostgroup_name]
        lun_list.sort(key=lambda x: x.port_name)
        return lun_list
    
    def add_hba_wwn(self,hba_wwn):
        """
        add hba_wwn to the new hostgroups
        """
        if isinstance(hba_wwn,HBA_Wwn):
            ### check if the hostgroup changes names ###
            if self.source_box.get_cluster_name(hba_wwn.hostgroup_name) is not None:
                new_hostgroup_name = self.source_box.get_cluster_name(hba_wwn.hostgroup_name)
            else:
                new_hostgroup_name = hba_wwn.hostgroup_name
            port_list = self.get_hostgroup_ports(new_hostgroup_name)
            even_port_list = [x for x in port_list if port_nbr_even(x)]
            odd_port_list = [x for x in port_list if not port_nbr_even(x)]
            if port_nbr_even(hba_wwn.port_name):
                ### add new hba_wwn on even ports ###
                for port_name in even_port_list:
                    new_hba_wwn = HBA_Wwn(port_name,new_hostgroup_name,hba_wwn.wwn,hba_wwn.nickname.lower(),new=True)
                    self.hba_wwns.append(new_hba_wwn)
                    logger.debug("add_hba_wwn {} : old hba_wwn {}".format(self.name,hba_wwn))
                    logger.debug("add_hba_wwn {} : new hba_wwn {}".format(self.name,new_hba_wwn))
            else:
                ### add new hba_wwn on odd ports ###
                for port_name in odd_port_list:
                    new_hba_wwn = HBA_Wwn(port_name,new_hostgroup_name,hba_wwn.wwn,hba_wwn.nickname.lower(),new=True)
                    self.hba_wwns.append(new_hba_wwn)
                    logger.debug("add_hba_wwn {} : old hba_wwn {}".format(self.name,hba_wwn))
                    logger.debug("add_hba_wwn {} : new hba_wwn {}".format(self.name,new_hba_wwn))
        else:
            logger.error("{} not a HBA_wwn".format(hba_wwn))
            print "ERROR {} not a hba_wwn".format(hba_wwn)
            sys.exit(1)
            
    def print_add_hba_wwn_cmds(self,fh=None):
        """
        print the add hba_wwn cmds
        """
        res = "#\n"
        res += "# ADD HBA_WWN on {}\n".format(self.name)
        res += "#\n"
        new_hba_wwns = [x for x in self.hba_wwns if x.new]
        hostgroup_set = set([x.hostgroup_name for x in new_hba_wwns])
        new_hba_wwns.sort(key=lambda x: x.port_name)
        for hostgroup_name in sorted(hostgroup_set):
            res += "#\n"
            res += "# ADD HBA_WWN cmds for {}\n".format(hostgroup_name)
            res += "#\n"
            for hba_wwn in new_hba_wwns:
                if hba_wwn.hostgroup_name == hostgroup_name:
                    res += "raidcom add hba_wwn -port {} {} -hba_wwn {} -I{}\n".format(
                        hba_wwn.port_name,hba_wwn.hostgroup_name,hba_wwn.wwn,self.instance_nbr
                    )
                    res += "raidcom set hba_wwn -port {} {} -hba_wwn {} -wwn_nickname {} -I{}\n".format(
                        hba_wwn.port_name,hba_wwn.hostgroup_name,hba_wwn.wwn,hba_wwn.nickname,self.instance_nbr
                    )
                    res += "\n"
        if fh is None:
            print res
        else:
            fh.write(res)
                    
    def print_port_login_check_cmds(self,fh=None):
        """
        print the cmds to check if all new hba_wwns were logged in to the target ports
        """
        res = "#\n"
        res += "# PORT login check {}\n".format(self.name)
        res += "#\n"
        new_hba_wwns = [x for x in self.hba_wwns if x.new]
        hostgroup_set = set([x.hostgroup_name for x in new_hba_wwns])
        new_hba_wwns.sort(key=lambda x: x.port_name)
        for hostgroup_name in sorted(hostgroup_set):
            res += "#\n"
            res += "# PORT login check for {}\n".format(hostgroup_name)
            res += "#\n"
            for hba_wwn in new_hba_wwns:
                if hba_wwn.hostgroup_name == hostgroup_name:
                    res += "# login check {} {}\n".format(hba_wwn.hostgroup_name,hba_wwn.nickname)
                    res += "raidcom get port -port {} -I{} | grep {}\n".format(
                        hba_wwn.port_name,self.instance_nbr,hba_wwn.wwn
                    )
        if fh is None:
            print res
        else:
            fh.write(res)
        
    def add_bc_svol_luns(self):
        """
        add luns to map BC SVOLs
        """
        new_bc_svol_ldevs = [x for x in self.ldevs if x.new and x.bc_pvol is not None]
        logger.debug("add_bc_svol_luns {} : start mapping {} BC SVOLs".format(self.name,len(new_bc_svol_ldevs)))
        hostgroup_name = self.bc_host.upper()
        already_mapped_ldevs = self.get_hostgroup_ldevs(hostgroup_name)
        for new_bc_svol_ldev in new_bc_svol_ldevs:
            if new_bc_svol_ldev.nbr in already_mapped_ldevs:
                logger.error("add_bc_svol_luns {} : new BC SVOL {} mapped already".format(self.name,new_bc_svol_ldev.nbr))
            else:
                ### map the ldev in the BC hostgroup ###
                port_list = self.get_hostgroup_ports(hostgroup_name)
                if len(port_list) == 0:
                    print "ERROR BC HOST {} not defined on target box {}, could not find ports, exiting..".format(
                        hostgroup_name,self.name
                        )
                    logger.error("ERROR BC HOST {} not defined on target box {}, could not find ports, exiting..".format(
                        hostgroup_name,self.name
                        ))
                    sys.exit(1)
                logger.debug("add_bc_svol_luns {} : mapping {} BC SVOL on ports {}".format(self.name,new_bc_svol_ldev.nbr,",".join(port_list)))
                for port in port_list:
                    new_lun = Lun(port,hostgroup_name,9999,new_bc_svol_ldev.nbr,new=True)
                    self.luns.append(new_lun)
                    
    def print_add_bc_svol_lun_cmds(self,fh=None):
        """
        print the raidcom add BC SVOL lun cmds
        """
        res = "#\n"
        res += "# ADD LUN for BC SVOLs on {}\n".format(self.name)
        res += "#\n"
        cnt = 0
        new_luns = [x for x in self.luns if x.new]
        new_luns.sort(key=lambda x: x.port_name)
        hostgroup_name = self.bc_host.upper()
        for lun in new_luns:
            if lun.hostgroup_name == hostgroup_name:
                res += "raidcom add lun -port {} {} -ldev_id {} -I{}\n".format(
                    lun.port_name,lun.hostgroup_name,long_format_ldev(lun.ldev_nbr),self.instance_nbr
                )
                cnt += 1
                if cnt % 10 == 0:
                    res += "\n"
        if fh is None:
            print res
        else:
            fh.write(res)
                    
    def print_horcm_ldev(self,hostgroup_name,dev_group,fh=None):
        """
        print the HORCM_LDEV entries
        """
        ldev_nbr_list = self.get_hostgroup_ldevs(hostgroup_name)
        res = "HORCM_LDEV\n"
        res += "{:<30s}    {:<30s}    {:<20s}    {:<20s}    {:<20s}\n".format(
            "# dev_grp","dev_name","serial_nbr","ldev_nbr","mu_nbr"
        )
        for ldev_nbr in ldev_nbr_list:
            ldev = self.get_ldev(ldev_nbr)
            res += "{:<30s}    {:<30s}    {:<20d}    {:<20s}    {:<20s}\n".format(
                dev_group,dev_group + "_" + ldev.standard_format(),self.serial_nbr,ldev.long_format(),"0"
            )
        if fh is None:
            print res
        else:
            fh.write(res)
            
    def test_hostgroup_exists(self,hostgroup_name):
        hg_exists = False
        for hostgroup in self.hostgroups:
            if hostgroup.name == hostgroup_name:
                hg_exists = True
        return hg_exists
        
    def get_hostgroup_noluns(self,hostgroup_name=None):
        """
        return ports / hba_wwn per hostgroup
        """
        res = []
        if hostgroup_name is None:
            ### list all hostgroups ###
            hostgroup_name_list = self.hostgroup_name_list
        elif hostgroup_name in self.hostgroup_name_list:
            ### list only the requested hostgroup ###
            hostgroup_name_list = [hostgroup_name]
        else:
            hostgroup_name_list = []
        ### report on the hostgroups in the list ###
        for hostgroup_name in hostgroup_name_list:
            res.append("{:{fill}{align}{width}s}".format("=",fill="=",width=100,align="^"))
            res.append("{:{fill}{align}{width}s}".format(hostgroup_name,fill="=",width=100,align="^"))
            res.append("{:{fill}{align}{width}s}".format("=",fill="=",width=100,align="^"))
            res.append("")
            ### ports ###
            hostgroup_list = [x for x in self.hostgroups if x.name == hostgroup_name]
            hostgroup_list.sort(key=lambda x: x.port_name)
            res.append("{:<50s} {:<10s} {:<10s} {:<20s} {:<10s}".format("HOSTGROUP","PORT","HOST MODE","HOST MODE OPTIONS","NBR"))
            res.append("{:=<50s} {:=<10s} {:=<10s} {:=<20s} {:=<10s}\n".format("","","","",""))
            for hostgroup in hostgroup_list:
                res.append("{:<50s} {:<10s} {:<10s} {:<20s} {:<10d}".format(hostgroup.name,hostgroup.port_name,hostgroup.mode,",".join(hostgroup.options),hostgroup.nbr))
            res.append("")
            ### hba_wwns ###
            hba_wwn_list = [x for x in self.hba_wwns if x.hostgroup_name == hostgroup_name]
            hba_wwn_list.sort(key=lambda x: x.port_name)
            res.append("{:<10s} {:<10s} {:<20s} {:<20s} {:<10s}".format("HBA_WWN","PORT","WWN","NICKNAME","LOGGED IN"))
            res.append("{:=<10s} {:=<10s} {:=<20s} {:=<20s} {:=<10s}".format("","","","",""))
            for hba_wwn in hba_wwn_list:
                res.append("{:<10s} {:<10s} {:<20s} {:<20s} {:<1s}".format("",hba_wwn.port_name,hba_wwn.wwn,hba_wwn.nickname,"V" if self.test_logged_in(hba_wwn.port_name,hba_wwn.wwn) else "X"))
            res.append("")
            ### luns ###
            lun_list = [x for x in self.luns if x.hostgroup_name == hostgroup_name]
            port_set = set([x.port_name for x in lun_list])
            res.append("{:<10s} {:<10s}".format("PORT","# LUNs"))
            res.append("{:=<10s} {:=<10s}".format("",""))
            for port_name in sorted(port_set):
                res.append("{:<10s} {}".format(port_name,len([x for x in lun_list if x.port_name == port_name])))
            res.append("")
        return res
    
    def get_hostgroup_consistency(self,hostgroup_name):
        """
        return the report on hostgroup consistency
        """
        res = []
        result = True
        if self.test_hostgroup_exists(hostgroup_name):
            ### hostmode and hostmode options test ### 
            hm_set = set()
            hmo_set = set()
            for hostgroup in self.hostgroups:
                if hostgroup.name == hostgroup_name:
                    hm_set.add(hostgroup.mode)
                    hmo_set.add(",".join(hostgroup.options))
            if len(hm_set) != 1:
                result = False
                res.append("    host modes are not consistent")
            if len(hmo_set) != 1:
                result = False
                res.append("    host mode options are not consistent")
            ### LDEV test ###
            lun_list = [x for x in self.luns if x.hostgroup_name == hostgroup_name]
            port_set = set([x.port_name for x in lun_list])
            if len(port_set) % 2 != 0:
                result = False
                res.append("    hostgroup defined on odd number of ports")
            base_set = None
            for port_name in sorted(port_set):
                new_set = set([x.ldev_nbr for x in lun_list if x.port_name == port_name])
                if base_set is None:
                    base_set = new_set
                else:
                    if len(base_set.difference(new_set)) != 0:
                        result = False
                        res.append("    LDEVs differ on different ports")
            res.append("")
            if result:
                res.insert(0,"{}-{} is consistent".format(self.name,hostgroup_name))
            else:
                res.insert(0,"{}-{} is not consistent".format(self.name,hostgroup_name))
            return result,res
        else:
            res.append("{}-{} does not exists".format(self.name,hostgroup_name))
            res.append("")
            return False,res
    
    def print_provisioning(self,hostgroup_name,fh=None):
        """
        print the provisioning list
        """
        ldev_nbr_list = self.get_hostgroup_ldevs(hostgroup_name)
        res = "# XPMIG mapping file for {}-{}\n".format(self.name,hostgroup_name)
        res += "# {},{},{},{},{}\n".format("SOURCE BOX S/N","SOURCE LDEV nbr","SOURCE LDEV size","TARGET BOX S/N","TARGET VOLUME nbr")
        for ldev_nbr in ldev_nbr_list:
            ldev = self.get_ldev(ldev_nbr)
            if ldev.is_cmd_device():
                res += "# {} is a CMD device\n".format(ldev.nbr.upper())
            else:
                res += "{},{},{}\n".format(self.serial_nbr,ldev.nbr.upper(),ldev.size)
        if fh is None:
            print res
        else:
            fh.write(res)
            
####################################################################################################
### Class IO_Port
####################################################################################################
# PORT,CL4-M,50060e80164ed63b
class IO_Port:
    
    def __init__(self,port_name,port_wwn):
        self.port_name = port_name
        self.port_wwn = standard_format_wwn(port_wwn)
        
    def __repr__(self):
        return "PORT {} WWN {}".format(self.port_name,self.port_wwn)
    
####################################################################################################
### Class Hostgroup
####################################################################################################
# HOSTGROUP,CL1-A,UCAP4020,HP-XP,12,2
# HOSTGROUP,CL1-J,OXXP2014-2018_OBSOLETE,SOLARIS,2;22,1
class Hostgroup:
    
    def __init__(self,port_name,hostgroup_name,host_mode,host_mode_options,hostgroup_id,new=False,cluster_name=None):
        self.name = hostgroup_name
        self.port_name = port_name
        self.mode = host_mode
        self.options = host_mode_options.split(";")
        self.nbr = int(hostgroup_id)
        self.new = new
        self.cluster_name = cluster_name
        
    def __repr__(self):
        return "HOSTGROUP {} PORT {} MODE {} OPTIONS {} NBR {} NEW {} CLUSTER_NAME {}".format(self.name,self.port_name,self.mode,";".join(self.options),self.nbr,"V" if self.new else "X",self.cluster_name)
    
    def test_is_generic(self):
        if self.nbr == 0:
            return True
        else:
            return False
        
####################################################################################################
### Class HBA_Wwn
####################################################################################################
# WWN,CL1-D,N-HPM13-14,50014380167ce38c,n-hpm13_hba0
class HBA_Wwn:
    
    def __init__(self,port_name,hostgroup_name,wwn,hba_wwn_nickname,new=False):
        self.hostgroup_name = hostgroup_name
        self.port_name = port_name
        self.wwn = standard_format_wwn(wwn)
        self.nickname = hba_wwn_nickname
        self.new = new

    def __repr__(self):
        return "HBA_WWN HOSTGROUP {} PORT {} WWN {} NICKNAME {}".format(self.hostgroup_name,self.port_name,self.wwn,self.nickname)
    
####################################################################################################
### Class Ldev
####################################################################################################
# LDEV,2a11,OPEN-V-CVS,NML,20971520,26,CVS : HORC : MRCF : THP : SMRT
class Ldev:
    
    def __init__(self,ldev_nbr,ldev_type,ldev_status,ldev_size,ldev_pool,ldev_attr,mp_blade=0,clpr=0,old_ldev_nbr=None):
        self.nbr = standard_format_ldev(ldev_nbr)
        self.type = ldev_type
        self.status = ldev_status
        self.size = int(ldev_size)
        if ldev_pool == "":
            self.pool = 0
        else:
            self.pool = int(ldev_pool)
        self.attr = ldev_attr
        self.attr_set = set( self.attr.translate(None,string.whitespace).split(":"))
        self.new = False
        self.reserved = False
        self.ca = None
        self.bc_1 = None
        self.bc_2 = None
        self.bc_3 = None
        self.mp_blade = int(mp_blade)
        self.clpr = int(clpr)
        self.old_ldev_nbr = old_ldev_nbr
        self.bc_pvol = None
        self.bc_svol = None
        
    def __repr__(self):
        res = "LDEV {} :\n".format(self.nbr)
        res += "{:<4s}TYPE        : {:<10}\n".format("",self.type)
        res += "{:<4s}STATUS      : {:<10}\n".format("",self.status)
        res += "{:<4s}SIZE        : {:<10}\n".format("",self.size)
        res += "{:<4s}POOL        : {:<10}\n".format("",self.pool)
        res += "{:<4s}ATTR        : {:<10}\n".format("",",".join(self.attr_set))
        res += "{:<4s}CA          : {:<10}\n".format("",self.ca)
        res += "{:<4s}BC 1        : {:<10}\n".format("",self.bc_1)
        res += "{:<4s}BC 2        : {:<10}\n".format("",self.bc_2)
        res += "{:<4s}BC 3        : {:<10}\n".format("",self.bc_3)
        res += "{:<4s}IS NEW      : {:<10}\n".format("",self.new)
        res += "{:<4s}IS RESERVED : {:<10}\n".format("",self.reserved)
        res += "{:<4s}MP BLADE    : {:<10}\n".format("",self.mp_blade)
        res += "{:<4s}CLPR        : {:<10}\n".format("",self.clpr)
        res += "{:<4s}OLD LDEV    : {:<10}\n".format("",self.old_ldev_nbr)
        return res

    def is_cmd_device(self):
        """
        return True if the ldev is a command device
        """
        if "CMD" in self.attr_set:
            return True
        else:
            return False
        
    def convert_size(self):
        """
        return the ldev size in human readble format
        """
        nbr_bytes = self.size * 512
        if nbr_bytes > 1024 ** 4:
            return "{0:d} TB".format(nbr_bytes / 1024**4 )
        elif nbr_bytes > 1024 ** 3:
            return "{0:d} GB".format(nbr_bytes / 1024**3 )
        elif nbr_bytes > 1024 ** 2:
            return "{0:d} MB".format(nbr_bytes / 1024**2 )
        elif nbr_bytes > 1024:
            return "{0:d} KB".format(nbr_bytes / 1024 )
        else:
            return "{0:d} B".format(nbr_bytes)
        
    def standard_format(self):
        ### remove : ###
        res = self.nbr.translate(None,":")
        res = res.translate(None,string.whitespace)
        ### lower case ###
        return res.lower()
    
    def long_format(self):
        res = self.standard_format()
        res = "{}:{}".format(
            res[0:2],res[2:4]
        )
        return res.upper()
            
####################################################################################################
### Class Lun
####################################################################################################
# LUN,CL1-B,OMEN2004-2005-2006-CL1-B-CL2-B_OBSOLETE,124,24c4
class Lun:
    
    def __init__(self,port_name,hostgroup_name,lun_id,ldev_nbr,new=False):
        self.port_name = port_name
        self.lun_id = lun_id
        self.ldev_nbr = standard_format_ldev(ldev_nbr)
        self.hostgroup_name = hostgroup_name
        self.new = new
        
    def __repr__(self):
        return "LUN {} HOSTGROUP {} PORT {} LDEV {}".format(self.lun_id,self.hostgroup_name,self.port_name,self.ldev_nbr)
    

####################################################################################################
### Class Login
####################################################################################################
# LOGIN,CL8-E,50060b0000c27202
class Login:
    
    def __init__(self,port_name,wwn):
        self.port_name = port_name
        self.wwn = standard_format_wwn(wwn)
        
    def __repr__(self):
        return "LOGIN {} PORT {}".format(self.port_name,self.wwn)

####################################################################################################
### Class Table
####################################################################################################
class TabLine:
    
    def __init__(self,val_list,width):
        self.width = width
        self.cols = len(val_list)
        self.colwidth = ( width -2 ) / self.cols
        self.values = val_list
        
    def __repr__(self):
        res = "  "
        for val in self.values:
            res += "{:{fill}{align}{width}}".format(val,fill="",align="<",width=self.colwidth)
        return res
    
class Table:
    
    def __init__(self,title,cols,width=120,char="#"):
        self.title = title.upper()
        self.linelen = width
        self.txtlen = width - 2
        self.cols = cols
        self.char = char
        self.header = []
        self.lines = []
        
    def __repr__(self):
        ### TITLE ###
        res = self.char * self.linelen + "\n"
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char," ",self.char,fill=" ",width=self.txtlen,align="^")
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char,self.title,self.char,fill=" ",width=self.txtlen,align="^")
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char," ",self.char,fill=" ",width=self.txtlen,align="^")
        res += self.char * self.linelen + "\n"
        ### HEADER ###
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char," ",self.char,fill=" ",width=self.txtlen,align="^")
        res += "{}{}{}\n".format(self.char,TabLine(self.header,self.txtlen),self.char)
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char," ",self.char,fill=" ",width=self.txtlen,align="^")
        res += self.char * self.linelen + "\n"
        ### VALUES ###
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char," ",self.char,fill=" ",width=self.txtlen,align="^")
        for line in self.lines:
            res += "{}{}{}\n".format(self.char,TabLine(line,self.txtlen),self.char)
        res += "{}{:{fill}{align}{width}}{}\n".format(self.char," ",self.char,fill=" ",width=self.txtlen,align="^")
        res += self.char * self.linelen + "\n"
        return res
    
    def set_header(self,header_list):
        if len(header_list) == self.cols:
            self.header = header_list
    
    def add_line(self,value_list):
        if len(value_list) == self.cols:
            self.lines.append(value_list)
