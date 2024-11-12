import os
from appdirs import user_config_dir

DIR = user_config_dir(appname="ans_token")
FILE = os.path.join(DIR, "token")

NO_TOKEN_ERROR_MSG = f"No ANS token found. Set token file via token.set() [or cli()] and call api_init_token(). Alternatively, call cli via command line 'python -m getans.token'"

INFO="""
Accessing ANS with getiANS requires authorization via an access token. Please copy
and paste your token below.  A new token can be generated via the ANS website:
https://ans.app/users/tokens
"""

def set(token):
    try:
        os.mkdir(DIR)
    except FileExistsError:
        pass
    token = token.strip()
    if len(token) == 0:
        print(f"Remove {FILE}")
        os.remove(FILE)
    else:
        with open(FILE, "w") as fl:
            fl.write(token)

def read():
    if os.path.isfile(FILE):
        with open(FILE, "r") as fl:
            return fl.read()
    else:
        raise RuntimeError(NO_TOKEN_ERROR_MSG)


def token_cli():
    print(INFO)
    try:
        t = read()
    except RuntimeError:
        t = None
    if t is None:
        wording = "set"
        print(f"Token file: '{t}'")
    else:
        wording = "reset"
        print(f"Current token: '{t}'")

    r = input(f"Do you want to {wording} ANS token? (y/N) ")
    if r.lower() == "yes" or r.lower() == "y":
        set(token=input("Token: "))
        print(f"\nNew token: '{read()}'")