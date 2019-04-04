"""
    Purpose
        The purpose of the loggingWrapper module is to create an easy way to use the native logging module from python distribution 
        in order to provide logging functionality to other modules and scripts.

    Description
        It contains a simple wrapper for the logging module, exposing a return_logging method.

    Dependencies 
        logging, os, shutil, datetime, collections.
"""

import logging
import os
import shutil
import datetime
import collections
import sys

def return_logging(logParameters):
    """
        Purpose
            Parse the parameters dictionary and return a class with the information.
        Description
            The method receives the dictionary and use it to initialize the logging system.
            ConfigParser object. This object is then iterated and populates a 
            dictionary.
    
        Parameter
            logParameters - dictionary with the parameters.

        Returns
            logging.logger object configured with the values provided in the dictionary.

        logParameters dictionary
            The dictionary have the following attributes: 
    
            * Folder: name of the folder that will hold the log files.
            * ArchiveFolder: name of the folder that will hold the archive log files.
            * FileNameFormat: name of the log file. It can use formatters to generate dynamic names (%Y, %M, ...).
            * FileNameFunction: the function used to dynamize the name of the log file.
            * LineFormat: structure of the log line. Example: %(asctime)s - %(levelname)s:%(message)s.
            * Level: log level of the log: DEBUG, WARNING, INFO, ...
            * GenerateArchive: indicate if the logger will generate archive or not: True/False.
            * FilesToKeep: Number of archive files to keep.
            * PrintToConsole: if should also print INFO messages to console

    """
    #Check for log folder existence. If it does not exist, create it
    if not os.path.exists(logParameters['Folder']):
        os.makedirs(logParameters['Folder'],mode=0o777)

    if eval(logParameters['GenerateArchive']):
        #Check for archive log folder existence. If it does not exist, create it
        if not os.path.exists(logParameters['ArchiveFolder']):
            os.makedirs(logParameters['ArchiveFolder'],mode=0o777)

        #Archiving log files
        for files in os.listdir(logParameters['Folder']):
            if os.path.isfile(os.path.join(logParameters['Folder'],files)) and not os.path.exists(os.path.join(logParameters['ArchiveFolder'],files)):
                shutil.move(os.path.join(logParameters['Folder'],files),logParameters['ArchiveFolder'])
            else:
                if not os.path.isdir(os.path.join(logParameters['Folder'],files)):
                    os.remove(os.path.join(logParameters['Folder'],files))
        
        #Clean up archive folder according to the number of files to keep
        files = os.listdir(logParameters['ArchiveFolder'])
        if len(files) > eval(logParameters['FilesToKeep']):
            fileDict = {}
            for item in files:
                fileDict[os.stat(os.path.join(logParameters['ArchiveFolder'],item)).st_mtime] = os.path.join(logParameters['ArchiveFolder'],item)
            fileDictOrder = collections.OrderedDict(sorted(fileDict.items()))
            itemIndex = 0
            for key, item in fileDictOrder.items():
                if itemIndex < eval(logParameters['FilesToKeep']):
                   os.remove(fileDictOrder[key])
                   itemIndex = itemIndex + 1
    else:
        pass

    #Initializing the log system
    logging.basicConfig(filename=logParameters['FileNameFormat'].format(eval(logParameters['FileNameFunction'])), filemode="w", format=logParameters['LineFormat'], level=getattr(logging, logParameters['Level']))

    ret_log = logging.getLogger()

    if eval(logParameters['PrintToConsole']):
        not_created = True
        for item in ret_log.handlers:
            if item.get_name() == "console":
                not_created = False
                break

        if not_created:
            console2 = logging.StreamHandler(sys.stdout)
            console2.set_name('console')
            console2.setLevel(logging.INFO)
            ret_log.addHandler(console2)

    return ret_log
