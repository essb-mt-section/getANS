import os
from pyans import AssignmentDB, load_db

# to set access token run: python -m pyans.cli --token
database_name = "fswp_21-22.ansdb"

# setup a new database, if it does not exist, otherwise load the local database
if not os.path.isfile(database_name):
    db = AssignmentDB()
    db.initialize(start_date="1.9.2021", end_date="31.8.2022",
                  select_by_name="FSWP")
    db.save(database_name, override=False)
else:
    db = load_db(database_name)

print(db.overview())

# retrieve missing data (downloading exercises/submissions takes a while!)
db.retrieve(results=True, exercises=False, submissions=False)

# show courses
print(db.course_list_df().to_string())

# show assignments
print(db.assignments_df().to_string())


# export data
data = db.grades_df() # for assignments: db.assignments_df()
# since 'data' is a Pandas dataframe you can export it to different file formats (see Pandas documentation)
data.to_csv("myexport.csv")