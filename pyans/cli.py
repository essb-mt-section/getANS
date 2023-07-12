import os
from argparse import ArgumentParser

from . import AssignmentDB, __version__, load_db
from ._misc import make_date
from ._token import token_cli


def run():
    usage = """\
Ensure that you have set a access token. (for more information call '--token')

Typical workflow:

1) Initiate new database:
        `--new mydatabase` and follow instructions
2) Download grades  (results):
        `mydatabase --results`
3) Download all questions (exercises):
        `mydatabase --exercises` (that might take a while!)
4) Show assignment overview:
        `mydatabase -a`
5) Show grades:
        `mydatabase -r`

   To save assignments, courses or grades add `--file myexcelfile.xlsx`
   to a show command

"""

    parser = ArgumentParser(
        prog = "pyans",
        description = "Retrieving Data from ANS. " ,
        epilog=f"Version {__version__}, (c) Oliver Lindemann")

    parser.add_argument("--usage", action="store_true", default=False,
                    help="show typical workflow")

    parser.add_argument("--token", action="store_true", default=False,
                    help="setting access token")

    parser.add_argument("DATABASE", nargs='?', default="",
                        help="database file")


    group1 = parser.add_argument_group('Retrieve / Download')


    group1.add_argument("--new", "-n", nargs='?', metavar="DATABASE_NAME", default="",
            help="initiate new database")

    group1.add_argument("--results", action="store_true", default=False,
                    help="retrieve results")

    group1.add_argument("--exercises",  action="store_true", default=False,
                    help="retrieve exercises & questions")

    group1.add_argument("--submissions",  action="store_true", default=False,
                    help="retrieve individual submissions and student information")

    group2 = parser.add_argument_group('Show / Export')

    group2.add_argument("--courses", "-c", action="store_true", default=False,
                    help="list all courses")

    group2.add_argument("--grades", "-g", action="store_true", default=False,
                    help="list all grades")

    group2.add_argument("--assignments", "-a", action="store_true", default=False,
                    help="overview assignments")

    group2.add_argument("--file", "-s", nargs='?', metavar="EXCEL_FILE", default="",
            help="export what is shown to excel")


    args = vars(parser.parse_args())
    #print(args); exit()

    if args["usage"]:
        parser.print_usage()
        print("\n" + usage)
        exit()

    elif args["token"]:
        token_cli()
        exit()

    elif args["new"] is not None and len(args["new"]):
        new_database(args["new"])
        exit()

    elif len(args["DATABASE"])==0:
        parser.print_usage()
        exit()

    db = get_database(args["DATABASE"])

    outfile = args["file"]
    if outfile is None:
        outfile = ""
    elif len(outfile)>0:
        outfile = outfile.removesuffix(".xlsx") + ".xlsx"

    if args["submissions"]:
        args["results"] = True # submissions requires results
    if args["results"] or args["exercises"]:
        db.retrieve(results=args["results"],
                    exercises=args["exercises"],
                    submissions=args["submissions"])

    df = None
    if args["courses"]:
        df = db.course_list_df()
        print(df.to_string())

    elif args["grades"]:
        df = db.grades_df()
        pdf = df.drop(columns=["course_name"], errors='ignore')
        print(pdf)

    elif args["assignments"]:
        df = db.assignments_df()
        pdf = df.drop(columns=["id", "course_id",
                               "name", "course_name"], errors='ignore')
        print(pdf.to_string())

    if df is not None:
        if len(outfile)>0:
            df.to_excel(outfile)
            print(f"saved: {outfile}")
    else:
        print(db.overview())


def new_database(database):

    db_file = database.removesuffix(AssignmentDB.DB_SUFFIX) + AssignmentDB.DB_SUFFIX

    ## new data  base
    if os.path.isfile(db_file):
        ask_yes_or_quit(f"Do you want to override the existing data {db_file}? (y/N) ")

    start_date = ask_date("Enter start date (e.g. 28.4.2019): ")
    end_date = ask_date("Enter end date: ")
    select = input("Select assignments by name (regex): ")

    info = f"{start_date.strftime('%d.%m.%Y')} - " +\
            f"{end_date.strftime('%d.%m.%Y')}, selection: '{select}'"
    ask_yes_or_quit("\nDo you want initiate the following database?\n"+
                        f"  name: {db_file}\n"+
                        f"  {info}\n  >> (y/N) ")
    db = AssignmentDB(info)
    db.initialize(start_date=start_date, end_date=end_date,
                select_by_name=select)

    db.save(db_file, override=True)


def get_database(database):

    db_file = None
    if os.path.isfile(database):
        db_file = database
    elif os.path.isfile(database + AssignmentDB.DB_SUFFIX):
        db_file = database + AssignmentDB.DB_SUFFIX
    else:
        print(f"Can't find '{database}'!")
        exit()

    return load_db(db_file)


def ask_yes_or_quit(txt):
    resp = input(txt)
    if resp.lower() != "yes" and resp.lower() != "y":
        exit()
    return resp

def ask_date(txt):
    resp = input(txt)
    try:
        return make_date(resp.strip())
    except ValueError:
        ask_yes_or_quit(f"'{resp}' is not a valid date. Try it again (y/N)? ")
        return ask_date(txt)


if __name__ == "__main__":
    run()
