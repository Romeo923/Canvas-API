import os
import json
from canvasAPI import CanvasAPI
from Utils import *

#! STILL IN PROGRESS

#! Issues: Default Settings, Time intervals, Holy Days, Course ID, Assignments w/ files, possibly more

course_id = "1865191"

with open("copy_inp.json") as f:
    settings = json.load(f)

canvasAPI = CanvasAPI(settings["login_token"])

IDs = {
    "Groups":{},
    "Assignments":{},
    "Files":{},
    "Folders":{}
}

course_settings = {
    "IDs" : IDs,
    "Assignments" : {},
    "Files" : {},
    "Tabs" : [],
    "Class Schedule" : {
        "days" : {},
        "holy_days" : {}
    }
}

settings[course_id] = course_settings

#* Copy Tabs
tabs = canvasAPI.getTabs(course_id)
my_tabs = [tab["label"] for tab in tabs if ('hidden' in tab and tab["hidden"] is False) or ('visibility' in tab and tab['visibility'] == 'public')]
course_settings['Tabs'] = my_tabs

#* Copy Groups
groups = canvasAPI.getCourseGroups(course_id)
for group in groups:
    id = group['id']
    name = group['name']
    group_weight = group['group_weight']
    group_rules = group['rules']
    
    rules = ''
    for rule in group_rules:
        rules += f'{rule}:{group_rules[rule]}\n'
    if len(rules) == 0: rules = None
    
    group_data = {
        "rules": rules,
        "file_upload": None,
        "parent_folder": name,
        "group_weight": group_weight,
        "max_points": None,
        "start_date": None,
        "interval": None
    }
    course_settings['Assignments'][name] = group_data
    IDs['Groups'][name] = id

# TODO Figure out assignments
assignments = canvasAPI.getAssignments(course_id)
for assignment in assignments:
    id = assignment['id']
    name = assignment['name']
    
    IDs['Assignments'][name] = id

# TODO Figure out Folders
folders = canvasAPI.getFolders(course_id)
for folder in folders:
    id = folder['id']
    name = folder['name']
    
    if name == 'course files' : name = 'root'
    IDs['Folders'][name] = id

# TODO Figure out Files 
files = canvasAPI.getFiles(course_id)
for file in files:
    id = file['id']
    name = file['display_name']
    
    IDs['Files'][name] = id

    parent_folder = file['folder_id']
    if parent_folder == IDs['Folders']['root']:
        IDs['Folders'][name] = None
        course_settings['Files'][name] = {"parent_folder": None}



modules = canvasAPI.getModules(course_id)
course_settings['Modules'] = modules
quizzes = canvasAPI.getQuizzes(course_id)
course_settings['Quizzes'] = quizzes



save(settings, 'copy_inp.json')