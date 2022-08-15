import sys
import os
from Utils import *
from canvasAPI import CanvasAPI

help = """
FLAGS:

Flags   | Info            | Type         | Inputs                     | Status
-----   | ----            | ----         | ------                     | ------
-u      | upload          | command      | None                       | Done
-r      | replace/edit    | command      | None                       | Done
-D      | delete          | command      | None                       | (In progress)
-i      | index duplicate | modifier     | None                       | Done
        | upload          |              |                            | 
-a      | assignment      | classifier   | Assignment Name            | Done
-f      | file            | classifier   | File Name (include .pdf)   | Done
-d      | date            | data         | mm/dd/yyyy                 | Done
-p      | points          | data         | int                        | Done

-help   | list all flags  | help         | None
"""

canvasAPI, course_id, settings, all_settings, root_dir = loadSettings()
inp = os.path.join(root_dir,'inp.json')
root_dir = os.path.join(root_dir,course_id)

curr_dir = os.getcwd().split(separator)[-1]
IDs = all_settings[course_id]['IDs']

def applyCommand(commands, kwargs):
    match [list(command) if command[0] == '-' else command for command in commands]:
        
        case [['-','h','e','l','p'], *_]:
            print()
            print(help)
            print()
            sys.exit()
        
        case [['-', *flags], *args]:
            
            if len(args) == 0:
                print('No input arguments given.\nEnter -help to see flag data and reqired inputs')
                sys.exit()
            full_name, *rest = args
            full_name = full_name.split('.',1)
            name = full_name[0]
            ext = '.' + full_name[-1]
            args = rest

            #* Handles Command Flags
            #* Determines api task and generates input data
            action, data, input_data = generateAction(flags, name, ext)
            
            data |= kwargs
            left_over = [flag for flag in flags if flag not in 'urDiaf']
            
            
            #? potentially unnecessary after adding kwargs
            for flag in left_over:
                
                match flag:
                    
                    case 'd':
                        date, *rest = args
                        args = rest
                        days, hdays = settings['Class Schedule']
                        data["assignment[due_at]"] = formatDate(date,0,settings['Class Schedule'][days],settings['Class Schedule'][hdays],1)[0]
                    
                    case 'p':
                        points, *rest = args
                        args = rest
                        data["assignment[points_possible]"] = points
            
            action(*input_data, secondary_data = data)
            save(all_settings,inp)
                    
        case _:
            print('No flags given or Impropper format\nEnter -help for a list of flags')
                        
def generateAction(flags, name, ext):
    data = {}
    input_data = []

    cflags = {flag: True if flag in flags else False for flag in "urDiaf"}
            
    match cflags:
        
        #* Uploads NEW Assignment w/ File
        case {'u':True, 'a': True, 'f': True}:
            input_data.append(course_id)
            input_data.append(data)
            input_data.append(os.path.join(os.getcwd(),name+ext))
            fid = IDs["Folders"][curr_dir]
            data["assignment[name]"] = name
            data["assignment[assignment_group_id]"] = IDs['Groups'][curr_dir]
            
            def temp(*input_data, secondary_data):
                assignment_response, file_id = canvasAPI.createAssignmentWithFile(*input_data)
                
                secondary_data['name'] = name
                secondary_data["parent_folder_id"] = fid
                canvasAPI.updateFile(file_id,secondary_data)
                assignment_id = assignment_response.json()['id']
                IDs['Assignments'][name] = assignment_id
                IDs['Files'][name] = file_id
            
            action = temp
                        
        
        #* Uploads NEW Assignment
        case {'u':True, 'a': True}:
            
            def temp(*input_data, secondary_data):
                response = canvasAPI.createAssignment(*input_data)
                IDs['Assignments'][name] = response.json()['id']
            
            action = temp
            input_data.append(course_id)
            input_data.append(data)
            data["assignment[name]"] = name
            data["assignment[assignment_group_id]"] = IDs['Groups'][curr_dir]
        
        #* Uploads File 
        #! Indexes name if duplicate is found
        case {'u':True, 'f': True, 'i': True}:           
            
            input_data.append(course_id)
            input_data.append(os.path.join(os.getcwd(),name+ext))
            fid = IDs["Folders"][curr_dir]
            
            def temp(*input_data, secondary_data):
                response = canvasAPI.uploadFile(*input_data)
                file_id = response.json()['id']
                
                secondary_data["on_duplicate"] = "rename"
                secondary_data['name'] = name
                secondary_data["parent_folder_id"] = fid
                
                canvasAPI.updateFile(file_id,secondary_data)
                IDs['Files'][name] = response.json()['id']
            
            action = temp
            
            
        #* Uploads NEW File
        case {'u':True, 'f': True}:
            
            if name in IDs['Files']:
                print('\nFile already exists.\nEnter flag -i to upload with indexing or use flag -r to replace/edit instead of -u\n')
                sys.exit()
            
            input_data.append(course_id)
            input_data.append(os.path.join(os.getcwd(),name+ext))            
            fid = IDs["Folders"][curr_dir]
            
            def temp(*input_data, secondary_data):
                response = canvasAPI.uploadFile(*input_data)
                file_id = response.json()['id']
                
                secondary_data['name'] = name
                secondary_data["parent_folder_id"] = fid
                
                canvasAPI.updateFile(file_id,secondary_data)
                IDs['Files'][name] = response.json()['id']
            
            action = temp
            

        #* Edits Assignment
        case {'r':True, 'a': True}:
            
            def temp(*input_data, secondary_data):
                canvasAPI.updateAssignment(*input_data)
            
            action = temp
            aid = IDs['Assignments'][name]
            input_data.append(course_id)
            input_data.append(aid)
            input_data.append(data)
        
        #* Edits File
        #! WILL Replace File w/ Same Name
        case {'r':True, 'f': True}:
            
            input_data.append(course_id)
            input_data.append(os.path.join(os.getcwd(),name+ext))
            fid = IDs["Folders"][curr_dir]
            
            def temp(*input_data, secondary_data):
                response = canvasAPI.uploadFile(*input_data)
                file_id = response.json()['id']
                
                secondary_data["on_duplicate"] = "overwrite"
                secondary_data['name'] = name
                secondary_data["parent_folder_id"] = fid
                
                canvasAPI.updateFile(file_id,secondary_data)
                IDs['Files'][name] = response.json()['id']
            
            action = temp
            

        #* Delete Assignment and File
        case {'D':True, 'a': True, 'f':True}:
            def temp (course_id, assignment_id, file_id, secondary_data):
                canvasAPI.deleteAssignment(course_id,assignment_id),
                canvasAPI.deleteFile(file_id)
            
            action = temp
            aid = IDs['Assignments'][name]
            fid = IDs['Files'][name]
            
            input_data.append(course_id)
            input_data.append(aid)
            input_data.append(fid)
            
            del IDs['Assignments'][name]
            del IDs['Files'][name]
        
        #* Delete Assignment
        case {'D':True, 'a': True}:
            def temp(*input_data, secondary_data):
                canvasAPI.deleteAssignment(*input_data)
            
            action = temp
            aid = IDs['Assignments'][name]
            input_data.append(course_id)
            input_data.append(aid)
            del IDs['Assignments'][name]
            
        
        #* Delete File
        case {'D':True, 'f':True}:
            def temp(*input_data, secondary_data):
                canvasAPI.deleteFile(*input_data)
            
            action = temp
            fid = IDs['Files'][name]
            input_data.append(course_id)
            input_data.append(fid)                
            del IDs['Files'][name]
                        
        case _:
            print("\nImporper format or no flags given.\nEnter -help to beiw list of flags\n")
            
    return action, data, input_data

def main():
    
    _, *args = sys.argv
    
    kwargs = dict(arg.split('=') for arg in args if '=' in arg)
    commands = [arg for arg in args if '=' not in arg]
    
    # commands = ['-uf', 'hmk-1.pdf','10']
    # commands = ['-help']
    
    applyCommand(commands, kwargs)
    print('done...')
    
    
    
if __name__ == "__main__":
    main()
    