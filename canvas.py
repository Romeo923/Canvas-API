import sys
import pandas as pd
import requests
import json
import os

with open("config.json") as f:
    config = json.load(f)

token = config["login_token"]
root = config["root"]
course_data = config["course_data"]

ub_url = f'https://bridgeport.instructure.com/api/v1/'
headers = {"Authorization": f"Bearer {token}"}

def createAssignment(course_id, data):
    full_path = f'{ub_url}courses/{course_id}/assignments/'
    return requests.post(url=full_path,headers=headers,params=data)

def uploadFile(course_id, name, path, data):
    full_path = f'{ub_url}courses/{course_id}/files'
    
    # prepares canvas for file upload
    response = requests.post(url=full_path,headers=headers,params=data)
    output = response.json()
    
    # gets upload path and upload parameter from canvas
    upload_url = output['upload_url']
    upload_params = output['upload_params']
    
    # file to be uploaded
    file = {'file': open(path,'rb')}
    
    # sends file to given upload path with given parameters
    response = requests.post(url=upload_url, params=upload_params, files=file)
    
    if response.status_code >= 300 and response.status_code <= 399: 
        # if response code is 3XX, another api request must be made

        location = response.json()['Location']
        response = requests.post(url=location,headers=headers)
    
    # changes name of file in canvas

    # file_id = response.json()['id']

    # params = {
    #     'name':f'{name}.pdf'
    # }
    # print(file_id)
    # print(params)

    # response = requests.put(f'{full_path}/{file_id}',headers=headers,params=params)
    # print(response.reason)

    return response

def getCanvasGroups(course_id):
    full_path = f'{ub_url}courses/{course_id}/assignment_groups/'
    return requests.get(url=full_path,headers=headers)

def updateCanvasGroups(course_id, group_data):
    for group in group_data:
        full_path = f"{ub_url}courses/{course_id}/assignment_groups/{group_data[group]['id']}"
        data = {
            "name":group,
            "group_weight":group_data[group]['group_weight'],
            "rules":group_data[group]['rules']
        }
        requests.put(url=full_path,headers=headers,params=data)

def updateLocalGroups(course_id):
    full_path = f'{ub_url}courses/{course_id}/assignment_groups/'
    course_name = (course for course in os.listdir(root) if course_data[course]['id'] == course_id)
    course_name = next(course_name)
    current_group_data = course_data[course_name]["group_data"]
    response = requests.get(url=full_path,headers=headers)
    canvas_group_data = response.json()
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

def updateTabs(course_id):
    full_path = f"{ub_url}courses/{course_id}/update_nav"

def cloneDir():
    
    courses = os.listdir(root)
    for course in courses:

        course_id = course_data[course]['id']
        groups = os.listdir(f'{root}\\{course}')
        group_data = course_data[course]["group_data"]

        # enables group weights
        requests.put(url = f'{ub_url}courses/{course_id}',headers=headers,params={"course[apply_assignment_group_weights]":True})

        for group in groups:
            
            if group not in group_data:
                
                group_data = updateLocalGroups(course_id)
                
                if group not in group_data:
                    
                    temp_group_data = {
                        'name':group
                    }

                    full_path = f'{ub_url}courses/{course_id}/assignment_groups/'
                    temp_group = requests.post(url=full_path,headers=headers,params=temp_group_data).json()
                    
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
                        response = uploadFile(course_id,file,f'{root}\\{course}\\{group}\\{assignment}\\{file}',{'name':file,'parent_folder_path':group})
                        file_id = response.json()['id']
                        file_preview = f'<p><a class="instructure_file_link instructure_scribd_file auto_open" title="{file}" href="https://bridgeport.instructure.com/courses/{course_id}/files/{file_id}?wrap=1" target="_blank" rel="noopener" data-api-endpoint="https://bridgeport.instructure.com/api/v1/courses/{course_id}/files/{file_id}" data-api-returntype="File">{file}</a></p>'
                        data['assignment[description]'] = file_preview
                        break

                createAssignment(course_id,data)

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