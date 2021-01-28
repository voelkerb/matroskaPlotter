"""Functions to help plot colored messages or warning and error messages to standard out"""

def printError(string, end="\n"):
    r"""Print an error message starting with \"Error:\" in red."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.FAIL + "Error: " + bcolors.ENDC + string, end=end)


def printCriticalError(string, end="\n"):
    r"""Print a red error message starting with \"Error:\"."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.FAIL + "Error: " + string + bcolors.ENDC, end=end)

def printTODO(string, end="\n"):
    r"""Print a TODO message starting with \"TODO:\"."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.HEADER + "TODO: " + string + bcolors.ENDC, end=end)


def printWarning(string, end="\n"):
    r"""Print an error message starting with \"Warning:\"."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.WARNING + "Warning: " + bcolors.ENDC + string, end=end)


def printRed(string, end="\n"):
    """Print a red Message."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.FAIL + string + bcolors.ENDC, end=end)


def printYellow(string, end="\n"):
    """Print a yellow Message."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.WARNING + string + bcolors.ENDC, end=end)


def printGreen(string, end="\n"):
    """Print a green Message."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.OKGREEN + string + bcolors.ENDC, end=end)


def printBlue(string, end="\n"):
    """Print a blue Message."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.OKBLUE + string + bcolors.ENDC, end=end)


def printPink(string, end="\n"):
    """Print a pink Message."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.HEADER + string + bcolors.ENDC, end=end)


def printTODO(string, end="\n"):
    """Print a pink Message."""
    if not isinstance(string, str):
        string = str(string)
    print(bcolors.HEADER + "TODO: " + bcolors.ENDC + string, end=end)

def printVariable(var, unit=""):
    import inspect
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    print(str([k for k, v in callers_local_vars if v is var][0])+': ' + str(var) + " " + str(unit))


class bcolors:
    """Enumeration class for escape characters in different colors"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

import keyboard, string as t
#: Maximum allowed charactes as input
MAX_ALLOWED = t.ascii_letters+"1234567890!@#$%^&*()-=_+{}[]|\:;',<>./?`~"+'"'
def readInput(text="", cancel="esc", allowed=MAX_ALLOWED):
    """
    Function to read standard-in input. Press enter to finish.
    If you are on Darwin systems, you require root access for this to work.

    :param text:    Text to display as input prompt
    :type  text:    str, default: ""
    :param cancel:  Key to escape input promt
    :type  cancel:  str, default: "esc"
    :param allowed: Allowed input character as a string
    :type  allowed: str, default: :attr:`MAX_ALLOWED<terminal.terminal.MAX_ALLOWED>`

    :return: Completed input string, None on esc pressed
    :rtype:  str or None
    """
    print(text,end="")
    output = []
    output2 = []
    while True:
        key = keyboard.read_event()
        k = key.name
        if key.event_type == "up": 
            continue
        if k == cancel:
            print("")
            return None
        elif k == "enter": 
            break
        elif k == "end": 
            output = output+output2
            output2 = []
        elif k == "home": 
            output2 = output+output2
            output = []
        elif k == "left":
            try: 
                output2.insert(0, output.pop())
            except: 
                pass
        elif k == "right":
            try: 
                output.append(output2.pop(0))
            except: 
                pass
        elif k == "space": 
            k = " "
            output.append(k)
        elif k == "backspace": 
            output = output[:-1]
        elif k in allowed: 
            output.append(k)
    foutput2 = ""
    for put in output:
        foutput2 += str(put)
    for put in output2:
        foutput2 += str(put)
    for i in range(0, len(foutput2)+2): 
        keyboard.press_and_release("backspace")
    print(foutput2)
    return foutput2