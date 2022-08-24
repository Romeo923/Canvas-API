import os
from canvasAPI import CanvasAPI
from Utils import *

os.chdir('./1865191')
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
        print("deleting assignments")
        for assignment in assignments:
            canvasAPI.deleteAssignment(course_id, assignment['id'])
        assignments = canvasAPI.getAssignments(course_id)
    
    groups = canvasAPI.getCourseGroups(course_id)
    while len(groups) > 0:
        print('deleting groups')
        for group in groups:
            canvasAPI.deleteGroup(course_id, group['id'])
        groups = canvasAPI.getCourseGroups(course_id)

    files = canvasAPI.getFiles(course_id)
    while len(files) > 0:
        print("deleting files")
        for file in files:
            canvasAPI.deleteFile(file['id'])
        files = canvasAPI.getFiles(course_id)
        
    folders = canvasAPI.getFolders(course_id)
    while len(folders) > 1:
        print("deleting folders")
        for folder in folders:
            canvasAPI.deleteFolder(folder['id'])
        folders = canvasAPI.getFolders(course_id)
        
    # gradingScales = canvasAPI.getGradingScales(course_id)
    # while len(gradingScales) > 0:
    #     for gradingScale in gradingScales:
    #         canvasAPI.deleteGradingScale(course_id, gradingScale['id'])
    #     gradingScales = canvasAPI.getGradingScales(course_id)
    #     print("deleting grading scales")
    #     print(gradingScales)

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
    ASSIGNMENTS, FILES, FILE_EXTS, GRADING_SCALE, TABS, CLASS_SCHEDULE, *other_settings = settings
    IDs = all_settings[course_id]['IDs']
    
    total_dirs = len(settings[ASSIGNMENTS]) + len(settings[FILES]) + len(other_settings)
    
    canvasAPI.enableGroupWeights(course_id)
    
    my_tabs = settings[TABS]
    schedule = settings[CLASS_SCHEDULE]
    grading_scale = settings[GRADING_SCALE]
    
    canvas_tabs = canvasAPI.getTabs(course_id)
    total_tabs = len(canvas_tabs)
    total_grades = len(grading_scale)
    
    total_tasks = total_dirs + 2
    
    exam_dates = [settings[ASSIGNMENTS][exam]['start_date'] for exam in settings[ASSIGNMENTS] if 'exam' in exam.lower()]
    
    #* update each tab's visibility and position
    for i, tab in enumerate(canvas_tabs):
        
        # update progress bar --------------------------------    
        progress = (i+1)/total_tabs
        progress /= total_tasks
        progress *= 100
        progressBar(progress,"Adjusting Tabs")
        # -------------------------------------
    
        if tab['label'] not in my_tabs:
            tab['hidden'] = True
        else:
            tab['position'] = my_tabs.index(tab['label']) + 1
            tab['hidden'] = False
        canvasAPI.updateTab(course_id, tab['id'], tab)
        

    #* creates grading scales
    scale_data = [ ('title', 'TEST Grading Scale') ]
    
    for i, grade in enumerate(grading_scale):
                
        # update progress bar --------------------------------    
        progress = (i+1)/total_grades
        progress /= total_tasks
        progress += 1/total_tasks
        progress *= 100
        progressBar(progress,"Creating Grade Scales")
        # -------------------------------------
        
        scale_data.append(('grading_scheme_entry[][name]', grade))
        scale_data.append(('grading_scheme_entry[][value]', grading_scale[grade]))

        
    scale_id = canvasAPI.createGradingScale(course_id, scale_data).json()['id']
    canvasAPI.updateCourseSettings(course_id,{'course[grading_standard_id]': scale_id})
    
    #* inits assignments 
    for i, dir in enumerate(settings[ASSIGNMENTS]):
        
        # update progress bar --------------------------------
        progress = (i+2)/total_tasks
        progress *= 100
        progressBar(progress, f'{dir}: Begining Uploads')
        # ----------------------------------------------------
        
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
            holy_days = schedule['holy_days']
            
            dates = generateDates(
                dir_settings['start_date'], 
                dir_settings['end_date'], 
                dir_settings['interval'], 
                schedule['days'],
                holy_days if 'exam' in dir.lower() else holy_days + exam_dates, 
                total_files
            )
            
            # create each assignment, upload file, attach file to assignment
            for j, (file_name, ext) in enumerate( [f for file in files if (f := file.split('.',1)) and f[-1] in settings[FILE_EXTS] and dir.lower() in f[0].lower()] ): 
                 
                # update progress bar -------------------------------- 
                progress = (j+1)/total_files
                progress /= total_tasks
                progress += (i+2)/total_tasks
                progress *= 100
                progressBar(progress, f'{dir}: Uploading {file_name}')
                # -----------------------------------------------------
                
                assignment_data = {
                    "assignment[name]" : file_name,
                    "assignment[points_possible]" : dir_settings['max_points'],
                    "assignment[grading_type]": "letter_grade",
                    "assignment[grading_standard_id]": scale_id,
                    "assignment[due_at]" : dates[j],
                    "assignment[assignment_group_id]" : id,
                    "assignment[published]" : False
                }

                file_path = os.path.join(root_dir, dir, f'{file_name}.{ext}')

                assignment_response, file_id = canvasAPI.createAssignmentWithFile(course_id, assignment_data, file_path)
                canvasAPI.updateFile(
                    file_id,
                    {
                        "name":file_name, 
                        "parent_folder_id": parent_folder_id
                    }
                )
                
                assignment_id = assignment_response.json()['id']
                IDs['Assignments'][file_name] = assignment_id
                IDs['Files'][file_name] = file_id
                
        
        #* Assignment w/o File
        else:
            
            id = initGroup(dir, dir_settings)
            holy_days = schedule['holy_days']
            
            dates = generateDates(
                dir_settings['start_date'], 
                dir_settings['end_date'], 
                dir_settings['interval'], 
                schedule['days'],
                holy_days if 'exam' in dir.lower() else holy_days + exam_dates, 
                dir_settings['amount']
            )
            
            # Creates the specified number of Assignments
            for j in range(dir_settings['amount']):
                
                # update progress bar --------------------------------
                progress = (j+1)/dir_settings['amount']
                progress /= total_tasks
                progress += (i+2)/total_tasks
                progress *= 100
                progressBar(progress, f'{dir}: Uploading {dir} {j+1}')
                # ----------------------------------------------------
                
                assignment_data = {
                    "assignment[name]" : f'{dir} {j+1}',
                    "assignment[points_possible]" : dir_settings['max_points'],
                    "assignment[grading_type]": "letter_grade",
                    "assignment[grading_standard_id]": scale_id,
                    "assignment[due_at]" : dates[j],
                    "assignment[assignment_group_id]" : id,
                    "assignment[published]" : False
                }
                assignment_id = canvasAPI.createAssignment(course_id, assignment_data).json()['id']
                IDs['Assignments'][f'{dir} {j+1}'] = assignment_id
                
        
        
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
        
        for j, (file_name, ext) in enumerate( [f for file in files if (f := file.split('.',1)) and f[-1] in settings[FILE_EXTS] and dir.lower() in f[0].lower()] ): 

            # update progress bar --------------------------------
            progress = (j+1)/total_files
            progress /= total_tasks
            progress += (i+len(settings[ASSIGNMENTS])+2)/total_tasks
            progress *= 100
            progressBar(progress, f'{dir}: Uploading {file_name}')
            # ----------------------------------------------------
            
            file_path = os.path.join(root_dir, dir, f'{file_name}.{ext}')
            file_id = canvasAPI.uploadFile(course_id,file_path).json()['id']
            
            file_data = {
                "name":file_name,
                "parent_folder_id" : parent_folder_id
            }
            
            canvasAPI.updateFile(file_id, file_data)
            IDs['Files'][file_name] = file_id
            
    
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