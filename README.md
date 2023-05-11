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
usage: ans_cli.py [-h] [--usage] [--token] [--new [DATABASE_NAME]] [--exercises] [--responses] [--submissions] [--courses] [--grades] [--assignments]
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
  --responses           retrieve responses
  --exercises           retrieve exercises & questions
  --submissions         retrieve submissions

Show / Export:
  --courses, -c         list all courses
  --grades, -r          list all grades
  --assignments, -a     overview all assignments
  --file [EXCEL_FILE], -s [EXCEL_FILE]
                        export what is current shown to excel

Version 0.7, (c) Oliver Lindemann
```

## Typical workflow

Ensure that you have set an access token (for more information call '--token').

1) Initiate new database:
        `--new mydatabase` and follow instructions
2) Download grades  (responses):
        `mydatabase --responses`
3) Download all questions (exercises):
        `mydatabase --exercises` (that might take a while!)
4) Show assignment overview:
        `mydatabase -a`
5) Show grades:
        `mydatabase -r`

    To save assignments, courses or grades append `--file myexcelfile.xlsx` to a show command


