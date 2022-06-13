import sys
import pandas as pd
from Utils import *
from canvasAPI import CanvasAPI

canvasAPI, course_id, settings, all_settings, root_dir = loadSettings()
inp = os.path.join(root_dir,'inp.json')
root_dir = os.path.join(root_dir,course_id)

def main(flags):

    assignment_ids = all_settings[course_id]['IDs']['Assignments']
    
    try:
        grades = pd.read_csv('grades.csv',index_col=False)
    except FileNotFoundError:
        print('\n\nError: Could not fild grades.csv\nPlease run file in the directory containing grades.csv\n\n')
        
    id, *assignments = grades
    
    students = [int(grades[id][i]) for i in range(1,len(grades[id]))]
    max_points = (int(grades[assignment][0]) for assignment in assignments)

    submission_data = [] # data to be submitted after confirming no issues with grade changes
    
    for assignment, points in zip(assignments,max_points):
        assignment_id = assignment_ids[assignment]
        
        canvasAPI.updateAssignment(course_id, assignment_id, {"assignment[published]" : True})
        
        # format grade data and check for grading issues
        for i, student in enumerate(students):
            new_grade = int(grades[assignment][i+1])
            grade_data = {
                "submission[posted_grade]" : str(new_grade),
            }
            submission_data.append( (assignment_id, student, grade_data, points) )
            
            current_grade = canvasAPI.getGrade(course_id, assignment_id, student)['grade']
            
            if current_grade is not None:
                current_grade = int(current_grade)
                
                if '-r' not in flags: 
                    print(f'\nError: Assignment "{assignment}" has already been graded.\nTo replace grades, enter flag "-r"\nAborting...\n')
                    sys.exit(0)
                    
                if new_grade < current_grade:
                    print(f'\nError: Grade for student {student} will be lowered from {current_grade} to {new_grade} for Assignment "{assignment}".\nEnter grades manually\nAborting...\n')
                    sys.exit(0)
    
    # post grades and update maximun points for each assignment
    for assignment_id, student, grade_data, points in submission_data:
        canvasAPI.updateAssignment(course_id, assignment_id, {"assignment[points_possible]" : points})
        canvasAPI.gradeAssignment(course_id, assignment_id, student, grade_data)
        print(f'\rGrading Assignment [{assignment_id}] for Student [{student}]                              ', end = '\r')
    print('Grading: done...                \n')

if __name__ == "__main__":
    
    _, *commands = sys.argv
    
    # main(['-r'])
    
    main(commands)