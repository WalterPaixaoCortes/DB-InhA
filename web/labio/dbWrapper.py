"""
    Purpose
        The purpose of dbWrapper is to make it easy to use the different databases: mysql, sqlite3. It wraps the module with some useful
        methods, like to check if the database is open, if it is a new database, or the last error occurred.

    Description
        It contains a class wrapper around sqlite3 class. The database name is provided through a dictionary containing
        the parameters loaded.

    Dependencies
        cx_Oracle, mysqlclient, sqlite3, traceback
"""

import traceback
try:
    import cx_Oracle
except:
    pass

try:
    import mysql.connector as MySQLdb
    #import MySQLdb
    #import MySQLdb.cursors
except:
    try:
        import mysql.connector as MySQLdb
    except:
        pass

try:
    import sqlite3
except:
    pass

from labio import utils


class dbSQLiteWrapper():
    """
        Purpose
            This is the wrapper class for sqlite3.
        Description
            This class wraps around the most common methods of the sqlite3 module, giving exception treatment support to it.
            It provides methods to open, retrieve data, maintain data and the boolean methods to check if database is open or
            is new.
    """
    __db = None
    __lastError = None
    __config = None

    def __init__(self, configObj):
        """
            This is the class constructor.

            Parameters
                configObj - the configuration dictionary

            Configuration Dictionary
                The configuration dictionary expected is as follows:

                * dbType -> indicates the database type. Valid values are SQLite, MySQL, Oracle, MSSQL, ...
                * dbConnectionString -> indicates the database connection.
                * sqlMetadataTable -> indicates the table to be used to check metadata about the database.

        """
        self.__config = configObj
        self.__createDB(self.__config['dbConnectionString'])

    def isDatabaseNew(self):
        """
            Returns if this database is a new one or not.
            To determine that, we query against the metadata table. If the count returns 0 or 1, this means an empty database.
            If the database is empty, we consider it a new database.

            Returns
                True if the database is empty or False otherwise.
        """
        returnValue = None
        returnValue = self.__returnTableCount()
        return ((returnValue < 1))

    def isDatabaseOpen(self):
        """
            Returns if this database is opened or not.

            Returns
                True if the database is opened or False otherwise.
        """
        return (not self.__db is None)

    def getLastError(self):
        """
            Returns the last error occurred in one of the methods.
        """
        return self.__lastError

    def commit(self):
        """
            Commit the transactions that are pending.

            Returns -1 in case of error or the number of commited rows in the database.
        """
        returnValue = -1
        try:
            self.__db.commit()
            returnValue = self.__db.total_changes
        except sqlite3.DatabaseError as e:
            self.__lastError = traceback.format_exc()
        except sqlite3.DataError as e:
            self.__lastError = traceback.format_exc()
        except sqlite3.Error as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def rollback(self):
        """
            Commit the transactions that are pending.

            Returns -1 in case of error or 0 to indicate that no transactions were commited.
        """
        returnValue = -1
        try:
            self.__db.rollback()
            returnValue = 0
        except sqlite3.DatabaseError as e:
            self.__lastError = traceback.format_exc()
        except sqlite3.DataError as e:
            self.__lastError = traceback.format_exc()
        except sqlite3.Error as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def __createDB(self,dbFile):
        self.__db = None
        try:
            self.__db = sqlite3.connect(dbFile)
        except sqlite3.DatabaseError as e:
            self.__lastError = traceback.format_exc()
        except sqlite3.DataError as e:
            self.__lastError = traceback.format_exc()
        except sqlite3.Error as e:
            self.__lastError = traceback.format_exc()

    def __returnTableCount(self):
        returnValue = None
        try:
            cntCursor = self.getData("select count() from %s where type = 'table' and name not like 'sqlite_%%'" % self.__config['sqlMetadataTable'])
            returnValue = cntCursor.fetchone()[0]
        except Exception as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def getData(self,sqlCommand,args=None):
        """
            Execute a SELECT statement or functions that returns data.
            Returns the cursor or value returned by the command.
        """
        returnData = None
        try:
            if args is not None:
                cursor = self.__db.execute(sqlCommand,args)
            else:
                cursor = self.__db.execute(sqlCommand)
            returnData = cursor
        except sqlite3.DatabaseError as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        except sqlite3.DataError as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        except sqlite3.Error as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def executeCommand(self,sqlCommand,args=None):
        """
            Execute DML (INSERT, UPDATE, DELETE) or DDL statements against the database.
            Returns False in case of error, True otherwise.
        """
        returnData = False
        try:
            x = 0
            if args is not None:
                x = self.__db.execute(sqlCommand,args)
            else:
                x = self.__db.execute(sqlCommand)
            returnData = x
        except sqlite3.DatabaseError as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        except sqlite3.DataError as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        except sqlite3.Error as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def executeCommandList(self,sqlCommand,args=None):
        """
            Execute a list of DML (INSERT, UPDATE, DELETE) or DDL statements against the database.
            Returns False in case of error, True otherwise.
        """
        returnData = 0
        try:
            if args is not None:
                self.__db.executemany(sqlCommand,args)
                returnData = len(args)
            else:
                self.__db.execute(sqlCommand)
                returnData = 1
        except sqlite3.DatabaseError as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        except sqlite3.DataError as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        except sqlite3.Error as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def close(self):
        self.__db.close()


class dbMySQLWrapper():
    """
        Purpose
            This is the wrapper class for sqlite3.
        Description
            This class wraps around the most common methods of the sqlite3 module, giving exception treatment support to it.
            It provides methods to open, retrieve data, maintain data and the boolean methods to check if database is open or
            is new.
    """
    __db = None
    __lastError = None
    __config = None

    def __init__(self, configObj):
        """
            This is the class constructor.

            Parameters
                configObj - the configuration dictionary

            Configuration Dictionary
                The configuration dictionary expected is as follows:

                * dbType -> indicates the database type. Valid values are SQLite, MySQL, Oracle, MSSQL, ...
                * dbConnectionString -> indicates the database connection.
                * sqlMetadataTable -> indicates the table to be used to check metadata about the database.

        """
        self.__config = configObj
        self.__createDB()

    def isDatabaseNew(self):
        """
            Returns if this database is a new one or not.
            To determine that, we query against the metadata table. If the count returns 0 or 1, this means an empty database.
            If the database is empty, we consider it a new database.

            Returns
                True if the database is empty or False otherwise.
        """
        returnValue = None
        returnValue = self.__returnTableCount()
        return ((returnValue < 1))

    def isDatabaseOpen(self):
        """
            Returns if this database is opened or not.

            Returns
                True if the database is opened or False otherwise.
        """
        return (not self.__db is None)

    def getLastError(self):
        """
            Returns the last error occurred in one of the methods.
        """
        return self.__lastError

    def commit(self):
        """
            Commit the transactions that are pending.

            Returns -1 in case of error or the number of commited rows in the database.
        """
        returnValue = -1
        try:
            self.__db.commit()
            returnValue = 0
        except MySQLdb.Error as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def rollback(self):
        """
            Commit the transactions that are pending.

            Returns -1 in case of error or 0 to indicate that no transactions were commited.
        """
        returnValue = -1
        try:
            self.__db.rollback()
            returnValue = 0
        except MySQLdb.Error as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def __createDB(self):
        self.__db = None
        try:
            try:
                self.__db = MySQLdb.connect (host = self.__config["MySQLServer"], user = self.__config["MySQLUser"], passwd=utils.decrypt(self.__config["MySQLPassword"]), db = self.__config["MySQLDB"],cursorclass=MySQLdb.cursors.DictCursor)
            except:
                self.__db = MySQLdb.connect(host = self.__config["MySQLServer"], user=self.__config["MySQLUser"], passwd=self.__config["MySQLPassword"], db=self.__config["MySQLDB"])
        except MySQLdb.Error as e:
            print(traceback.format_exc())
            self.__lastError = traceback.format_exc()

    def __returnTableCount(self):
        returnValue = None
        try:
            cntCursor = self.getData("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '%s';" % self.__config['MySQLDB'])
            returnValue = cntCursor.fetchone()[0]
        except Exception as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def getData(self,sqlCommand,args=None):
        """
            Execute a SELECT statement or functions that returns data.
            Returns the cursor or value returned by the command.
        """
        returnData = None
        try:
            cursor = self.__db.cursor(dictionary=True)
            if args is not None:
                result = cursor.execute(sqlCommand,[args])
            else:
                result = cursor.execute(sqlCommand)
            returnData = cursor
        except MySQLdb.Error as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def executeCommand(self,sqlCommand,args=None):
        """
            Execute DML (INSERT, UPDATE, DELETE) or DDL statements against the database.
            Returns False in case of error, True otherwise.
        """
        returnData = False
        try:
            cursor = self.__db.cursor()
            if args is not None:
                cursor.execute(sqlCommand,args)
            else:
                cursor.execute(sqlCommand)
            returnData = True
        except MySQLdb.Error as e:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def close(self):
        self.__db.close()

class dbOracleWrapper():
    """
        Purpose
            This is the wrapper class for sqlite3.
        Description
            This class wraps around the most common methods of the sqlite3 module, giving exception treatment support to it.
            It provides methods to open, retrieve data, maintain data and the boolean methods to check if database is open or
            is new.
    """
    __db = None
    __lastError = None
    __config = None

    def __init__(self, configObj):
        """
            This is the class constructor.

            Parameters
                configObj - the configuration dictionary

            Configuration Dictionary
                The configuration dictionary expected is as follows:

                * dbType -> indicates the database type. Valid values are SQLite, MySQL, Oracle, MSSQL, ...
                * dbConnectionString -> indicates the database connection.
                * sqlMetadataTable -> indicates the table to be used to check metadata about the database.

        """
        self.__config = configObj
        self.__createDB()

    def isDatabaseNew(self):
        """
            Returns if this database is a new one or not.
            To determine that, we query against the metadata table. If the count returns 0 or 1, this means an empty database.
            If the database is empty, we consider it a new database.

            Returns
                True if the database is empty or False otherwise.
        """
        returnValue = None
        returnValue = self.__returnTableCount()
        return ((returnValue < 1))

    def isDatabaseOpen(self):
        """
            Returns if this database is opened or not.

            Returns
                True if the database is opened or False otherwise.
        """
        return (not self.__db is None)

    def getLastError(self):
        """
            Returns the last error occurred in one of the methods.
        """
        return self.__lastError

    def commit(self):
        """
            Commit the transactions that are pending.

            Returns -1 in case of error or the number of commited rows in the database.
        """
        returnValue = -1
        try:
            self.__db.commit()
            returnValue = 0
        except:
            self.__lastError = traceback.format_exc()
        return returnValue

    def rollback(self):
        """
            Commit the transactions that are pending.

            Returns -1 in case of error or 0 to indicate that no transactions were commited.
        """
        returnValue = -1
        try:
            self.__db.rollback()
            returnValue = 0
        except:
            self.__lastError = traceback.format_exc()
        return returnValue

    def __createDB(self):
        self.__db = None
        try:
            self.__db = cx_Oracle.connect ("{0}/{1}@{2}".format(self.__config["OracleUser"],self.__config["OraclePwd"],self.__config["OracleServer"]))
        except:
            self.__lastError = traceback.format_exc()
            print(self.__lastError)

    def __returnTableCount(self):
        returnValue = None
        try:
            cntCursor = self.getData("SELECT COUNT(*) FROM all_tables WHERE owner = '%s'" % self.__config['OracleSchema'])
            returnValue = cntCursor.fetchone()[0]
        except Exception as e:
            self.__lastError = traceback.format_exc()
        return returnValue

    def getData(self,sqlCommand,args=None):
        """
            Execute a SELECT statement or functions that returns data.
            Returns the cursor or value returned by the command.
        """
        returnData = None
        try:
            cursor = self.__db.cursor()
            if args is not None:
                result = cursor.execute(sqlCommand,[args])
            else:
                result = cursor.execute(sqlCommand)
            returnData = cursor
        except:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def executeCommand(self,sqlCommand,args=None):
        """
            Execute DML (INSERT, UPDATE, DELETE) or DDL statements against the database.
            Returns False in case of error, True otherwise.
        """
        returnData = False
        try:
            cursor = self.__db.cursor()

            if args is not None:
                cursor.execute(sqlCommand,args)
            else:
                cursor.execute(sqlCommand)
            returnData = True
        except:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData

    def executeProc(self,sqlCommand,args=None):
        """
            Execute PROCEDURES OR FUNCTIONS against the database.
            Returns False in case of error, True otherwise.
        """
        returnData = False
        try:
            cursor = self.__db.cursor()
            cursor.callproc(sqlCommand)

            returnData = True
        except:
            self.__lastError = traceback.format_exc()
            raise Exception(self.__lastError)
        return returnData


    def close(self):
        self.__db.close()

    def getCursor(self):
        return self.__db.cursor()

class dbGenericWrapper():
    __db = None
    __lastError = None

    def __init__(self, configObj):
        """
            This is the class constructor.

            Parameters
                configObj - the configuration dictionary

            Configuration Dictionary
                The configuration dictionary expected is as follows:

        """
        self.__config = configObj
        if self.__config['dbType'] == 'Oracle':
            try:
                import cx_Oracle
                self.__db = dbOracleWrapper(self.__config)
            except:
                __lastError = "Oracle module is missing. Please install cx_Oracle 5.2 module."
        if self.__config['dbType'] == 'MySQL':
            try:
                try:
                    import MySQLdb
                    import MySQLdb.cursors
                except:
                    try:
                        import mysql.connector as MySQLdb
                    except:
                        pass
                print(traceback.format_exc())
                self.__db = dbMySQLWrapper(self.__config)
            except:
                print(traceback.format_exc())
                __lastError = "MySQL module is missing. Please install with: pip install mysqlclient."
        if self.__config['dbType'] == 'SQLite':
            try:
                import sqlite3
                self.__db = dbSQLiteWrapper(self.__config)
            except:
                __lastError = "SQL Lite driver is not available. Please install"

    def getDB(self):
        return self.__db

