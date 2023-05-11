import os
from appdirs import user_config_dir

DIR = user_config_dir(appname="ans_token")
FILE = os.path.join(DIR, "token")

NO_TOKEN_ERROR_MSG = f"No ANS token found. Set token file via token.set() [or cli()] and call api_init_token(). Alternatively, call cli via command line 'python -m pyans.token'"

def set(token):
    try:
        os.mkdir(DIR)
    except FileExistsError:
        pass
    token = token.strip()
    if len(token) == 0:
        print("Remove {}".format(FILE))
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


def cli():
    try:
        t = read()
    except RuntimeError:
        t = None
    if t is None:
        wording = "set"
        print("Token file: {}".format(FILE))
    else:
        wording = "reset"
        print("Current token: '{}'".format(t))

    r = input("Do you want to {} the ANS token? (y/N) ".format(wording))
    if r.lower() == "yes" or r.lower() == "y":
        set(token=input("Token: "))
        print("")
        cli()

if __name__ == "__main__":
    cli()
