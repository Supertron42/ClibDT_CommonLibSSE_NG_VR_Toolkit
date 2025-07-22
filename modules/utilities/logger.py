from colorama import Fore, Style

def cprint(msg, color=Fore.RESET):
    print(color + msg + Style.RESET_ALL) 