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
-d      | delete          | command      | None                       | (In progress)
-i      | index duplicate | modifier     | None                       | Done
        | upload          |              |                            | 
-a      | assignment      | classifier   | Assignment Name            | Done
-f      | file            | classifier   | File Name (include .pdf)   | Done
-d      | date            | data         | mm/dd/yyyy                 | Done
-p      | points          | data         | int                        | Done

-help   list all flags  help         None
"""


os.chdir('1865191/Hmk')

canvasAPI, course_id, all_settings, settings, course_settings, inp_dir = loadSettings()
inp = os.path.join(inp_dir,'inp.json')
root_dir = os.path.join(inp_dir,course_id)

curr_dir = os.getcwd().split('\\')[-1]
IDs = course_settings['IDs']

def applyCommand(commands):
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
            name, *rest = args
            args = rest

            #* Handles Command Flags
            #* Determines api task and generates input data
            action, data, input_data = generateAction(flags, name)
                    
            left_over = [flag for flag in flags if flag not in 'uriaf']
            
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
            
            response = action(*input_data)
            if 'u' in flags:
                if 'a' in flags and 'f' in flags:
                    
                    assignment_response, file_id = response
                    
                    canvasAPI.updateFile(file_id,data)
                    assignment_id = assignment_response.json()['id']
                    
                    IDs['Assignments'][name[:-4]] = assignment_id
                    IDs['Files'][name[:-4]] = file_id
                
                elif 'a' in flags:
                    IDs['Assignments'][name] = response.json()['id']
                elif 'f' in flags:
                    
                    file_id = response.json()['id']
                    
                    canvasAPI.updateFile(file_id,data)
                    
                    IDs['Files'][name[:-4]] = response.json()['id']
                    
            save(all_settings,inp)
                    
        case _:
            print('No flags given or Impropper format\nEnter -help for a list of flags')
                        
def generateAction(flags, name):
    data = {}
    input_data = []

    cflags = {flag: True if flag in flags else False for flag in "urdiaf"}
            
    match cflags:
        
        #* Uploads NEW Assignment w/ File
        case {'u':True, 'a': True, 'f': True}:
            action = canvasAPI.createAssignmentWithFile
            input_data.append(course_id)
            input_data.append(data)
            input_data.append(os.path.join(os.getcwd(),name))
            fid = IDs["Folders"][curr_dir]
            data['name'] = name[:-4]
            data["parent_folder_id"] = fid            
            data["assignment[name]"] = name[:-4]
            data["assignment[assignment_group_id]"] = IDs['Groups'][curr_dir]
        
        #* Uploads NEW Assignment
        case {'u':True, 'a': True}:
            action = canvasAPI.createAssignment
            input_data.append(course_id)
            input_data.append(data)
            data["assignment[name]"] = name
            data["assignment[assignment_group_id]"] = IDs['Groups'][curr_dir]
        
        #* Uploads File 
        #! Indexes name if duplicate is found
        case {'u':True, 'f': True, 'i': True}:           
            action = canvasAPI.uploadFile
            input_data.append(course_id)
            input_data.append(os.path.join(os.getcwd(),name))
            fid = IDs["Folders"][curr_dir]
            data["on_duplicate"] = "rename"
            data['name'] = name[:-4]
            data["parent_folder_id"] = fid
        
        #* Uploads NEW File
        case {'u':True, 'f': True}:
            
            if name[:-4] in IDs['Files']:
                print('\nFile already exists.\nEnter flag -i to upload with indexing or use flag -r to replace/edit instead of -u\n')
                sys.exit()
            
            action = canvasAPI.uploadFile
            input_data.append(course_id)
            input_data.append(os.path.join(os.getcwd(),name))            
            fid = IDs["Folders"][curr_dir]
            data['name'] = name[:-4]
            data["parent_folder_id"] = fid
        
        #* Edits Assignment
        case {'r':True, 'a': True}:
            action = canvasAPI.updateAssignment
            aid = IDs['Assignments'][name]
            input_data.append(course_id)
            input_data.append(aid)
            input_data.append(data)
        
        #* Edits File
        #! WILL Replace File w/ Same Name
        case {'r':True, 'f': True}:
            action = canvasAPI.uploadFile
            input_data.append(course_id)
            input_data.append(os.path.join(os.getcwd(),name))
            fid = IDs["Folders"][curr_dir]
            data['name'] = name[:-4]
            data["parent_folder_id"] = fid
            data["on_duplicate"] = "overwrite"

        #* Delete Assignment and File
        # TODO Find Assignment ID and File ID
        # TODO Delete From Canvas 
        # TODO Delete From INP File
        case {'d':True, 'a': True, 'f':True}:
            pass
        
        #* Delete Assignment
        # TODO Find Assignment ID
        # TODO Delete From Canvas 
        # TODO Delete From INP File
        case {'d':True, 'a': True}:
            pass
        
        #* Delete File
        # TODO Find File ID
        # TODO Delete From Canvas 
        # TODO Delete From INP File
        case {'d':True, 'f':True}:
            pass                
                        
        case _:
            print("\nImporper format or no flags given.\nEnter -help to beiw list of flags\n")
            
    return action, data, input_data

def main():
    
    _, *commands = sys.argv
    
    # commands = ['-uf', 'hmk-1.pdf','10']
    # commands = ['-help']
    applyCommand(commands)
    print('done...')
    
    
    
if __name__ == "__main__":
    main()
    