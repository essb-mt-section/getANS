# getANS

Retrieving Data from ANS with Python

Released under the MIT License

Oliver Lindemann, Erasmus University Rotterdam, NL

---

## Dependencies

Python 3.10 and the following libraries:
* pandas (>=2.2)
* appdirs (>=1.4)
* requests (>=2.32)

---

## getANS Command line interface

call: `python -m getANS`

```
usage: getANS [-h] [--usage] [--token] [--new [DATABASE_NAME]] [--exercises] [--results] [--submissions] [--courses] [--grades] [--assignments]
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
  --results             retrieve results
  --exercises           retrieve exercises & questions
  --submissions         retrieve submissions

Show / Export:
  --courses, -c         list all courses
  --grades, -g          list all grades
  --assignments, -a     overview all assignments
  --file [EXCEL_FILE], -f [EXCEL_FILE]
                        export what is shown to excel

(c) Oliver Lindemann
```

### Typical workflow

Ensure that you have set an access token (call '--token'). A new token can be generated via the ANS website:
https://ans.app/users/tokens


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

---

## getANS Python library

API documentation is work in progress

see demo script [getans_demo.py](getans_demo.py)
