import sys
import os
from Utils import *
from canvasAPI import CanvasAPI

help = """
FLAGS:

Flags   Info            Type         Inputs
-----   ----            ----         ------
-u      upload          command      None
-r      repost/edit     command      None
-i      index instead   modifier     None
        of override
-a      assignment      classifier   Assignment Name
-f      file            classifier   File Name (include .pdf)
-d      date            data         mm/dd/yyyy
-p      points          data         int
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
            
            data = {}
            input_data = []
            
            if len(args) == 0:
                print('No input arguments given.\nEnter -help to see flag data and reqired inputs')
                sys.exit()
            name, *rest = args
            args = rest
        
            if 'u' in flags:
                
                if 'a' in flags and 'f' in flags:
                    action = canvasAPI.createAssignmentWithFile
                    input_data.append(course_id)
                    input_data.append(data)
                    input_data.append(os.path.join(os.getcwd(),name))
                    data["assignment[name]"] = name
                    data["assignment[assignment_group_id]"] = IDs['Groups'][curr_dir]
                elif 'a' in flags:
                    action = canvasAPI.createAssignment
                    input_data.append(course_id)
                    input_data.append(data)
                    data["assignment[name]"] = name
                    data["assignment[assignment_group_id]"] = IDs['Groups'][curr_dir]
                elif 'f' in flags:
                    action = canvasAPI.uploadFile
                    input_data.append(course_id)
                    input_data.append(os.path.join(os.getcwd(),name))
                    data['name'] = name[:-4]
                else:
                    print('Impropper format, no upload classifier given')
                          
            elif 'r' in flags:
                                
                if 'a' in flags:
                    action = canvasAPI.updateAssignment
                    input_data.append(course_id)
                    aid = IDs['Assignments'][name]
                    input_data.append(aid)
                    input_data.append(data)
                elif 'f' in flags:
                    # TODO upload file, rename file
                    # requires upload and update methods
                    data["on_duplicate"] = "rename" if 'i' in flags else "overwrite"
                    action = canvasAPI.uploadFile
                    fid = IDs["Files"][name[:-4]]
                    data['name'] = name[:-4]
                    input_data.append(course_id)
                    input_data.append(os.path.join(os.getcwd(),name))
                else:
                    print('Impropper format, no upload classifier given')
                    
            else:
                print("Impropper format. Flags -u or -r must be included and cannot be combined.")
                sys.exit()
                    
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
                    
                    foid = IDs['Folders'][curr_dir]
                    assignment_response, file_id = response
                    canvasAPI.updateFile(
                        file_id,
                        {
                            "name":name[:-4], 
                            "parent_folder_id": foid
                        }
                    )
                    assignment_id = assignment_response.json()['id']
                    
                    IDs['Assignments'][name[:-4]] = assignment_id
                    IDs['Files'][name[:-4]] = file_id
                
                elif 'a' in flags:
                    IDs['Assignments'][name] = response.json()['id']
                elif 'f' in flags:
                    IDs['Files'][name[:-4]] = response.json()['id']
                    
            save(all_settings,inp)
                    
        case _:
            print('No flags given or Impropper format\nEnter -help for a list of flags')
            
            

def main():
    
    # _, *commands = sys.argv
    
    commands = ['-rfi', 'hmk-1.pdf']
    # commands = ['-help']
    applyCommand(commands)
    print('done...')
    
    
    
if __name__ == "__main__":
    main()
    