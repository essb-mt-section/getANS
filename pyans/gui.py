from os import path
from copy import copy
import csv
import pandas as pd
from datetime import datetime, timedelta
import PySimpleGUI as _sg

from . import __version__
from . import api
from . import AssignmentDB
from . import _misc

OUTPUT_FILE = "out.csv"


def _time_diff(t1, t2):
    print((t1, t2))
    try:
        return t1-t2
    except:
        return 0

def new_database_window():
    #_sg.theme('SystemDefault1')
    layout = []

    layout.append([_sg.Frame('Period',
                [[ _sg.Text("from:", size=(4,1), key="txt_from"),
                   _sg.InputText("", size=(14,1), enable_events=True, readonly=True,
                            key="date_it_from"),
                   _sg.CalendarButton("change",
                                      begin_at_sunday_plus=1, size=(6, 1),
                                      target=(_sg.ThisRow, -1),
                                      close_when_date_chosen=False)
                ],[_sg.Text("to:", size=(4,1), key="txt_to"),
                   _sg.InputText("", size=(14,1), enable_events=True, readonly=True,
                            key="date_it_to"),
                   _sg.CalendarButton("change",
                                      begin_at_sunday_plus=1, size=(6, 1),
                                      target=(_sg.ThisRow, -1), enable_events=True,
                                      close_when_date_chosen=False)
                ]])])

    win =  _sg.Window('New database', layout)

    d_from = None
    d_to = None
    while True:
        e, v = win.read()
        print((e,v))

        if e in ["Cancel", "Exit", None]:
            break

        elif e.startswith("date"):
            d = datetime.fromisoformat(v[e])
            print((d, d_to, d_from))
            if e == "date_it_from:":
                d_from = copy(d)
                print(_time_diff(d_to, d_from))
            elif e == "date_it_to":
                d_to = copy(d)
                print(_time_diff(d_to, d_from))

            print((d_to, d_from))
            win[e].update(value=d.strftime("%d %B %y"))


def run():
    #new_database_window()
    #exit()

    _sg.theme('SystemDefault1')
    layout = []
    input_db_file = _sg.InputText("", size=(40, 2), enable_events=True,
                                  disabled=True, key="fl_database")
    fr_database = _sg.Frame('Local Database:',
                             [[input_db_file,
                               _sg.FileBrowse(button_text="Open",
                                              size=(12, 1),
                                              initial_folder="."),
                               _sg.Button("New", size=(6, 1),
                                          key="btn_new")
                               ]])

    layout.append([fr_database])
    layout.append([_sg.Frame('',
                             [[_sg.Button("Extract CSV", size=(12, 2),
                                          disabled=True,
                                          key="btn_csv"),
                               _sg.Button("Download Data", size=(12, 2),
                                          disabled=True,
                                          key="btn_download"),
                                _sg.Checkbox('Result Details',
                                             default=True,
                                             key="cb_details"),
                               _sg.Exit(size=(12, 2))
                               ]])])

    ml_out = _sg.Multiline(size=(120, 40), key='ml_out', autoscroll=True,
                           reroute_stdout=True, write_only=True,
                           font=('monospace', 10),
                           reroute_cprint=True)
    layout.append([ml_out])

    win = _sg.Window("{} ({})".format("ANS Results", __version__), layout)
    _misc.print_fnc = _sg.Print
    #_api.print_fnc = lambda *args, **kwargs: ml_out.print(*args, **kwargs)

    db = None
    database_name = ""
    download_process = None
    while True:
        e, v = win.read(timeout=200)
        win.Refresh()

        if e in ["Cancel", "Exit", None]:
            break

        if download_process is None:
            # no processing running
            if e == "fl_database":
                if path.isfile(v["fl_database"]):
                    database_name = path.splitext(path.split(v["fl_database"])[1])[0]
                else:
                    database_name = ""
                try:
                    db = database.load(database_name)
                except Exception as e:
                    print(e)

                if isinstance(db, AssignmentDB):
                    fr_database.update('Local Database: ' + database_name)
                    print(db.overview().to_markdown())
                else:
                    database_name = ""

                win['btn_csv'].update(disabled=len(database_name)==0)
                win['btn_download'].update(disabled=len(database_name)==0)

            if len(database_name):
                # file selected
                if e == "btn_csv":
                    data = []
                    for a in db._assignments:
                        a.order_all_questions_and_choices()
                        data.append(a.get_results_df())

                    df = pd.concat(data)
                    file = path.join(path.split(v["fl_database"])[0], OUTPUT_FILE)
                    print("writing {}".format(file))
                    with open(file, "w") as fl:
                        fl.write(df.to_csv(quoting=csv.QUOTE_NONNUMERIC))

                elif e == "btn_download":
                    download_process = database.DownloadProcess(database_name=database_name,
                                            download_answer_details=v['cb_details'])
                    download_process.start()


        # process feedback of running download
        if download_process is not None:
            while True:
                f = download_process.get_feedback()
                if len(f):
                    print(f)
                else:
                    break

            if download_process.is_finished():
                download_process.terminate()
                download_process = None

    win.close()

    if download_process is not None and not download_process.is_finished():
        download_process.terminate()


if __name__ == "__main__":
    run()
