import sys
import os
from Utils import *
from canvasAPI import CanvasAPI

os.chdir('1865191/')

canvasAPI, course_id, all_settings, inp = loadSettings()
course_settings = all_settings[course_id]

def applyCommand(commands):
    match commands:
        case [['-',*flags], *args, ['-',*flags2], _]:
            print(f'Matched multiple set of commands with primary Flags: {flags} and primary Arguments: {args}\nAnd Additional Flags: {flags2} and Aditional Arguments {_}')
        case [['-', *flags], *args]:
            print(f'Matched 1 set of commands with flags: {flags} anf Arguments: {args}')
        case _:
            print('did not match')

def main(dir, name, flags):

    if '-r' in flags:
        action = "overwrite"
        
    elif '-ra':
        action = "rename"
        
    else:
        print('\nError: No flag given.\nEnter flag "-r" to replace or "-ra" to rename and upload.\n')
        sys.exit(0)
    
    file_path = os.path.join(os.getcwd(), dir, name)
    
    parent_folder_id = course_settings['IDs']['Folders'][dir]
    
    id = canvasAPI.uploadFile(course_id,file_path).json()['id']
    file_data = {
        "name":name[:-4],
        "parent_folder_id":parent_folder_id,
        "on_duplicate" : action
    }
    response = canvasAPI.updateFile(id, file_data)
    print(response)
    print(response.json())
    file_name = response.json()['display_name']
    
    course_settings['IDs']['Files'][file_name] = id
    all_settings[course_id] = course_settings
    save(all_settings)
    
    
if __name__ == "__main__":
    
    _, *commands = sys.argv
    commands = ['-r', 'Hmk-1']
    # main(commands)
    # applyCommand(commands)