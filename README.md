# PyANS

Retrieving Data from ANS with Python

Released under the MIT License

Oliver Lindemann, Erasmus University Rotterdam, NL

---

## Dependencies

Python 3.8+ and the following libraries (see [requirements.txt](requirements.txt)):
* pandas (>=1.5)
* appdirs (>=1.4)
* requests (>=2.25)

---

## PyANS Command line interface

call: `python ans_cli.py`

```
usage: ans_cli.py [-h] [--usage] [--token] [--new [DATABASE_NAME]] [--exercises] [--responses] [--submissions] [--courses] [--results] [--assignments]
                  [--file [EXCEL_FILE]]
                  [DATABASE]

Retrieving Data from ANS.

positional arguments:
  DATABASE              database file

options:
  -h, --help            show this help message and exit
  --usage               show typical workflow
  --token               setting access token

Retrieve / Download:
  --new [DATABASE_NAME], -n [DATABASE_NAME]
                        initiate new database
  --exercises           retrieve exercises & questions
  --responses           retrieve responses
  --submissions         retrieve submissions

Show / Export:
  --courses, -c         list all courses
  --results, -r         list all results
  --assignments, -a     overview all assignments
  --file [EXCEL_FILE], -s [EXCEL_FILE]
                        export to excel file

Version 0.7, (c) Oliver Lindemann
```

## Typical workflow

Ensure that you have set a access token. (for more information call '--token')

1) Initiate new database:
        `--new mydatabase` and follow instructions
2) Download results  (responses):
        `mydatabase --responses`
3) Download all questions (exercises):
        `mydatabase --exercises` (that might take a while!)
4) Show assignment overview:
        `mydatabase -a`
5) Show results:
        `mydatabase -r`

    To save assignment overview or results just append `--file myexcelfile.xlsx`


