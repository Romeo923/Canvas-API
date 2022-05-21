import requests

class CanvasAPI:

    def __init__(self, login_token):
        
        self.ub_url = 'https://bridgeport.instructure.com/api/v1/'
        
        self.token = login_token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # Assignments
    
    def getAssignments(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignments'
        return requests.get(url=full_path,headers=self.headers).json()
    
    def createAssignment(self, course_id, assignment_data):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/'
        return requests.post(url=full_path,headers=self.headers,params=assignment_data)

    def createAssignmentWithFile(self, course_id, assignment_data, file_path):
        response = self.uploadFile(course_id,file_path).json()
        file_id = response['id']
        file_name = response['filename']
        file_preview = f'<p><a class="instructure_file_link instructure_scribd_file auto_open" title="{file_name}" href="https://bridgeport.instructure.com/courses/{course_id}/files/{file_id}?wrap=1" target="_blank" rel="noopener" data-api-endpoint="https://bridgeport.instructure.com/api/v1/courses/{course_id}/files/{file_id}" data-api-returntype="File">{file_name}</a></p>'
        assignment_data['assignment[description]'] = file_preview
        return self.createAssignment(course_id,assignment_data), file_id   
    
    def updateAssignment(self, course_id, assignment_id, assignment_data):
        full_path = f"{self.ub_url}courses/{course_id}/assignments/{assignment_id}"
        return requests.put(url=full_path,headers=self.headers,params=assignment_data)

    def deleteAssignment(self, course_id, assignment_id):
        full_path = f"{self.ub_url}courses/{course_id}/assignments/{assignment_id}"
        return requests.delete(url=full_path,headers=self.headers)

    def gradeAssignment(self, course_id, assignment_id, student_id, grade_data):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}'
        return requests.put(url=full_path,headers=self.headers,params=grade_data)
    
    def getGrade(self, course_id, assignment_id, student_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}'
        return requests.get(url=full_path,headers=self.headers).json()
    
    # Files
    
    def getFiles(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/files'
        return requests.get(url=full_path,headers=self.headers).json()
    
    def getFile(self, file_id):
        full_path = f'{self.ub_url}files/{file_id}'
        return requests.get(url=full_path,headers=self.headers).json()
    
    def getFolders(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/folders/'
        return requests.get(url=full_path,headers=self.headers).json()
    
    def uploadFile(self, course_id, path):
        full_path = f'{self.ub_url}courses/{course_id}/files'
        
        # prepares canvas for file upload
        response = requests.post(url=full_path,headers=self.headers,params={"parent_folder_path":""})
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

    def updateFile(self, file_id, file_data):
        full_path = f'{self.ub_url}/files/{file_id}'
        return requests.put(url=full_path, headers=self.headers, params=file_data)

    def deleteFile(self, file_id):
        full_path = f'{self.ub_url}files/{file_id}'
        return requests.delete(url=full_path,headers=self.headers)
    
    def createFolder(self, course_id, folder_data):
        full_path = f'{self.ub_url}courses/{course_id}/folders'
        return requests.post(url=full_path,headers=self.headers,params=folder_data)
    
    def deleteFolder(self, folder_id):
        full_path = f'{self.ub_url}folders/{folder_id}'
        return requests.delete(url=full_path,headers=self.headers)
    
    # Groups
    
    def getCourseGroups(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignment_groups/'
        return requests.get(url=full_path,headers=self.headers).json()

    def createGroup(self, course_id, group_data):
        full_path = f'{self.ub_url}courses/{course_id}/assignment_groups/'
        return requests.post(url=full_path,headers=self.headers,params = group_data)
    
    def updateGroup(self, course_id, group_id, group_data):
        full_path = f"{self.ub_url}courses/{course_id}/assignment_groups/{group_id}"
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
    
    def getTabs(self, course_id):
        full_path = f"{self.ub_url}courses/{course_id}/tabs"
        return requests.get(url=full_path,headers=self.headers).json()
    
    def updateTab(self, course_id, tab_id, tab_data):
        full_path = f"{self.ub_url}courses/{course_id}/tabs/{tab_id}"
        return requests.put(url=full_path,headers=self.headers,params=tab_data)