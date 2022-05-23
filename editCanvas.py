import json
import sys
import os
import datetime
from canvasAPI import CanvasAPI

os.chdir('1865191/')
with open("inp.json") as f:
    settings = json.load(f)

token = settings["login_token"]
canvasAPI = CanvasAPI(token)
course_id = 1865191

def save(data):
    with open("inp.json", 'w') as f:
        json.dump(data, f, indent= 2)

def main(dir, name, flags):
    # file_id = settings['IDs']['Files'][name[:-4]]

    if '-r' in flags:
        action = "overwrite"
        
    elif '-ra':
        action = "rename"
        
    else:
        print('\nError: No flag given.\nEnter flag "-r" to replace or "-ra" to rename and upload.\n')
        sys.exit(0)
    
    file_path = os.path.join(os.getcwd(), dir, name)
    
    parent_folder_id = settings['IDs']['Folders'][dir]
    
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
    
    settings['IDs']['Files'][file_name] = id
    save(settings)
    
    
if __name__ == "__main__":
    
    # _, dir, name, *flags = sys.argv
    dir = 'Hmk'
    name = 'hmk-1.pdf'
    flags = ['-r']
    main(dir, name, flags)
    