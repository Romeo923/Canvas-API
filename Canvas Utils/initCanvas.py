import os
from canvasAPI import CanvasAPI
from Utils import *

canvasAPI, course_id, settings, all_settings, root_dir = loadSettings()
inp = os.path.join(root_dir,'inp.json')
root_dir = os.path.join(root_dir,course_id)

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
    all_settings[course_id]['IDs']['Groups'][dir] = id
    return id

def initCourse():
    ASSIGNMENTS, FILES, TABS, CLASS_SCHEDULE, *other_settings = settings
    IDs = all_settings[course_id]['IDs']
    
    total_dirs = len(settings[ASSIGNMENTS]) + len(settings[FILES]) + len(other_settings)
    
    canvasAPI.enableGroupWeights(course_id)
    
    my_tabs = settings[TABS]
    schedule = settings[CLASS_SCHEDULE]
    
    canvas_tabs = canvasAPI.getTabs(course_id)
    total_tabs = len(canvas_tabs)
    
    total_tasks = total_dirs + 1
    
    #* update each tab's visibility and position
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
    
    #* inits assignments 
    for i, dir in enumerate(settings[ASSIGNMENTS]):
        dir_settings = settings[ASSIGNMENTS][dir]
        
        #* Assignment w/File
        if dir_settings['file_upload']:
            id = initGroup(dir, dir_settings)
            
            path = os.path.join(root_dir, dir)
            files = sorted(os.listdir(path))
            total_files = len(files)
            
            folder_data = {
                "name" : dir_settings['parent_folder'],
                "parent_folder_path" : ""
            }
            
            parent_folder_id = canvasAPI.createFolder(course_id,folder_data).json()['id']
            IDs['Folders'][dir] = parent_folder_id
            
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

                file_path = os.path.join(root_dir, dir, file)

                assignment_response, file_id = canvasAPI.createAssignmentWithFile(course_id, assignment_data, file_path)
                canvasAPI.updateFile(
                    file_id,
                    {
                        "name":file[:-4], 
                        "parent_folder_id": parent_folder_id
                    }
                )
                
                assignment_id = assignment_response.json()['id']
                IDs['Assignments'][file[:-4]] = assignment_id
                IDs['Files'][file[:-4]] = file_id
                
                
                # update progress bar -------------------------------- 
                progress = (j+1)/total_files
                progress /= total_tasks
                progress += (i+1)/total_tasks
                progress *= 100
                progressBar(progress, f'{dir}: Uploading {file[:-4]}')
                # -----------------------------------------------------
        
        #* Assignment w/o File
        else:
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
                IDs['Assignments'][f'{dir} {j+1}'] = assignment_id
                
                # update progress bar --------------------------------
                progress = (j+1)/dir_settings['amount']
                progress /= total_tasks
                progress += (i+1)/total_tasks
                progress *= 100
                progressBar(progress, f'{dir}: Uploading {dir} {j+1}')
                # ----------------------------------------------------
        
        
    #* inits files
    for i, dir in enumerate(settings[FILES]):
        dir_settings = settings[FILES][dir]
        
        path = os.path.join(root_dir, dir)
        files = sorted(os.listdir(path))
        total_files = len(files)
        
        parent_folder_id = None
        if dir_settings['parent_folder'] is not None:
            folder_data = {
                "name" : dir_settings['parent_folder'],
                "parent_folder_path" : ""
            }
            parent_folder_id = canvasAPI.createFolder(course_id,folder_data).json()['id']                   
            
        IDs['Folders'][dir] = parent_folder_id
        
        #* uploads each file
        for j, file in enumerate(files):                    
            
            file_name, ext = file.split('.',1)
            file_path = os.path.join(root_dir, dir, file)
            file_id = canvasAPI.uploadFile(course_id,file_path).json()['id']
            
            file_data = {
                "name":file_name,
                "parent_folder_id" : parent_folder_id
            }
            
            canvasAPI.updateFile(file_id, file_data)
            IDs['Files'][file_name] = file_id
            
            # update progress bar --------------------------------
            progress = (j+1)/total_files
            progress /= total_tasks
            progress += (i+len(settings[ASSIGNMENTS])+1)/total_tasks
            progress *= 100
            progressBar(progress, f'{dir}: Uploading {file_name}')
            # ----------------------------------------------------
    
    #* inits Modules and Quizzes
    for option in other_settings:
        
        match option:
            case 'Modules':
                # TODO init Modules
                pass
            case 'Quizzes':
                # TODO init Quizzes
                pass
    
    save(all_settings, inp)      
    progressBar(100,"Done...")
    print('\n')
    

def main():
    resetInp()
    resetCanvas()
    initCourse()

if __name__ == "__main__":
    main()