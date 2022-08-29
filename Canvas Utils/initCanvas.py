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
    i=0
    while len(assignments) > 0:
        print("deleting assignments",end='\r')
        for assignment in assignments:
            canvasAPI.deleteAssignment(course_id, assignment['id'])
            print(f"deleting assignments{'.'*(i%4)}   ",end='\r')
            i+=1
        assignments = canvasAPI.getAssignments(course_id)
    print(f"assignments deleted {' '*10}")
    
    groups = canvasAPI.getCourseGroups(course_id)
    while len(groups) > 0:
        print('deleting groups',end='\r')
        for group in groups:
            canvasAPI.deleteGroup(course_id, group['id'])
            print(f"deleting groups{'.'*(i%4)}   ",end='\r')
            i+=1
        groups = canvasAPI.getCourseGroups(course_id)
    print(f"groups deleted {' '*10}")
        

    files = canvasAPI.getFiles(course_id)
    while len(files) > 0:
        print("deleting files",end='\r')
        for file in files:
            canvasAPI.deleteFile(file['id'])
            print(f"deleting files{'.'*(i%4)}   ",end='\r')
            i+=1
        files = canvasAPI.getFiles(course_id)
    print(f"files deleted {' '*10}")
    
        
    folders = canvasAPI.getFolders(course_id)
    while len(folders) > 1:
        print("deleting folders",end='\r')
        for folder in folders:
            canvasAPI.deleteFolder(folder['id'])
            print(f"deleting folders{'.'*(i%4)}   ",end='\r')
            i+=1
        folders = canvasAPI.getFolders(course_id)
    print(f"folders deleted {' '*10}")
        
        
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
    
    
    #* update each tab's visibility and position
    
    visible = [tab for tab in canvas_tabs if tab['label'] in my_tabs]
    for tab in visible : tab['hidden'] = False
    visible.sort(key=lambda tab : my_tabs.index(tab['label']))
    hidden = [tab for tab in canvas_tabs if tab['label'] not in my_tabs]
    for tab in hidden : tab['hidden'] = True
    
    for i, tab in enumerate(visible+hidden):
        
        # update progress bar --------------------------------    
        progress = (i+1)/total_tabs
        progress /= total_tasks
        progress *= 100
        progressBar(progress,"Adjusting Tabs")
        # -------------------------------------

        tab['position'] = i + 1
        canvasAPI.updateTab(course_id, tab['id'], tab)
        

    #* creates grading scales
    scale_title = 'TEST Grading Scale'
    scale_data = [ ('title', scale_title) ]
    canvas_schemes = [scheme['title'] for scheme in canvasAPI.getGradingScales(course_id)]
    
    if scale_title not in canvas_schemes:
    
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
        
        no_overlap = dir_settings['no_overlap']
        overlap_dates = []
        for overlap in no_overlap:
            overlap_dates += generateDates(settings['Assignments'][overlap]['start_date'],settings['Assignments'][overlap]['end_date'],settings['Assignments'][overlap]['interval'],settings['Class Schedule']['days'],settings['Class Schedule']['holy_days'],settings['Assignments'][overlap]['amount'])
                
        
        #* Assignment w/File
        if dir_settings['file_upload']:
            id = initGroup(dir, dir_settings)
            
            path = os.path.join(root_dir, dir)
            files = naturalSort(os.listdir(path))
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
                holy_days, 
                total_files,
                overlap_dates
            )
            
            # create each assignment, upload file, attach file to assignment
            for j, (file_name, ext) in enumerate( uploading := [f for file in files if (f := file.split('.',1)) and f[-1] in settings[FILE_EXTS] and dir.lower() in f[0].lower()] ): 
                 
                if j+1 > len(dates):
                    print(f'\nAssignments have exceed end date.\nCould not upload: {uploading[j+2:]}\n')
                    break
                 
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
                    "assignment[grading_type]": "points",
                    "assignment[published]": dir_settings['published'],
                    "assignment[due_at]" : dates[j],
                    "assignment[assignment_group_id]" : id,
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
                holy_days, 
                dir_settings['amount'],
                overlap_dates
            )
            
            # Creates the specified number of Assignments
            for j in range(dir_settings['amount']):
                
                if j+1 > len(dates):
                    print(f"Assignments have exceed end date.{' '*50}\nCould not upload: {dir}'s {j+1}-{dir_settings['amount']}\n")
                    break
                
                # update progress bar --------------------------------
                progress = (j+1)/dir_settings['amount']
                progress /= total_tasks
                progress += (i+2)/total_tasks
                progress *= 100
                progressBar(progress, f'{dir}: Uploading {dir}-{j+1}')
                # ----------------------------------------------------
                
                assignment_data = {
                    "assignment[name]" : f'{dir}-{j+1}',
                    "assignment[points_possible]" : dir_settings['max_points'],
                    "assignment[grading_type]": "points",
                    "assignment[published]": dir_settings['published'],
                    "assignment[due_at]" : dates[j],
                    "assignment[assignment_group_id]" : id,
                }
                assignment_id = canvasAPI.createAssignment(course_id, assignment_data).json()['id']
                IDs['Assignments'][f'{dir}-{j+1}'] = assignment_id
                
                
                
        
        
    #* inits files
    for i, dir in enumerate(settings[FILES]):
        dir_settings = settings[FILES][dir]
        
        path = os.path.join(root_dir, dir)
        files = naturalSort(os.listdir(path))
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