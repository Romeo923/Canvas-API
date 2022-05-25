import os
from canvasAPI import CanvasAPI
from Utils import *

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

os.chdir('1865191/Hmk')

canvasAPI, course_id, all_settings, inp = loadSettings()
course_settings = all_settings[course_id]

def resetInp():
   
    all_settings[course_id]['IDs'] = {
        "Groups":{},
        "Assignments":{},
        "Files":{},
        "Folders":{}
    }
    
    save(all_settings, inp)
    print('\ninp.json reset...\n')
        
def resetCanvas():
    
    canvasAPI.disableGroupWeights(course_id)
    
    assignments = canvasAPI.getAssignments(course_id)
    while len(assignments) > 0:
        for assignment in assignments:
            canvasAPI.deleteAssignment(course_id, assignment['id'])
        assignments = canvasAPI.getAssignments(course_id)
        print("deleting assignments")
    
    groups = canvasAPI.getCourseGroups(course_id)
    while len(groups) > 0:
        for group in groups:
            canvasAPI.deleteGroup(course_id, group['id'])
        groups = canvasAPI.getCourseGroups(course_id)
        print('deleting groups')

    files = canvasAPI.getFiles(course_id)
    while len(files) > 0:
        for file in files:
            canvasAPI.deleteFile(file['id'])
        files = canvasAPI.getFiles(course_id)
        print("deleting files")
        
    folders = canvasAPI.getFolders(course_id)
    while len(folders) > 1:
        for folder in folders:
            canvasAPI.deleteFolder(folder['id'])
        folders = canvasAPI.getFolders(course_id)
        print("deleting folders")

    print('\nCanvas Reset...\n')
   
def initGroup(dir, dir_settings):
    group_data = {
        "name" : dir,
        "group_weight" : dir_settings['group_weight'],
        "rules" : dir_settings['rules']
    }
                    
    id = canvasAPI.createGroup(course_id, group_data).json()['id']
    course_settings['IDs']['Groups'][dir] = id
    return id

def initCourse():
    *dirs, tabs, class_schedule, IDs = course_settings
    
    total_dirs = len(dirs)
    
    canvasAPI.enableGroupWeights(course_id)
    
    my_tabs = course_settings[tabs]
    schedule = course_settings[class_schedule]
    
    canvas_tabs = canvasAPI.getTabs(course_id)
    total_tabs = len(canvas_tabs)
    
    total_tasks = total_dirs + 1
    
    # update each tab's visibility and position
    for i, tab in enumerate(canvas_tabs):
        
        if tab['label'] not in my_tabs:
            tab['hidden'] = True
            tab['position'] = i
            canvasAPI.updateTab(course_id, tab['id'], tab)
        
        # update progress bar --------------------------------    
        progress = (i+1)/total_tabs
        progress /= total_tasks
        progress *= 100
        progressBar(progress,"Adjusting Tabs")
        # -------------------------------------
    
    # loops through each directory defined in inp.json
    for i, dir in enumerate(dirs):    
         
        dir_settings = course_settings[dir]
        
        match dir_settings:
            
            # uploads assignments based on file names and number of files
            case {'assignment_group': True, 'file_upload': True}:
               
                id = initGroup(dir, dir_settings)
                
                path = os.path.join(os.getcwd(), dir)
                files = sorted(os.listdir(path))
                total_files = len(files)
                
                folder_data = {
                    "name" : dir_settings['parent_folder'],
                    "parent_folder_path" : ""
                }
                
                parent_folder_id = canvasAPI.createFolder(course_id,folder_data).json()['id']
                course_settings[IDs]['Folders'][dir] = parent_folder_id
                
                dates = formatDate(
                    dir_settings['start_date'], 
                    dir_settings['interval'], 
                    schedule['days'], 
                    schedule['holy_days'], 
                    total_files
                )
                
                # create each assignment, upload file, attach file to assignment
                for j, file in enumerate(files):
                    
                    assignment_data = {
                        "assignment[name]" : file[:-4],
                        "assignment[points_possible]" : dir_settings['max_points'],
                        "assignment[due_at]" : dates[j],
                        "assignment[assignment_group_id]" : id,
                        "assignment[published]" : False
                    }

                    file_path = os.path.join(os.getcwd(), dir, file)

                    assignment_response, file_id = canvasAPI.createAssignmentWithFile(course_id, assignment_data, file_path)
                    canvasAPI.updateFile(
                        file_id,
                        {
                            "name":file[:-4], 
                            "parent_folder_id": parent_folder_id
                        }
                    )
                    
                    assignment_id = assignment_response.json()['id']
                    course_settings[IDs]['Assignments'][file[:-4]] = assignment_id
                    course_settings[IDs]['Files'][file[:-4]] = file_id
                    
                    
                    # update progress bar -------------------------------- 
                    progress = (j+1)/total_files
                    progress /= total_tasks
                    progress += (i+1)/total_tasks
                    progress *= 100
                    progressBar(progress, f'{dir}: Uploading {file[:-4]}')
                    # -----------------------------------------------------

            # uploads assignments based on given 'amount' parameter in inp.json with name [Group name]-[index]
            case {'assignment_group': True}:
                
                id = initGroup(dir, dir_settings)

                dates = formatDate(
                    dir_settings['start_date'], 
                    dir_settings['interval'], 
                    schedule['days'], 
                    schedule['holy_days'], 
                    dir_settings['amount']
                )
                
                # Creates the specified number of Assignments
                for j in range(dir_settings['amount']):
                    
                    assignment_data = {
                        "assignment[name]" : f'{dir} {j+1}',
                        "assignment[points_possible]" : dir_settings['max_points'],
                        "assignment[due_at]" : dates[j],
                        "assignment[assignment_group_id]" : id,
                        "assignment[published]" : False
                    }
                    assignment_id = canvasAPI.createAssignment(course_id, assignment_data).json()['id']
                    course_settings[IDs]['Assignments'][f'{dir} {j+1}'] = assignment_id
                    
                    # update progress bar --------------------------------
                    progress = (j+1)/dir_settings['amount']
                    progress /= total_tasks
                    progress += (i+1)/total_tasks
                    progress *= 100
                    progressBar(progress, f'{dir}: Uploading {dir} {j+1}')
                    # ----------------------------------------------------
            
            # uploads files
            case {'file_upload': True}:
                
                path = os.path.join(os.getcwd(), dir)
                files = sorted(os.listdir(path))
                total_files = len(files)
                
                parent_folder_id = None
                if dir_settings['parent_folder'] is not None:
                    folder_data = {
                        "name" : dir_settings['parent_folder'],
                        "parent_folder_path" : ""
                    }
                    parent_folder_id = canvasAPI.createFolder(course_id,folder_data).json()['id']                   
                    
                course_settings[IDs]['Folders'][dir] = parent_folder_id
                
                # uploads each file
                for j, file in enumerate(files):                    
                    
                    file_path = os.path.join(os.getcwd(), dir, file)
                    file_id = canvasAPI.uploadFile(course_id,file_path).json()['id']
                    
                    file_data = {
                        "name":file[:-4],
                        "parent_folder_id" : parent_folder_id
                    }
                    
                    canvasAPI.updateFile(file_id, file_data)
                    course_settings[IDs]['Files'][file[:-4]] = file_id
                    
                    # update progress bar --------------------------------
                    progress = (j+1)/total_files
                    progress /= total_tasks
                    progress += (i+1)/total_tasks
                    progress *= 100
                    progressBar(progress, f'{dir}: Uploading {file[:-4]}')
                    # ----------------------------------------------------
            
            case _:
                pass
        
        all_settings[course_id] = course_settings
        save(all_settings, inp)
        
    progressBar(100,"Done...")
    print('\n')

def main():
    resetInp()
    resetCanvas()
    initCourse()


if __name__ == "__main__":
    main()