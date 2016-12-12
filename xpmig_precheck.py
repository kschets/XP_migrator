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
    2.0 Consistency check update
    2.1 Add xpinfo file processing 

CONFIG : xpmig.ini

LOG : xpmig_precheck.log

TODO :
    add generate temporary horcm file and daemon to pairdisplay & check on status 

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
import os
import os.path
import csv
import string
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
        self.heigth,self.width = self.window.getmaxyx()
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
        if line >= self.width:
            line = line[:self.width-1]
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
        
class Search(object):
    
    def __init__(self,window,title,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.title = title
        self.search_str = ""
        
    def display(self):
        self.window.clear()
        line = "{}: {}".format(self.title,self.search_str)
        if len(line) >= self.width:
            line = line[:self.width-1]
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
    
class Consistent(object):
    
    def __init__(self,window,title,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.title = title
        self.consistent = []
        
    def display(self):
        self.window.clear()
        line = "{}: {}".format(self.title,",".join(["{}-{}".format(x[0],x[1]) for x in self.consistent]))
        if len(line) >= self.width:
            line = line[:self.width-1]
        self.window.addstr(1,2,line)
        self.window.border()
        self.window.refresh()
        curses.doupdate()
        
    def add(self,item):
        current_set = set(self.consistent)
        current_set.add(item)
        self.consistent = list(sorted(current_set))
        self.display()
        
    def clear(self):
        del self.consistent[:]
        self.display()
        
    def get(self):
        return self.consistent
    
class ShowSummaryMenu(object):
    
    def __init__(self,window,selection,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
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
        for box_name,hostgroup_name in self.selection.get():
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
                if len(item) >= self.width:
                    item = item[:self.width-1]
                if self.slice_start <= index <= self.slice_end:
                    self.window.addstr(1+(index-self.slice_start),2,item,curses.A_NORMAL)
            key = self.window.getch()
            if key in [curses.KEY_ENTER,ord("\n"),ord("B"),ord("b")]:
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
    
    def __init__(self,window,selection,consistent,stdscr):
        self.window = window
        self.selection = selection
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.display_list = []
        self.consistent = consistent
        
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
        for box_name,hostgroup_name in self.selection.get():
            if box_dict[box_name].test_hostgroup_exists(hostgroup_name):
                ### TODO: add CA check ###
                result,report = box_dict[box_name].get_hostgroup_consistency(hostgroup_name)
                self.display_list.extend(report)
                if result:
                    self.consistent.add((box_name,hostgroup_name))
                    logger.info("{}-{} added to consistent hostgroup list during consistency check".format(box_name,hostgroup_name))
                else:
                    logger.error("{}-{} not added to consistent hostgroup list during consistency check".format(box_name,hostgroup_name))
            else:
                logger.debug("{}-{} does not exists".format(box_name,hostgroup_name))
        ### now we know what to display ###
        self.slice_start = 0
        self.slice_len = min(len(self.display_list),self.heigth-6)
        self.slice_end = self.slice_start + self.slice_len
        while True:
            self.window.clear()
            self.window.refresh()
            curses.doupdate()
            for index,item in enumerate(self.display_list):
                if len(item) >= self.width:
                    item = item[:self.width-1]
                if self.slice_start <= index <= self.slice_end:
                    self.window.addstr(1+(index-self.slice_start),2,item,curses.A_NORMAL)
            key = self.window.getch()
            if key in [curses.KEY_ENTER,ord("\n"),ord("B"),ord("b")]:
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
    
    def __init__(self,window,consistent,map_dir,stdscr):
        self.window = window
        self.consistent = consistent
        self.map_dir = map_dir
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        self.window.addstr(1,2,"Write provisioning out to file for the consistent HOSTGROUPs ? (Y/n)")
        key = self.window.getch()
        if key in [curses.KEY_ENTER,ord("\n"),ord("Y"),ord("y")]:
            ### write out the ldevs to file ###
            for box_name,hostgroup_name in self.consistent.get():
                if box_dict[box_name].test_hostgroup_exists(hostgroup_name):
                    sf = os.path.join(self.map_dir,"{}_{}.prov".format(box_name,hostgroup_name))
                    with open(sf,"wt") as sfh:
                        box_dict[box_name].print_provisioning(hostgroup_name,sfh)
            self.window.addstr(2,2,"Written..")
        else:
            self.window.addstr(2,2,"Cancelled..")
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        
class Select_Menu(object):
    
    def __init__(self,window,items,selection,search,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        ### items is a dict ###
        self.items = items
        self.filtered_items = copy.copy(self.items.keys())
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
        
    def update(self):
        """
        update the selection items list to match the new search criteria
        """
        if self.search.get() != "":
            logger.debug("Select_Menu.update :: update items to match search str {}".format(self.search.get()))
            self.filtered_items = [x for x in self.items.keys() if re.search(self.search.get(),x,flags=re.IGNORECASE)]
        else:
            logger.debug("Select_Menu.update :: update items to match search all")
            self.filtered_items = copy.copy(self.items.keys())
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
        logger.debug("Select_Menu.navigate :: position = {}, n = {}".format(self.position,n ))
        ### adjust slice ###
        if n < 0:
            if self.position - self.slice_start < 2 and self.slice_start >= 1:
                ### slide slice up ###
                self.slice_start += n
                if self.slice_start < 0:
                    self.slice_start = 0
                self.slice_end = self.slice_start + self.slice_len
                logger.debug("Select_Menu.navigate :: slide slice up to {}-{}".format(self.slice_start,self.slice_end ))
        elif n > 0:
            if self.slice_end - self.position < 2 and self.slice_end < len(self.filtered_items) - 1:
                ### slide slice down ###
                self.slice_end += n
                if self.slice_end > len(self.filtered_items) - 1:
                    self.slice_end = len(self.filtered_items) - 1
                self.slice_start = self.slice_end - self.slice_len
                logger.debug("Select_Menu.navigate :: slide slice down to {}-{}".format(self.slice_start,self.slice_end ))
            
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
                if len(line) >= self.width:
                    line = line[:self.width-1]
                ### only add lines in the slice ###
                # logger.debug("SelectMenu.display :: about to addstr line {}".format(line))
                if self.slice_start <= index <= self.slice_end:
                    # logger.debug("SelectMenu.display :: index in slice {} - {}, executing addstr".format(self.slice_start,self.slice_end))
                    self.window.addstr(1+(index-self.slice_start),2,line,mode)
            
            key = self.window.getch()
            if key in [ord("b"),ord("B")]:
                break
            elif key in [curses.KEY_ENTER,ord("\n")]:
                if self.position == len(self.filtered_items) - 1:
                    break
                else:
                    # self.items = {"select_str":[(boxpair_name,hostgroup_name),...]}
                    # self.selection.add(self.items[self.filtered_items[self.position]])
                    for add_item in self.items[self.filtered_items[self.position]]:
                        self.selection.add(add_item)
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
        
class Select_XPinfo(object):
    
    def __init__(self,window,selection,xpinfo_dir,stdscr):
        self.window = window
        self.heigth,self.width = self.window.getmaxyx()
        self.xpinfo_file_list =[]
        self.slice_start = 0
        self.slice_len = 0
        self.slice_end = 0
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        self.position = 0
        self.xpinfo_dir = xpinfo_dir
        self.selection = selection
        
    def update(self):
        """
        update the list of xpinfo files present
        """
        if os.path.exists(self.xpinfo_dir):
            del(self.xpinfo_file_list[:])
            self.xpinfo_file_list = [f for f in os.listdir(self.xpinfo_dir) if os.path.isfile("{}/{}".format(self.xpinfo_dir,f)) and re.match(".+\.xpinfo$",f,flags=re.IGNORECASE)]
            self.xpinfo_file_list.append("exit")
            self.slice_len = min(len(self.xpinfo_file_list)-1, self.heigth - 6)
            self.slice_start = 0
            self.slice_end = self.slice_start + self.slice_len
            self.position = 0
        
    def navigate(self,n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.xpinfo_file_list):
            self.position = len(self.xpinfo_file_list) - 1
        if n < 0:
            if self.position - self.slice_start < 2 and self.slice_start >= 1:
                ### slide slice up ###
                self.slice_start += n
                if self.slice_start < 0:
                    self.slice_start = 0
                self.slice_end = self.slice_start + self.slice_len
        elif n > 0:
            if self.slice_end - self.position < 2 and self.slice_end < len(self.xpinfo_file_list) - 1:
                ### slide slice down ###
                self.slice_end += n
                if self.slice_end > len(self.xpinfo_file_list) - 1:
                    self.slice_end = len(self.xpinfo_file_list) - 1
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
            ### show the list of xpinfo files ###
            for index,item in enumerate(self.xpinfo_file_list):
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
                if self.position == len(self.xpinfo_file_list) - 1:
                    break
                else:
                    logger.debug("XPINFO: start processing {}".format(self.xpinfo_file_list[self.position]))
                    serial_nbr_set = set(serialnbr_dict.values())
                    ldev_dict = {}
                    hostgroup_dict = {}
                    for serial_nbr in serial_nbr_set:
                        ldev_dict[serial_nbr] = set()
                    ### process the selected xpinfo file ###
                    with open("{}/{}".format(self.xpinfo_dir,self.xpinfo_file_list[self.position]),"rt") as f:
                        xpinfo_file_reader = csv.reader(f,delimiter=",",quotechar="'")
                        for row in xpinfo_file_reader:
                            if len(row) > 8:
                                hostname = row[0]
                                device_name = row[1]
                                ldev_nbr = xp7.standard_format_ldev(row[5])
                                serial_nbr = int(row[8])
                                logger.debug("XPINFO: got S/N {} LDEV {} from xpinfo file".format(serial_nbr,ldev_nbr))
                                if serial_nbr in ldev_dict:
                                    ldev_dict[serial_nbr].add(ldev_nbr)
                                    logger.debug("XPINFO: known S/N, added to ldev_dict, now at {} elements".format(len(ldev_dict[serial_nbr])))
                            else:
                                logger.error("XPINFO: line too short to be valid, skipping {}".format(row))
                    ### translate ldev to hostgroup ###
                    for serial_nbr in ldev_dict:
                        box_name = serial_to_name_dict[serial_nbr]
                        if not box_name in hostgroup_dict:
                            hostgroup_dict[box_name] = set()
                        for ldev_nbr in ldev_dict[serial_nbr]:
                            for hostgroup_name in box_dict[box_name].get_ldev_hostgroups(ldev_nbr):
                                hostgroup_dict[box_name].add(hostgroup_name)
                    ### add found hostgroups to the selection ###
                    for box_name in hostgroup_dict:
                        for hostgroup_name in hostgroup_dict[box_name]:
                            logger.debug("XPINFO processing: adding {}-{} to the selection".format(box_name,hostgroup_name))
                            self.selection.add((box_name,hostgroup_name))
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
        
####################################################################################################
### MAIN
####################################################################################################
def main(stdscr):
    ### clear screen ###
    stdscr.clear()
    
    ### check window heigth and width ###
    if curses.COLS < 20 or curses.LINES < 20:
        sys.stderr.write("Window not large enough, exiting ..\n")
        sys.exit(1)
    
    ### define title_win ###
    title_win = stdscr.subwin(3,curses.COLS,0,0)
    title_win.addstr(1,2,"HPE P9500 TO XP7 MIGRATION PRE-CHECK")
    title_win.border()
    
    ### define search_win ###
    search_win = stdscr.subwin(3,curses.COLS,curses.LINES-10,0)
    search = Search(search_win,"Display HOSTGROUPS matching this SEARCH expression",stdscr)
    search.display()
    
    ### define selection_win ###
    select_win = stdscr.subwin(3,curses.COLS,curses.LINES-7,0)
    selection = Selection(select_win,"SELECTED HOSTGROUP(s)",stdscr)
    selection.display()
    
    ### define consistent_win ###
    consistent_win = stdscr.subwin(3,curses.COLS,curses.LINES-4,0)
    consistent = Consistent(consistent_win,"CONSISTENT HOSTGROUP(s)",stdscr)
    consistent.display()
    
    ### define key_win ###
    key_win = stdscr.subwin(1,curses.COLS,curses.LINES-1,0)
    #key_win.clear()
    #key_win.refresh()
    #curses.doupdate()
    key_win.addstr(0,2,"<ARROW-UP or PAGE-UP> SCROLL UP <ARROW-DOWN or PAGE-DOWN> SCROLL DOWN <B> BACK",curses.A_BOLD)
    
    ### define menu_win ###
    menu_win = stdscr.subwin(curses.LINES-13,curses.COLS,3,0)
    # menu_win.border()
    
    main_menu_items = []
    
    input_search = InputMenu(menu_win,"Specify new search string",search,stdscr)
    main_menu_items.append(("Set   SEARCH string",input_search.display))
    main_menu_items.append(("Clear SEARCH string",search.clear))
    
    ### select hostgroups by box ###
    for boxpair_name in sorted(boxpair_dict.keys()):
        select_item_dict = {}
        for box_name in boxpair_dict[boxpair_name]:
            hostgroup_name_list = box_dict[box_name].get_hostgroups()
            for hostgroup_name in hostgroup_name_list:
                if hostgroup_name not in select_item_dict:
                    select_item_dict[hostgroup_name] = set()
                select_item_dict[hostgroup_name].add((box_name,hostgroup_name))
        hg_by_box_menu = Select_Menu(menu_win,select_item_dict,selection,search,stdscr)
        main_menu_items.append(("Select {} HOSTGROUP".format(boxpair_name),hg_by_box_menu.display))
    
    ### select hostgroups by host (hba_wwn) ###
    select_item_dict = {}
    for boxpair_name in sorted(boxpair_dict.keys()):
        for box_name in boxpair_dict[boxpair_name]:
            hostgroup_name_list = box_dict[box_name].get_hostgroups()
            for hostgroup_name in hostgroup_name_list:
                hba_wwn_list = box_dict[box_name].get_hostgroup_hba_wwns(hostgroup_name)
                for hba_wwn in hba_wwn_list:
                    if len(hba_wwn.nickname.split("_")) > 1:
                        sel_item = hba_wwn.nickname.split("_")[0]
                    else:
                        sel_item = hba_wwn.nickname
                    if "{}-{}".format(box_name,sel_item) not in select_item_dict:
                        select_item_dict["{}-{}".format(box_name,sel_item)] = set()
                    select_item_dict["{}-{}".format(box_name,sel_item)].add((box_name,hostgroup_name))
    hg_by_host_menu = Select_Menu(menu_win,select_item_dict,selection,search,stdscr)
    main_menu_items.append(("Select by HOSTNAME",hg_by_host_menu.display))
    
    ### select hostgroups by name ###
    select_item_dict = {}
    for boxpair_name in sorted(boxpair_dict.keys()):
        for box_name in boxpair_dict[boxpair_name]:
            hostgroup_name_list = box_dict[box_name].get_hostgroups()
            for hostgroup_name in hostgroup_name_list:
                if hostgroup_name not in select_item_dict:
                        select_item_dict[hostgroup_name] = set()
                select_item_dict[hostgroup_name].add((box_name,hostgroup_name))
    hg_by_name_menu = Select_Menu(menu_win,select_item_dict,selection,search,stdscr)
    main_menu_items.append(("Select by HOSTGROUP",hg_by_name_menu.display))
    
    ### read XPINFO file ###
    xpinfo_menu = Select_XPinfo(menu_win,selection,xpinfo_dir,stdscr)
    main_menu_items.append(("Read XPINFO file",xpinfo_menu.display))
    
    ### show hostgroup summary menu ###
    hostgroup_summary = ShowSummaryMenu(menu_win,selection,stdscr)
    main_menu_items.append(("Show HOSTGROUPs summary",hostgroup_summary.display))
    
    ### show hostgroup consistency menu ###
    hostgroup_consistency = ShowConsistencyMenu(menu_win,selection,consistent,stdscr)
    main_menu_items.append(("Show HOSTGROUPs consistency check results",hostgroup_consistency.display))
    
    main_menu_items.append(("Clear HOSTGROUP selection",selection.clear))
    main_menu_items.append(("Clear consistent HOSTGROUP",consistent.clear))
    
    write_prov = ShowWriteProvisionMenu(menu_win,consistent,map_dir,stdscr)
    main_menu_items.append(("Write PROVISION file",write_prov.display))
    
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
    
for mandatory_section in ("boxpair","serialnbr","instance","site","collect","dir"):
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
    log_level = cfg.getint("log","level")
except:
    log_level = 30
    
try:
    log_size = cfg.getint("log","maxsize")
except:
    log_size = 100000000
    
try:
    log_versions = cfg.getint("log","maxversions")
except:
    log_versions = 5
    
try:
    log_dir = cfg.get("dir","log")
except:
    sys.stderr.write("log file dir not defined, exiting..\n")
    sys.exit(1)
    
try:
    xpinfo_dir = cfg.get("dir","xpinfo")
except:
    sys.stderr.write("xpinfo file dir not defined, exiting..\n")
    sys.exit(1)
    
try:
    collect_dir = cfg.get("dir","collect")
except:
    sys.stderr.write("collect file dir not defined, exiting..\n")
    sys.exit(1)
    
try:
    map_dir = cfg.get("dir","map")
except:
    sys.stderr.write("map file dir not defined, exiting..\n")
    sys.exit(1)
    
serial_to_name_dict = {}
for box_name,serial_nbr in serialnbr_dict.items():
    serial_to_name_dict[serial_nbr] = box_name
    
#####################
### start logging ###
#####################
logfile = os.path.join(log_dir,"xpmig_precheck.log")
logger = logging.getLogger("xpmig_precheck")
logger.setLevel(log_level)
fh = logging.handlers.RotatingFileHandler(logfile,maxBytes=log_size,backupCount=log_versions)
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
logger.info("XPINFO dir: {}".format(xpinfo_dir))

#########################
### instantiate boxes ###
#########################
for box_name in collectfile_dict:
    
    collect_file = os.path.join(collect_dir,collectfile_dict[box_name])
    
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