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
course_id = 1865191

def save(data):
    with open("inp.json", 'w') as f:
        json.dump(data, f, indent= 2)

def progressBar(progress, task):
    bar = '█' * int(progress) + '-' * (100 - int(progress))
    print(f'\r{task}   |{bar}| {progress:.2f}%                              ', end = '\r')
    
def init_course():
    dirs = [dir for dir in os.listdir() if dir != 'inp.json']
    total_dirs = len(dirs)
    
    tabs = settings['Tabs']
    current_tabs = canvasAPI.getTabs(course_id)
    total_tabs = len(current_tabs)
    
    total_tasks = total_dirs + 1
    
    for i, tab in enumerate(current_tabs):
        if tab['label'] not in tabs:
            tab['hidden'] = True
            canvasAPI.updateTab(course_id, tab['id'], tab)
            
        progress = (i+1)/total_tabs
        progress /= total_tasks
        progress *= 100
        progressBar(progress,"Adjussting Tabs")
    
    for i, dir in enumerate(dirs):       
        dir_settings = settings[dir]
        
        if dir_settings['assignment_group']:
            id = dir_settings['id']
            canvasAPI.enableGroupWeights(course_id)
            
            if id == None:
                
                group_data = {
                    "name" : dir,
                    "group_weight" : dir_settings['group_weight'],
                    "rules" : dir_settings['rules']
                }
                
                id = canvasAPI.createGroup(course_id, group_data).json()['id']
                settings[dir]['id'] = id
                save(settings)
            
            if dir_settings['file_upload']:
                files = os.listdir(f'{os.getcwd()}\{dir}')
                total_files = len(files)
                for j, file in enumerate(files):
                    
                    assignment_data = {
                        "assignment[name]" : file[:-4],
                        "assignment[points_possible]" : dir_settings['max_points'],
                        # "assignment[due_at]" : "2022-07-01T23:59:00-06:00",
                        # "assignment[lock_at]" : "2022-07-01T23:59:00-06:00",
                        # "assignment[unlock_at]" : "2022-07-01T23:59:00-06:00",
                        # "assignment[description]" : "description",
                        "assignment[assignment_group_id]" : id,
                        "assignment[published]" : True # boolean
                    }
                    
                    file_path = f'{os.getcwd()}\{dir}\{file}'
                    file_data = {
                        "name" : file[:-3], # str
                        "parent_folder_path" : dir, # str
                    }
                    
                    canvasAPI.createAssignmentWithFile(course_id, assignment_data, file_path, file_data)
                    
                    progress = (j+1)/total_files
                    progress /= total_tasks
                    progress += (i+1)/total_tasks
                    progress *= 100
                    progressBar(progress, f'{dir}: Uploading {file[:-4]}')
                    
            else:
                for j in range(dir_settings['amount']):
                    assignment_data = {
                        "assignment[name]" : f'{dir} {j+1}',
                        "assignment[points_possible]" : dir_settings['max_points'],
                        # "assignment[due_at]" : "2022-07-01T23:59:00-06:00",
                        # "assignment[lock_at]" : "2022-07-01T23:59:00-06:00",
                        # "assignment[unlock_at]" : "2022-07-01T23:59:00-06:00",
                        # "assignment[description]" : "description",
                        "assignment[assignment_group_id]" : id,
                        "assignment[published]" : True # boolean
                    }
                    canvasAPI.createAssignment(course_id, assignment_data)
                    
                    progress = (j+1)/dir_settings['amount']
                    progress /= total_tasks
                    progress += (i+1)/total_tasks
                    progress *= 100
                    progressBar(progress, f'{dir}: Uploading {dir} {j+1}')
        else:
            if dir_settings['file_upload']:
                files = os.listdir(f'{os.getcwd()}\{dir}')
                total_files = len(files)
                for j, file in enumerate(files):
                    file_path = f'{os.getcwd()}\{dir}\{file}'
                    file_data = {
                        "name" : file[:-4], # str
                        "parent_folder_path" : dir_settings['parent_folder'], # str
                    }
                    canvasAPI.uploadFile(course_id,file_path,file_data)
                    
                    progress = (j+1)/total_files
                    progress /= total_tasks
                    progress += (i+1)/total_tasks
                    progress *= 100
                    progressBar(progress, f'{dir}: Uploading {file[:-4]}')
    print('\n')
           

def main():
    init_course()



if __name__ == "__main__":
    main()