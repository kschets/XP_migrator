#!/usr/bin/python
"""
####################################################################################################

TITLE : HPE XP7 Migration, Precheck

DESCRIPTION :  Precheck to examine hostgroup is ready for migration
    
AUTHOR : Koen Schets / StorageTeam

VERSION : Based on previous ODR framework
    1.0 Initial version
    1.1 Curses menu structure added
    1.2 Add search term criteria
    1.3 Add config file 

CONFIG : xpmig.ini

LOG : xpmig_precheck.log

TODO :
    add print selected hostgroup summary to main menu
    add check selected hostgroup to main menu
    add generate temporary horcm file and daemon to pairdisplay & check on status 
    add read xpinfo file to main menu
    add write provisioning file out to main menu

####################################################################################################
"""
import curses
from curses import panel
import re
import logging
import logging.handlers
import copy
from ConfigParser import ConfigParser
import sys
import xp7

####################################################################################################
### VARIABLES 
####################################################################################################
linelen = 100
boxpair_dict = {}
serialnbr_dict = {}
instance_dict = {}
site_dict = {}
collectfile_dict = {}
box_dict = {}

####################################################################################################
### FUNCTIONS
####################################################################################################
####################################################################################################
### CLASSES
####################################################################################################
class Menu(object):
    
    def __init__(self,window,items,stdscr):
        self.window = window
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
                self.window.addstr(1+index,2,line,mode)
            
            key = self.window.getch()
            
            if key in [curses.KEY_ENTER,ord("\n")]:
                if self.position == len(self.items) - 1:
                    break
                else:
                    self.items[self.position][1]()
            elif key == curses.KEY_UP:
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
                
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        
class InputMenu(object):
    
    def __init__(self,window,text,upd_obj,stdscr):
        self.window = window
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.text = text
        self.reply = ""
        self.update_object = upd_obj
        
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        line = "{}: ".format(self.text)
        self.window.addstr(1,2,line)
        curses.echo()
        self.window.refresh()
        curses.doupdate()
        self.reply = self.window.getstr()
        ### after we received the response ###
        self.update_object.set(self.reply)
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.noecho()
        curses.doupdate()
        
class SelectMenu(object):
    
    def __init__(self,window,items,boxpair_name,selection,search,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.items = items
        self.filtered_items = copy.copy(self.items)
        self.filtered_items.append("exit")
        ### slice is a view on the items which fits in the window ### 
        self.slice_start = 0
        self.slice_len = min(len(self.filtered_items)-1,self.heigth-6)
        self.slice_end = self.slice_start + self.slice_len
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.position = 0
        self.selection = selection
        self.search = search
        self.boxpair_name = boxpair_name
        
    def update(self):
        """
        update the items list to contain only HG matching the new search criteria
        """
        if self.search.get() != "":
            logger.debug("SelectMenu.update :: update items to match search str {}".format(self.search.get()))
            self.filtered_items = [x for x in self.items if re.search(self.search.get(),x,flags=re.IGNORECASE)]
        else:
            logger.debug("SelectMenu.update :: update items to match search all")
            self.filtered_items = copy.copy(self.items)
        self.filtered_items.append("exit")
        self.slice_start = 0
        self.slice_end = self.slice_start + self.slice_len
        self.position = 0
        
    def navigate(self,n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.filtered_items):
            self.position = len(self.filtered_items) - 1
        logger.debug("SelectMenu.navigate :: position = {}, n = {}".format(self.position,n ))
        ### adjust slice ###
        if n < 0:
            if self.position - self.slice_start < 2 and self.slice_start >= 1:
                ### slide slice up ###
                self.slice_start += n
                if self.slice_start < 0:
                    self.slice_start = 0
                self.slice_end = self.slice_start + self.slice_len
                logger.debug("SelectMenu.navigate :: slide slice up to {}-{}".format(self.slice_start,self.slice_end ))
        elif n > 0:
            if self.slice_end - self.position < 2 and self.slice_end < len(self.filtered_items) - 1:
                ### slide slice down ###
                self.slice_end += n
                if self.slice_end > len(self.filtered_items) - 1:
                    self.slice_end = len(self.filtered_items) - 1
                self.slice_start = self.slice_end - self.slice_len
                logger.debug("SelectMenu.navigate :: slide slice down to {}-{}".format(self.slice_start,self.slice_end ))
            
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.update()
        
        while True:
            self.window.clear()
            self.window.refresh()
            curses.doupdate()
            for index,item in enumerate(self.filtered_items):
                if index == self.position:
                    mode = curses.A_STANDOUT
                else:
                    mode = curses.A_NORMAL
                # line = "{}: {}".format(index,item)
                line = "{}".format(item)
                ### only add lines in the slice ###
                # logger.debug("SelectMenu.display :: about to addstr line {}".format(line))
                if self.slice_start <= index <= self.slice_end:
                    # logger.debug("SelectMenu.display :: index in slice {} - {}, executing addstr".format(self.slice_start,self.slice_end))
                    self.window.addstr(2+(index-self.slice_start),2,line,mode)
            
            key = self.window.getch()
            
            if key in [curses.KEY_ENTER,ord("\n")]:
                if self.position == len(self.filtered_items) - 1:
                    break
                else:
                    self.selection.add((self.boxpair_name,self.filtered_items[self.position]))
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
        self.title = title
        self.selection = []
        
    def display(self):
        self.window.clear()
        line = "{} : {}".format(self.title, ",".join(["{}-{}".format(x[0],x[1]) for x in self.selection]))
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
        
class Search(object):
    
    def __init__(self,window,title,stdscr):
        self.window = window
        self.title = title
        self.search_str = ""
        
    def display(self):
        self.window.clear()
        line = "{}: {}".format(self.title,self.search_str)
        self.window.addstr(1,2,line)
        self.window.border()
        self.window.refresh()
        curses.doupdate()
        
    def set(self,search_str):
        self.search_str = search_str
        self.display()
        
    def clear(self):
        self.search_str = ""
        self.display()
        
    def get(self):
        return self.search_str
    
class ShowSummaryMenu(object):
    
    def __init__(self,window,selection,stdscr):
        self.window = window
        self.selection = selection
        self.hostgroup_summary = []
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.display_list = []
        
    def navigate(self,n):
        if n < 0:
            if self.slice_start >= 1:
                self.slice_start += n
                if self.slice_start < 0:
                    self.slice_start = 0
                self.slice_end = self.slice_start + self.slice_len
        elif n > 0:
            if self.slice_end < len(self.display_list) - 1:
                self.slice_end += n
                if self.slice_end > len(self.display_list) - 1:
                    self.slice_end = len(self.display_list) - 1
                self.slice_start = self.slice_end - self.slice_len
        
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.heigth,self.width = self.window.getmaxyx()
        ### fill the list to display ###
        self.display_list = []
        for boxpair_name,hostgroup_name in self.selection.get():
            for box_name in boxpair_dict[boxpair_name]:
                self.display_list.extend(box_dict[box_name].get_hostgroup_noluns(hostgroup_name))
        ### now we know what to display ###
        self.slice_start = 0
        self.slice_len = min(len(self.display_list),self.heigth-6)
        self.slice_end = self.slice_start + self.slice_len
        while True:
            self.window.clear()
            self.window.refresh()
            curses.doupdate()
            for index,item in enumerate(self.display_list):
                if self.slice_start <= index <= self.slice_end:
                    self.window.addstr(2+(index-self.slice_start),2,item,curses.A_NORMAL)
            key = self.window.getch()
            if key in [curses.KEY_ENTER,ord("\n")]:
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
        
class ShowConsistencyMenu(object):
    
    def __init__(self,window,selection,stdscr):
        self.window = window
        self.selection = selection
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.display_list = []
        
    def navigate(self,n):
        if n < 0:
            if self.slice_start >= 1:
                self.slice_start += n
                if self.slice_start < 0:
                    self.slice_start = 0
                self.slice_end = self.slice_start + self.slice_len
        elif n > 0:
            if self.slice_end < len(self.display_list) - 1:
                self.slice_end += n
                if self.slice_end > len(self.display_list) - 1:
                    self.slice_end = len(self.display_list) - 1
                self.slice_start = self.slice_end - self.slice_len
        
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.heigth,self.width = self.window.getmaxyx()
        ### fill the list to display ###
        self.display_list = []
        for boxpair_name,hostgroup_name in self.selection.get():
            for box_name in boxpair_dict[boxpair_name]:
                # self.display_list.extend(box_dict[box_name].get_hostgroup_noluns(hostgroup_name))
                # self.display_list.append("{}-{}: {}".format(boxpair_name,hostgroup_name,"V" if box_dict[box_name].test_hostgroup_consistency(hostgroup_name) else "X"))
                self.display_list.extend(box_dict[box_name].get_hostgroup_consistency(hostgroup_name))
        ### now we know what to display ###
        self.slice_start = 0
        self.slice_len = min(len(self.display_list),self.heigth-6)
        self.slice_end = self.slice_start + self.slice_len
        while True:
            self.window.clear()
            self.window.refresh()
            curses.doupdate()
            for index,item in enumerate(self.display_list):
                if self.slice_start <= index <= self.slice_end:
                    self.window.addstr(2+(index-self.slice_start),2,item,curses.A_NORMAL)
            key = self.window.getch()
            if key in [curses.KEY_ENTER,ord("\n")]:
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
        
class ShowWriteProvisionMenu(object):
    
    def __init__(self,window,selection,stdscr):
        self.window = window
        self.selection = selection
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.window.addstr(1,2,"Write provisioning out to file for the selected HOSTGROUPs ? (Y/n)")
        key = self.window.getch()
        if key in [curses.KEY_ENTER,ord("\n"),ord("Y"),ord("y")]:
            ### write out the ldevs to file ###
            for boxpair_name,hostgroup_name in self.selection.get():
                for box_name in boxpair_dict[boxpair_name]:
                    if box_dict[box_name].test_hostgroup_exists(hostgroup_name):
                        sf = "/tmp/{}_{}.prov".format(box_name,hostgroup_name)
                        with open(sf,"wt") as sfh:
                            box_dict[box_name].print_provisioning(hostgroup_name,sfh)
            self.window.addstr(2,2,"Written..")
        else:
            self.window.addstr(2,2,"Cancelled..")
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        
####################################################################################################
### MAIN
####################################################################################################
def main(stdscr):
    ### clear screen ###
    stdscr.clear()
    
    ### define title_win ###
    title_win = stdscr.subwin(3,curses.COLS,0,0)
    title_win.addstr(1,2,"HPE P9500 TO XP7 MIGRATION PRE-CHECK")
    title_win.border()
    
    ### define search_win ###
    search_win = stdscr.subwin(3,curses.COLS,curses.LINES-6,0)
    search = Search(search_win,"Display HOSTGROUPS matching this SEARCH expression",stdscr)
    search.display()
    
    ### define selection_win ###
    select_win = stdscr.subwin(3,curses.COLS,curses.LINES-3,0)
    selection = Selection(select_win,"SELECTED HOSTGROUP(s)",stdscr)
    selection.display()
    
    ### define menu_win ###
    menu_win = stdscr.subwin(curses.LINES-9,curses.COLS,3,0)
    # menu_win.border()
    
    main_menu_items = []
    for boxpair_name in sorted(boxpair_dict.keys()):
        hostgroup_name_set = set()
        for box_name in boxpair_dict[boxpair_name]:
            hostgroup_name_set = hostgroup_name_set.union([x for x in box_dict[box_name].get_hostgroups() if not re.match(".*-G00$",x)])
        hostgroup_name_list = list(sorted(hostgroup_name_set))
        sel_menu_item = SelectMenu(menu_win,hostgroup_name_list,boxpair_name,selection,search,stdscr)
        main_menu_items.append(("Select HOSTGROUP from {} boxpair".format(boxpair_name),sel_menu_item.display))
    
    input_search = InputMenu(menu_win,"Specify new search string",search,stdscr)
    main_menu_items.append(("Set   SEARCH string",input_search.display))
    main_menu_items.append(("Clear SEARCH string",search.clear))
    
    hostgroup_summary = ShowSummaryMenu(menu_win,selection,stdscr)
    main_menu_items.append(("Show HOSTGROUPs summary",hostgroup_summary.display))
    hostgroup_consistency = ShowConsistencyMenu(menu_win,selection,stdscr)
    main_menu_items.append(("Show HOSTGROUPs consistency check results",hostgroup_consistency.display))
    main_menu_items.append(("Clear HOSTGROUP selection",selection.clear))
    write_prov = ShowWriteProvisionMenu(menu_win,selection,stdscr)
    main_menu_items.append(("Write provisioning to file",write_prov.display))
    
    main_menu = Menu(menu_win,main_menu_items,stdscr)
    main_menu.display()
    
    ### refresh & wait ###
    stdscr.refresh()
    stdscr.getkey()
    
####################
### parse config ###
####################
configfile = "xpmig.ini"
cfg = ConfigParser()
cfg.read(configfile)
    
for mandatory_section in ("boxpair","serialnbr","instance","site","collect"):
    if not cfg.has_section(mandatory_section):
        sys.stderr("{} section missing in config file {}, exiting..".format(mandatory_section,configfile))
        sys.exit(1)

for name,value in cfg.items("boxpair"):
    boxpair_dict[name.upper()] = value.split(",")
    
for name,value in cfg.items("serialnbr"):
    serialnbr_dict[name.upper()] = int(value)
    
for name,value in cfg.items("instance"):
    instance_dict[name.upper()] = int(value)
    
for name,value in cfg.items("site"):
    site_dict[name.upper()] = value
    
for name,value in cfg.items("collect"):
    collectfile_dict[name.upper()] = value
    
try:
    loglevel = cfg.getint("log","level")
except:
    loglevel = 30
    
try:
    logfile = cfg.get("log","file")
except:
    logfile = "/tmp/xpmig_precheck.log"
    
try:
    logsize = cfg.getint("log","maxsize")
except:
    logsize = 100000000
    
try:
    logversions = cfg.getint("log","maxversions")
except:
    logversions = 5
    
#####################
### start logging ###
#####################
logger = logging.getLogger("curses")
logger.setLevel(loglevel)
fh = logging.handlers.RotatingFileHandler(logfile,maxBytes=logsize,backupCount=logversions)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s","%Y/%m/%d-%H:%M:%S")
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info("#" * linelen)
logger.info("XPMIG PRECHECK started")
logger.info("#" * linelen)

logger.info("Configuration settings :")
logger.info("BOXPAIR :")
logger.info(boxpair_dict)
logger.info("SERIAL NBRs:")
logger.info(serialnbr_dict)
logger.info("INSTANCE NBRs:")
logger.info(instance_dict)
logger.info("SITE NBRs:")
logger.info(site_dict)
logger.info("COLLECT FILEs:")
logger.info(collectfile_dict)

#########################
### instantiate boxes ###
#########################
for box_name in collectfile_dict:
    
    collect_file = collectfile_dict[box_name]
    
    if box_name in instance_dict:
        instance_nbr = instance_dict[box_name]
    else:
        err_msg = "No HORCM instance nbr defined for box {}, exiting..".format(box_name)
        logger.error(err_msg)
        sys.stderr(err_msg + "\n")
        sys.exit(1)
        
    if box_name in serialnbr_dict:
        serial_nbr = serialnbr_dict[box_name]
    else:
        err_msg = "No serial nbr defined for box {}, exiting..".format(box_name)
        logger.error(err_msg)
        sys.stderr(err_msg + "\n")
        sys.exit(1)
        
    if box_name in site_dict:
        site = site_dict[box_name]
    else:
        err_msg = "No site defined for box {}, exiting..".format(box_name)
        logger.error(err_msg)
        sys.stderr(err_msg + "\n")
        sys.exit(1)
        
    box_dict[box_name] = xp7.XP7(box_name,instance_nbr,serial_nbr,site,collect_file)
    logger.info("XP7 object created for box {} :".format(box_name))
    logger.info(box_dict[box_name])
    
#####################
### start menu    ###
#####################
curses.wrapper(main)

logger.info("#" * linelen)
logger.info("XPMIG PRECHECK ended")
logger.info("#" * linelen)