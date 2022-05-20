import json
import sys
import os
import datetime
import pandas as pd
from canvasAPI import CanvasAPI

os.chdir('1865191/')
with open("inp.json") as f:
    settings = json.load(f)

token = settings["login_token"]
canvasAPI = CanvasAPI(token)
course_id = 1865191

def main():
    grades = pd.read_csv('grades.csv',index_col=False)
    id, *assignments = grades
    
    students = [int(grades[id][i]) for i in range(1,len(grades[id]))]
    max_points = (int(grades[assignment][0]) for assignment in assignments)

    assignment_data = canvasAPI.getAssignments(course_id)
    
    for data in assignment_data:
        print(data['name'], data['id'])
    assignment_ids = {data["name"] : data["id"] for data in assignment_data}
    print(assignment_ids)
    
    for assignment in assignments:
        assignment_id = 0
        for i, student in enumerate(students):
            grade_data = {
                "submission[posted_grade]" : str(grades[assignment][i+1]),
            }
            # canvasAPI.gradeAssignment(course_id, assignment_id,student,grade_data)
    
    

if __name__ == "__main__":
    main()