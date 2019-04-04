"""
	Purpose
		The purpose of the argParseWrapper module is to create an easy way to use the native argparse module from python distribution 
		in order to parse command line arguments.

	Description
		It contains a simple wrapper class for the argparse.Action class, which adds the action attribute and a return_args method
		that will return the command line arguments and options parsed and ready to be used.

	Dependencies 
		argparse, labio.configWrapper.
"""

import argparse

#---------------------------------------------------------------------------------------
# [history]
# [15/03/2014 - walter.paixao-cortes] - First version
# [19/03/2014 - walter.paixao-cortes] - Adding comments to generate the documentation.
#---------------------------------------------------------------------------------------
class CustomAction(argparse.Action):
	"""
		Wrapper class for argparse.Action class.
		Adds the action attribute to the object, which is missing from the class.
	"""

	action = None
	"""The action attribute."""

#---------------------------------------------------------------------------------------
# [history]
# [15/03/2014 - walter.paixao-cortes] - First version
# [19/03/2014 - walter.paixao-cortes] - Adding comments to generate the documentation.
#---------------------------------------------------------------------------------------
def return_args(arguments):
	"""
		Purpose
			Parse the arguments from command line, based on a json dictionary.
		Description
			The method receives and iterates through the arguments dictionary, 
			creating an instance of :class:`labio.argParseWrapper.CustomAction` for
			each argument, that will be added to the parser collection.
	
		Parameter
			arguments - a dictionary of json objects describing the options.

		Returns
			Dynamic class with attributes as the keys of each json object in dictionary
			and the values captured from the command line as values.

		Json structure
			The json structure that represents each argument is as follows: 
			::
				{
				 short:   string - Represents the short version of an optional parameter (e.g. -f).
				                   The string "None" is used when it is an argument, not an optional parameter. 

				 long:    string - Represents the short version of an optional parameter (e.g. -file).
				                   The string "None" is used when it is an argument, not an optional parameter.

				 dest:    string - the attribute that will receive the value of the optional parameter.

				 help:    string - The explanation that will be displayed for this optional parameter 
				                   when the command line is executed with the ``--help`` option.

				 metavar: string - The explanation that will be displayed for this argument
				                   when the command line is executed with the ``--help`` option.

				 type:    string - The type of data for this optional parameter or argument (str, int, ...).

				 action:  string - The action that will be executed. See more detail in the argparse documentation.

				 nargs:   string - The number of arguments that an optional parameter should have. 
				                   ? means 0 or more
				                   1..n means the number of arguments

				 default: string - The default value when the optional parameter does not have a value set.

				 const:   string - The constant value when the optional parameter does not have a value set.

				 choices: list   - The choices that are valid for an optional  argument. 
				}

	"""
	#Initializing variables
	optItem = None
	isOptionCorrect = False
	parser = argparse.ArgumentParser()
	
	#iterate through the dictionary, filling an instance of CustomAction and adding to the parser
	for item in arguments:
		if 'short' in arguments[item].keys() and 'long' in arguments[item].keys() and 'dest' in arguments[item].keys():
			optItem = CustomAction([arguments[item]['short'],arguments[item]['long']],dest=arguments[item]['dest'])
			isOptionCorrect = True
	
		if 'dest' in arguments[item].keys() and isOptionCorrect:
			optItem.dest = arguments[item]['dest']
	
		if 'action' in arguments[item].keys() and isOptionCorrect:
			optItem.action = arguments[item]['action']
	
		if 'type' in arguments[item].keys() and isOptionCorrect:
			optItem.type = eval(arguments[item]['type'])
	
		if 'nargs' in arguments[item].keys() and isOptionCorrect:
			optItem.nargs = arguments[item]['nargs']
		else:
			optItem.nargs='?'
	
		if 'help' in arguments[item].keys() and isOptionCorrect:
			optItem.help = arguments[item]['help']
	
		if 'metavar' in arguments[item].keys() and isOptionCorrect:
			optItem.metavar = arguments[item]['metavar']
	
		if 'default' in arguments[item].keys() and isOptionCorrect:
			if optItem.type != str:
				optItem.default = eval(arguments[item]['default'])
			else:
				optItem.default = arguments[item]['default']
	
		if 'const' in arguments[item].keys() and isOptionCorrect:
			if optItem.type != str:
				optItem.const = eval(arguments[item]['const'])
			else:
				optItem.default = arguments[item]['const']
	
		if 'choices' in arguments[item].keys() and isOptionCorrect:
			optItem.choices = eval(arguments[item]['choices'])
	
		#Add to the parser with different parameters depending if it is an argument or optional parameter
		if optItem.option_strings[0] == u'None':
			parser.add_argument(optItem.metavar, action=optItem.action, type=optItem.type, nargs=optItem.nargs, help=optItem.help, metavar=optItem.metavar, default=optItem.default, choices=optItem.choices)
		else:	
			if optItem.action is None:
				parser.add_argument(optItem.option_strings[0],optItem.option_strings[1], dest=optItem.dest, action=optItem.action, type=optItem.type, nargs=optItem.nargs, help=optItem.help, metavar=optItem.metavar, default=optItem.default, choices=optItem.choices)
			else:
				parser.add_argument(optItem.option_strings[0],optItem.option_strings[1], dest=optItem.dest, action=optItem.action, help=optItem.help, default=optItem.default)
	
	#Parse the arguments coming from command line and returns a dynamic class 
	#with the keys of the json objects as attributes.
	options = parser.parse_args()
	
	return options
