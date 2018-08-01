


class Print(object):
    ANSI_CLEAR               = "\u001b[0m"
    ANSI_CLEOL               = "\u001b[K"                           # CLEAR TO END OF LINE
    ANSI_CLSML               = "\u001b[1K"                          # CLEAR SAME LINE
    ANSI_RSCUR               = "\u001b[G"                           # RESET / MOVE the CURSOR to the line beginning

    ANSI_BLACK               = "\u001b[30m"
    ANSI_RED                 = "\u001b[31m"
    ANSI_GREEN               = "\u001b[32m"
    ANSI_YELLOW              = "\u001b[33m"
    ANSI_BLUE                = "\u001b[34m"
    ANSI_MAGENTA             = "\u001b[35m"
    ANSI_CYAN                = "\u001b[36m"
    ANSI_WHITE               = "\u001b[37m"

    ANSI_BG_BLACK            = "\u001b[40m"
    ANSI_BG_RED              = "\u001b[41m"
    ANSI_BG_GREEN            = "\u001b[42m"
    ANSI_BG_YELLOW           = "\u001b[43m"
    ANSI_BG_BLUE             = "\u001b[44m"
    ANSI_BG_MAGENTA          = "\u001b[45m"
    ANSI_BG_CYAN             = "\u001b[46m"
    ANSI_BG_WHITE            = "\u001b[47m"

    @classmethod
    def title(cls, title: str):
        length = len(title)
        ppsl = 4
        ps = '*' * (length + (ppsl * 2) + 2)
        pps = '*' * ppsl
        if length > 0:
            print(f"{Print.ANSI_BG_WHITE}{Print.ANSI_BLACK}{ps}\n{pps} {title} {pps}\n{ps}{Print.ANSI_CLEAR}{Print.ANSI_CLEOL}")

    @classmethod
    def green(cls, output: str):
        color = Print.ANSI_GREEN
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def cyan(cls, output: str):
        color = Print.ANSI_BG_CYAN
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def green_bg(cls, output: str):
        color = f"{Print.ANSI_BG_GREEN}{Print.ANSI_BLACK}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def red(cls, output: str):
        color = f"{Print.ANSI_RED}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def red_bg(cls, output: str):
        color = f"{Print.ANSI_BG_RED}{Print.ANSI_BLACK}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def magenta_bg(cls, output: str):
        color = f"{Print.ANSI_BG_MAGENTA}{Print.ANSI_BLACK}"
        eol = Print.ANSI_CLEOL
        clear = Print.ANSI_CLEAR
        print(f"{color}{output}{eol}{clear}")

    @classmethod
    def label_value(cls, label: str, value):
        """ Output in the form of =>  label               : value """
        # color = f"{Print.ANSI_BG_GREEN}{Print.ANSI_BLACK}"
        # eol = Print.ANSI_CLEOL
        # clear = Print.ANSI_CLEAR
        # print(f"{color}{output}{eol}{clear}")
        print(f"{label:<50} : {value}")

    @classmethod
    def progress(cls, complete, total, char_width=80):
        """ Create dynmaically updating progress bar """
        to_check = ( complete, total, char_width )
        if not all( type(i) is int for i in to_check):
            raise TypeError(f"all inputs must be of type int, {to_check}")
        complete = complete + 1
        to_check = ( complete, total, char_width )
        if total != 0 and char_width != 0:
            interval = total / char_width
        if any( i == 0 for i in to_check):
            raise ValueError(f"Inputs can not be 0, {to_check}")
        else:
            mod = ( interval ) % complete == 0
            percent = complete / total
            intervals = round( complete / interval)
        if mod == 0:
            print(f"{cls.ANSI_CLSML}{cls.ANSI_RSCUR} 0% [{percent:6.01%}] |{intervals * '='}" + ( " " * ( char_width - intervals ) ) + "| 100%", end='')
        if complete == total:
            print("... complete")
