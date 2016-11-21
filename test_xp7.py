#!/usr/bin/python
"""
####################################################################################################

TITLE : ODR provisioning Tool, XPINFO file based

DESCRIPTION : generate provisioning commands for P9500 / XP7 migrations
    First, a list of LDEVs to be migrated is extracted from the xpinfo output provided
    A check/cleanup is done for LDEVs which are known to be migrated already
    Based on the to-be-migrated LDEV list a list of hostgroups to be migrated is compiled
