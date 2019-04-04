import re


# ---------------------------------------------------------------------------------------------------------------------
def is_url(content):
    p = re.compile("""^((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\[?[A-F0-9]*:[A-F0-9:]+\]?)(?::\d+)?(?:/?|[/?]\S+)$""", re.IGNORECASE)
    res_match = re.match(p,content)
    return not(res_match is None)


# ---------------------------------------------------------------------------------------------------------------------
def isStreetAddress(content):
    p = re.compile("""(\d{1,6}(?:\s[a-zA-Z0-9.,]+)+)""", re.IGNORECASE)
    if re.match(p,content):
        return True
    else:
       return False


# ---------------------------------------------------------------------------------------------------------------------
def isStreetAddress2(content):
    p = re.compile("""(([A-Z][a-zA-Z0-9,\s]+)+)""")
    if re.match(p,content):
        return True
    else:
        return False


# ---------------------------------------------------------------------------------------------------------------------
def is_email(content):
    p = re.compile("""(^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$)""")
    if re.match(p,content):
        return True
    else:
        return False


# ---------------------------------------------------------------------------------------------------------------------
def is_number(val):
    try:
        int(val)
        return True
    except:
        return False


