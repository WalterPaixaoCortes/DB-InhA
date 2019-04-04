"""
    Purpose
        The purpose of the configWrapper module is to create an easy way to use the native ConfigParser module from python distribution 
        in order to load parameters from configuration file.

    Description
        It contains a simple wrapper for the ConfigParser module, exposing a load_configuration method.

    Dependencies 
        ConfigParser, json.
"""

#Imports used on this module
try:
	import configparser
except:
	import ConfigParser as configparser

import json

#---------------------------------------------------------------------------------------
# [history]
# [13/03/2014 - walter.paixao-cortes] - First version.
# [14/03/2014 - walter.paixao-cortes] - Added attribute args to the dynamic class to re-
#                                       ceive the arguments dictionary.
# [17/03/2014 - walter.paixao-cortes] - Added attribute log to the dynamic class to re-
#                                       ceive the logging parameters.
# [19/03/2014 - walter.paixao-cortes] - Adding comments to generate the documentation.
#---------------------------------------------------------------------------------------
def load_configuration(fileName="app.config"):
    """
        Purpose
            Parse the configuration file and return a class with the information.
        Description
            The method receives the configuration file name and parse it into a
            ConfigParser object. This object is then iterated and populates a 
            dictionary.
    
        Parameter
            fileName - the name of the config file. If not filled, the default is "app.config".

        Returns
            Dynamic class with attributes created from the keys of the dictionary.

        Config file structure
            The config file is a .INI like file with sections and attributes: 
            ::
                [section name]
                parameter = value
                .
                .
                .
                [other section name]
                otherparameter = other value
                otherparameter2 = other value2
                .
                .
                .

        Sections with specific names
            The section names can be pretty much anything, but there are 4 section names that serve to specific purposes:
            
            * [lists] - all parameters that are lists or list of lists or dictionaries shall be declared under this section.
            * [dicts] - all parameters that are lists or list of lists or dictionaries shall be declared under this section.
            * [structures] - all parameters that are lists or list of lists or dictionaries shall be declared under this section.
            * [numbers] - all integer or float items shall be declared under this section.
            * [booleans] - all booleans items shall be declared under this section.
            * [commandline] - all parameters that are related to command line arguments or optional parameters.
            * [logging] - all parameters related to logging configuration.
            * [database] - all parameters related to open a database connection.

    """
    #Initializing dictionaries
    attrs = {}
    args = {}
    log = {}
    database = {}
    
    try:
        configFile = configparser.ConfigParser()
        configFile.optionxform = str
        configFile.read(fileName)

        for section in configFile.sections():
            if section == 'commandline':
                for item in configFile.options(section):
                    args[item] = json.loads(configFile.get(section, item, raw=True))

                attrs['args'] = args
            elif section == 'logging':
                for item in configFile.options(section):
                    log[item] = configFile.get(section, item, raw=True)

                attrs['log'] = log
            elif section == 'database':
                for item in configFile.options(section):
                    database[item] = configFile.get(section, item, raw=True)

                attrs['database'] = database
            else:
                for item in configFile.options(section):
                    if section in ['lists','numbers','dicts','structures','booleans']:
                        attrs[item] = eval(configFile.get(section, item, raw=True))
                    else:
                        attrs[item] = configFile.get(section, item, raw=True)

        isLoaded = True
    except configparser.NoSectionError:
        isLoaded = False
    
    attrs['isLoaded'] = isLoaded

    return type('Config',(), attrs)
