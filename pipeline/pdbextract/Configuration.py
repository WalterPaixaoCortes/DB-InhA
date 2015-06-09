# -*- coding: utf-8 -*-
import sys
import datetime
import logging

__name__ = "Configuration"

class PDBSynchConfig():
    #Configuration File
    logFolder = 'log/'
    logArchiveFolder = 'log/archive/'
    logFile = logFolder + 'log_{0:%Y%m%d%H%M%S}.log'.format(datetime.datetime.now()) 
    logLineFormat = '%(asctime)s - %(levelname)s:%(message)s'
    logLevel = logging.DEBUG

    extractFilesFolder = 'extract/'

    dbConnectionHost = 'localhost'
    dbConnectionPort = 27017
    dbConnectionCollection = 'dbInhA'

    pdbGetIdURL = 'http://www.rcsb.org/pdb/files/{0}.pdb'
    pdbGetAllIdsURL = 'http://www.rcsb.org/pdb/rest/getCurrent'
    pdbSelectedIds = '1ENY,2H7M,2h7i,2x23'
    #End Configuration File