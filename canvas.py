import sys
import pandas as pd
import json
import os
from canvasAPI import CanvasAPI

"""
Assignment Data:
{
    "assignment[name]" : "Assignment 1", # str
    "assignment[points_possible]" : 10, # int
    "assignment[due_at]" : "2022-07-01T23:59:00-06:00", # str : ISO 8601 formatted date and time
    "assignment[lock_at]" : "2022-07-01T23:59:00-06:00", # str : ISO 8601 formatted date and time
    "assignment[unlock_at]" : "2022-07-01T23:59:00-06:00", # str : ISO 8601 formatted date and time
    "assignment[description]" : "description", #str
    "assignment[assignment_group_id]" : 12345, # int
    "assignment[published]" : True # boolean
}

Group Data:
{
    "name" : "group 1", # str
    "group_weight" : 25, # int : %
    "rules" : "drop_lowest:1\ndrop_highest:2\n" # str : rule1:value\nrule2:value\n...
}

File Data FOR UPLOADING:
{
    "name" : "file 1", # str
    "parent_folder_path" : "folder name", # str
}

Tab Data:
{
    "id": "context_external_tool_153670",
    "html_url": "/courses/1865191/external_tools/153670",
    "full_url": "https://bridgeport.instructure.com/courses/1865191/external_tools/153670",
    "position": 22, # int
    "hidden": True, # boolean
    "visibility": "admins", # str : public, members, admins, none
    "label": "Studio", # str
    "type": "external",
    "url": "https://bridgeport.instructure.com/api/v1/courses/1865191/external_tools/sessionless_launch?id=153670&launch_type=course_navigation"
}

Grade Data:
{
    "comment[text_comment]" : "∀ ε > 0 in limit definition, NOT Let ε > 0 be given!\n-5 points", # str
    "submission[posted_grade]" : "95", # str : can take formats such as "92.5", "84%", "-A", "pass", "fail", "complete", "incomplete"
    "submission[excuse]" : True, # boolean
}
"""

os.chdir('1865191/')
with open("inp.json") as f:
    settings = json.load(f)

token = settings["login_token"]
canvasAPI = CanvasAPI(token)

def init_course():
    dirs = (dir for dir in os.listdir() if dir != 'inp.json')
    for dir in dirs:
        dir_settings = settings[dir]
        print(dir_settings)
    

def main():
    init_course()
    # & C:/Users/Romeo/anaconda3/python.exe "c:/Users/Romeo/Desktop/Canvas API/canvas.py"  cmd



if __name__ == "__main__":
    main()