from urllib import response
import requests

class CanvasAPI:

    def __init__(self, login_token):
        
        self.ub_url = 'https://bridgeport.instructure.com/api/v1/'
        
        self.token = login_token
        headers = {"Authorization": f"Bearer {self.token}"}
    
    # Assignments
    
    def createAssignment(self, course_id, assignment_data):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/'
        return requests.post(url=full_path,headers=self.headers,params=assignment_data)

    def updateAssignment(self, course_id, assignment_data):
        full_path = f"{self.ub_url}courses/{course_id}/assignments/{assignment_data['id']}"
        return requests.put(url=full_path,headers=self.headers,params=assignment_data)

    def deleteAssignment(self, course_id, assignment_id):
        full_path = f"{self.ub_url}courses/{course_id}/assignments/{assignment_id}"
        return requests.delete(url=full_path,headers=self.headers)

    # Files
    
    def uploadFile(self, course_id, name, path, file_data):
        full_path = f'{self.ub_url}courses/{course_id}/files'
        
        # prepares canvas for file upload
        response = requests.post(url=full_path,headers=self.headers,params=file_data)
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
            response = requests.post(url=location,headers=self.headers)

        return response

    # Groups
    
    def getCourseGroups(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignment_groups/'
        return requests.get(url=full_path,headers=self.headers).json()

    def createGroup(self, course_id, group_data):
        full_path = f'{self.ub_url}courses/{course_id}/assignment_groups/'
        return requests.post(url=full_path,headers=self.headers,params = group_data)
    
    def updateGroup(self, course_id, group_data):
        full_path = f"{self.ub_url}courses/{course_id}/assignment_groups/{group_data['id']}"
        return requests.put(url=full_path,headers=self.headers,params=group_data)

    def deleteGroup(self, course_id, group_id):
        full_path = f"{self.ub_url}courses/{course_id}/assignment_groups/{group_id}"
        return requests.delete(url=full_path,headers=self.headers)
    
    def enableGroupWeights(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}'
        return requests.put(url = full_path, headers=self.headers, params={"course[apply_assignment_group_weights]":True})
        
    def disableGroupWeights(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}'
        return requests.put(url = full_path, headers=self.headers, params={"course[apply_assignment_group_weights]":False})
    
    # Tabs
    
    def updateTab(self, course_id, tab_data):
        full_path = f"{self.ub_url}courses/{course_id}/update_nav"