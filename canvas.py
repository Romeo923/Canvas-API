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
    "assignment[due_at]" : "", # str
    "assignment[description]" : "description", #str
    "assignment[assignment_group_id]" : 12345, # int
    "assignment[published]" : True # boolean
}

Group Data:
{
    "name" : "group 1", # str
    "group_weight" : 25, # int %
    "rules" : "drop_lowest:1\ndrop_highest:2\n" # str rule1:value\nrule2:value\n...
}

File Data UPLOADING:
{
    "name" : "file 1", # str
    "parent_folder_path" : "folder name", # str
}
"""

with open("config.json") as f:
    config = json.load(f)

token = config["login_token"]
root = config["root"]
course_data = config["course_data"]

canvasAPI = CanvasAPI(token)

def updateCanvasGroups(course_id, group_data):
    for group in group_data:
        data = {
            "name":group,
            "group_weight":group_data[group]['group_weight'],
            "rules":group_data[group]['rules']
        }
        canvasAPI.updateGroup(course_id,data)

def updateLocalGroups(course_id):

    course_name = (course for course in os.listdir(root) if course_data[course]['id'] == course_id)
    course_name = next(course_name)
    current_group_data = course_data[course_name]["group_data"]
    
    canvas_group_data = canvasAPI.getCourseGroups(course_id)
    
    new_group_data = {
        canvas_group["name"]:{
            "group_weight":canvas_group["group_weight"],
            "default_points":10,
            "rules":canvas_group["rules"],
            "id":canvas_group["id"]
        } for canvas_group in canvas_group_data}
   
    for group in new_group_data:
        
        rules = ""
        for rule in new_group_data[group]["rules"]:
            rules += f'{rule}:{new_group_data[group]["rules"][rule]}\n'
        new_group_data[group]["rules"] = rules
        
        if group in current_group_data:
            new_group_data[group]["default_points"] = current_group_data[group]["default_points"]
    
    course_data[course_name]['group_data'] = new_group_data
    config['course_data'] = course_data
    
    with open("config.json",'w') as f:
        json.dump(config,f,indent=2)
    
    return new_group_data


def cloneDir():
    
    courses = os.listdir(root)
    for course in courses:

        course_id = course_data[course]['id']
        groups = os.listdir(f'{root}\\{course}')
        group_data = course_data[course]["group_data"]

        canvasAPI.enableGroupWeights(course_id)

        for group in groups:
            
            if group not in group_data:
                
                group_data = updateLocalGroups(course_id)
                
                if group not in group_data:
                    
                    temp_group_data = {
                        'name':group
                    }

                    
                    temp_group = canvasAPI.createGroup(course_id, temp_group_data).json()
                    
                    group_data = updateLocalGroups(course_id)

            group_id = group_data[group]['id']
            
            assignments = os.listdir(f'{root}\\{course}\\{group}')
            for assignment in assignments:

                data = {
                'assignment[name]': assignment,
                'assignment[points_possible]' : group_data[group]['default_points'],
                'assignment[published]' : False,
                'assignment[assignment_group_id]': group_data[group]['id']
                }
                file_data = os.listdir(f'{root}\\{course}\\{group}\\{assignment}')
                for file in file_data:
                    if '.pdf' in file:
                        response = canvasAPI.uploadFile(course_id, file, f'{root}\\{course}\\{group}\\{assignment}\\{file}', {'name':file,'parent_folder_path':group})
                        file_id = response.json()['id']
                        file_preview = f'<p><a class="instructure_file_link instructure_scribd_file auto_open" title="{file}" href="https://bridgeport.instructure.com/courses/{course_id}/files/{file_id}?wrap=1" target="_blank" rel="noopener" data-api-endpoint="https://bridgeport.instructure.com/api/v1/courses/{course_id}/files/{file_id}" data-api-returntype="File">{file}</a></p>'
                        data['assignment[description]'] = file_preview
                        break

                canvasAPI.createAssignment(course_id,data)

def main():

    # & C:/Users/Romeo/anaconda3/python.exe "c:/Users/Romeo/Desktop/Canvas API/canvas.py"  cmd shit
    
    try:
        arg = sys.argv[1]
        print(arg)
    except IndexError:
        pass

    # cloneDir()

    for course in course_data:
        course_id = course_data[course]['id']
        groups = os.listdir(f'{root}\\{course}')
        group_data = course_data[course]["group_data"]
        
        # updateLocalGroups(course_id)
        updateCanvasGroups(course_id,group_data)


if __name__ == "__main__":
    main()