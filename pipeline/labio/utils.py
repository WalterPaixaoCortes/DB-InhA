import base64
import json
import decimal
import random
import datetime


# ---------------------------------------------------------------------------------------------------------------------
def returnData(fieldName,data, default_value):
    if fieldName in data.keys():
        return data[fieldName]
    else:
        return default_value


# ---------------------------------------------------------------------------------------------------------------------
def isStringFound(string, content):
    return (string.lower() in content.lower())


# ---------------------------------------------------------------------------------------------------------------------
def encrypt(value):
    return_value = base64.encodebytes(value.encode())
    return_value = return_value[2:len(return_value)-1] + return_value[0:2] + return_value[len(return_value)-1:]
    return return_value


# ---------------------------------------------------------------------------------------------------------------------
def decrypt(value):
    try:
        encoded = value.encode()
    except:
        encoded = value
    return_value = encoded[len(encoded)-3:].replace(b'\n',b'') + encoded[0:len(encoded)-3] + encoded[len(encoded)-1:]
    return_value = base64.decodebytes(return_value)
    return return_value.decode()


# ---------------------------------------------------------------------------------------------------------------------
def find_item(src_list, val):
    try:
        idx = src_list.index(val)
        return True
    except:
        try:
            idx = src_list.index(''.join(["`",val,"`"]))
            return True
        except:
            return False


# ---------------------------------------------------------------------------------------------------------------------
def shift_text(shift, val, name, decimals):
    strs = 'abcdefghijklmnopqrstuvwxyz'
    nbrs = '0123456789'
    data = []
    if val is not None:
        if isinstance(val, decimal.Decimal) or isinstance(val, float):
            if '_wid' in name or '_id' in name:
                data = val
                output = str(data)
            else:
                if isinstance(val, float):
                    mult = round(random.random(),3)
                else:
                    mult = round(decimal.Decimal(random.random()),3)
                data = val * mult 
                output = str(round(data, int(decimals)))
        elif isinstance(val, datetime.datetime) or (isinstance(val, str) and len(val) == 1):
            output = val
        elif isinstance(val, int):
            output = val
        else:
            data = []
            if is_number(val) and '_id' in name:
                for i in str(val):
                    if i.strip() and i in nbrs and i != '.' and i != ',':
                        data.append(nbrs[(nbrs.index(i) + shift) % 10])
                    else:
                        data.append(i)
            elif '_name' in name:
                for i in val:
                    if i.strip() and i in strs:
                        data.append(strs[(strs.index(i) + shift) % 26])    
                    else:
                        data.append(i)
            else:
                data = [val]
            
            output = ''.join(data)
    else:
        output = val
    return output


# ---------------------------------------------------------------------------------------------------------------------
def format_field(field):
    if field:
        return field.replace("'", "''").lstrip().rstrip()
    else:
        return field


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------
class GenericJsonObject(object):
    def __init__(self, co):
        try:
            self.__dict__ = json.loads(co)
        except:
            self.__dict__ = co

    def get_value(self, fields, default_value):
        levels = fields.split('|')
        return_value = default_value
        for idx in range(0, len(levels)):
            if idx == 0:
                obj = self.__dict__
            else:
                obj = obj[levels[idx-1]]

            if levels[idx] not in obj.keys():
                break
            else:
                if (idx+1) == len(levels):
                    if isinstance(obj[levels[idx]], bool):
                        return_value = (1 if obj[levels[idx]] else 0)
                    elif isinstance(obj[levels[idx]], str):
                        return_value = obj[levels[idx]].replace("'", "''")
                    else:
                        return_value = obj[levels[idx]]
                    break
        return return_value