import requests

class CanvasAPI:

    def __init__(self, login_token):

        self.ub_url = 'https://bridgeport.instructure.com/api/v1/'

        self.token = login_token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def get(self, url):
        return requests.get(url=url, headers=self.headers)

    # Assignments

    Assignment_Data = {
        "assignment[name]" : "Assignment 1", # str
        "assignment[points_possible]" : 10, # int
        "assignment[grading_type]": "letter_grade", # str : pass_fail, percent, letter_grade, gpa_scale, points, not_graded
        "assignment[grading_standard_id]": 456312, # int
        "assignment[due_at]" : "2022-07-01T23:59:00-06:00", # str : ISO 8601 formatted date and time
        "assignment[lock_at]" : "2022-07-01T23:59:00-06:00", # str : ISO 8601 formatted date and time
        "assignment[unlock_at]" : "2022-07-01T23:59:00-06:00", # str : ISO 8601 formatted date and time
        "assignment[description]" : "description", #str
        "assignment[assignment_group_id]" : 12345, # int
        "assignment[published]" : True # boolean
    }
    Grade_Data = {
        "comment[text_comment]" : "∀ ε > 0 in limit definition, NOT Let ε > 0 be given!\n-5 points", # str
        "submission[posted_grade]" : "95", # str : can take formats such as "92.5", "84%", "-A", "pass", "fail", "complete", "incomplete"
        "submission[excuse]" : True, # boolean
    }

    def getAllAssignments(self, course_id,per_page=50,data=dict(), response = False):
        full_path = f'{self.ub_url}courses/{course_id}/assignments?per_page={per_page}'
        res = requests.get(url=full_path,headers=self.headers,params=data)

        return res if response else res.json()

    def createAssignment(self, course_id, assignment_data):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/'
        return requests.post(url=full_path,headers=self.headers,params=assignment_data)

    def createAssignmentWithFile(self, course_id, assignment_data, file_path):
        response = self.uploadFile(course_id,file_path).json()
        file_id = response['id']
        file_name = response['filename']
        file_preview = f'<p><a class="instructure_file_link instructure_scribd_file auto_open" title="{file_name}" href="https://bridgeport.instructure.com/courses/{course_id}/files/{file_id}?wrap=1" target="_blank" rel="noopener" data-api-endpoint="{self.ub_url}courses/{course_id}/files/{file_id}" data-api-returntype="File">{file_name}</a></p>'
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

    def getSubmission(self, course_id, assignment_id, student_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}'
        return requests.get(url=full_path,headers=self.headers).json()

    def getAllSubmissions(self, course_id, assignment_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/{assignment_id}/submissions'
        return requests.get(url=full_path,headers=self.headers).json()

    def getAssignment(self, course_id, assignment_id):
        full_path = f'{self.ub_url}courses/{course_id}/assignments/{assignment_id}'
        return requests.get(url=full_path,headers=self.headers).json()



    # Groups

    Group_Data = {
        "name" : "group 1", # str
        "group_weight" : 25, # int : %
        "rules" : "drop_lowest:1\ndrop_highest:2\n" # str : rule1:value\nrule2:value\n...
    }

    def getCourseGroups(self, course_id, response = False):
        full_path = f'{self.ub_url}courses/{course_id}/assignment_groups/'
        res = requests.get(url=full_path,headers=self.headers)
        return res if response else res.json()

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

    # Modules

    Module_Data ={
        "module[name]" : "name", # str
        "module[unlock_at]" : "2011-10-21T18:48Z", # str DateTime in ISO 8601 format
        "module[position]" : 3, # int
        "module[require_sequential_progress]" : True, # boolean
        "module[prerequisite_module_ids][]" : "123\n456\n", # str : position value must be greater than prerequisite modules
        "module[publish_final_grade]" : True, # boolean
    }

    def createModule(self, course_id, module_data):
        full_path = f'{self.ub_url}courses/{course_id}/modules'
        return requests.post(url=full_path,headers=self.headers, params=module_data)

    def getModules(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/modules'
        return requests.get(url=full_path,headers=self.headers).json()

    def updateModule(self, course_id, module_id, module_data):
        full_path = f'{self.ub_url}courses/{course_id}/modules/{module_id}'
        return requests.put(url=full_path,headers=self.headers, params=module_data)

    def deleteModule(self, course_id, module_id):
        full_path = f'{self.ub_url}courses/{course_id}/modules/{module_id}'
        return requests.delete(url=full_path,headers=self.headers)

    # Module Items

    Item_Data = {
        "module_id" : 123, # int
        "position" : 1, # int
        "title" : "Title", # str
        "type" : "Assignment", # str : Assignment, Quiz, File, Page, Discussion, SubHeader, ExternalUrl, ExternalTool
        "content_id" : 123, # int : id of assignment, quiz, file, ect. for this item
        "page_url" : "Url", # str : for page type items
        "external_url" : "Url", # str : for external type items
        "completion_requirement" : {"type":"min_score","min_score":10,"completed":True}, # dict
        "published" : True, # boolean
    }

    def createModuleItem(self, course_id, module_id, item_data):
        full_path = f'{self.ub_url}courses/{course_id}/modules/{module_id}/items'
        return requests.post(url=full_path,headers=self.headers, params=item_data)

    def getModuleItems(self, course_id, module_id):
        full_path = f'{self.ub_url}courses/{course_id}/modules/{module_id}/items'
        return requests.get(url=full_path,headers=self.headers).json()

    def updateModuleItem(self, course_id, module_id, item_id, item_data):
        full_path = f'{self.ub_url}courses/{course_id}/modules/{module_id}/items/{item_id}'
        return requests.put(url=full_path,headers=self.headers, params=item_data)

    def deleteModuleItem(self, course_id, module_id, item_id):
        full_path = f'{self.ub_url}courses/{course_id}/modules/{module_id}/items/{item_id}'
        return requests.delete(url=full_path,headers=self.headers)

    # Quizzes

    Quiz_Data = {
        "quiz[title]" : "Title", # str
        "quiz[description]" : "Description", # str
        "quiz[quiz_type]" : "practice_quiz", # str : practice_quiz, assignment, graded_survey, survey
        "quiz[assignment_group_id]" : 123, # int
        "quiz[time_limit]" : 60, # int in minutes, None = no time limit
        "quiz[shuffle_answers]" : True, # boolean
        "quiz[hide_results]" : "always", # str : always, until_after_last_attempt
        "quiz[show_correct_answers]" : True, # boolean
        "quiz[allowed_attempts]" : 2, # int
        "quiz[scoring_policy]" : "keep_highest", # str : keep_highest, keep_latest
        "quiz[cant_go_back]" : True, # boolean
        "quiz[access_code]" : "Access Code", # str
        "quiz[due_at]" : "2011-10-21T18:48Z", # str DateTime in ISO 8601 format
        "quiz[lock_at]" : "2011-10-21T18:48Z", # str DateTime in ISO 8601 format
        "quiz[unlock_at]" : "2011-10-21T18:48Z", # str DateTime in ISO 8601 format
        "quiz[published]" : True, # boolean
    }

    def createQuiz(self, course_id, quiz_data):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes'
        return requests.post(url=full_path,headers=self.headers, params=quiz_data)

    def getQuizzes(self, course_id):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes'
        return requests.get(url=full_path,headers=self.headers).json()

    def updateQuiz(self, course_id, quiz_id, quiz_data):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes/{quiz_id}'
        return requests.put(url=full_path,headers=self.headers,params=quiz_data)

    def deleteQuiz(self, course_id, quiz_id):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes/{quiz_id}'
        return requests.delete(url=full_path,headers=self.headers)

    # Quiz Questions

    Question_Data = {
        "question[question_name]" : "Name", # str
        "question[question_text]" : "Text", # str
        "question[quiz_group_id]" : 123, # int
        "question[position]" : 1, # int
        "question[points_possible]" : 5, # int
        "question[answers]" : {}, # dict : Answer data
        "question[question_name]" : "Name", # str
        "question[question_type]" : "calculated_question"
        # str : calculated_question, essay_question, fill_in_multiple_blanks_question,
        #       matching_question, multiple_answers_question, multiple_choice_question,
        #       multiple_dropdowns_question, numerical_question, short_answer_question,
        #       true_false_question
    }
    Answer_Data = {
        "answer_text" : "Answer", # str
        "answer_weight" : 100, # int : correct = 100, incorrect = 0
        "text_after_answers" : " is the capital of Utah.", # str : Used in missing word questions.  The text to follow the missing word
        "answer_match_left" : "Salt Lake City", # str : Used in matching questions
        "answer_match_right" : "Utah", # str : Used in matching questions, correct answer for answer_match_left
        "matching_answer_incorrect_matches" : "Nevada\nCalifornia\nWashington\n", # str : incorrect answers for answer_match_left
        "numerical_answer_type" : "exact_answer", # str : exact_answer, range_answer, precision_answer
        "exact" : 42, # int : exact_answer
        "margin" : 0, # int : exact_answer, margin of error allowed for exact answer
        "approximate" : 1234600.0, # int : precision_answer
        "precision" : 4, # int : required percision for precision_answer
        "start" : 1, # int : range_answer, inclusive
        "end" : 10, # int : range_answer, inclusive
    }

    def createQuizQuestions(self, course_id, quiz_id, question_data):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes/{quiz_id}/questions'
        return requests.post(url=full_path,headers=self.headers, params=question_data)

    def getQuizQuestions(self, course_id, quiz_id):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes/{quiz_id}/questions'
        return requests.get(url=full_path,headers=self.headers).json()

    def updateQuizQuestions(self, course_id, quiz_id, question_id, question_data):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}'
        return requests.put(url=full_path,headers=self.headers,params=question_data)

    def deleteQuizQuestions(self, course_id, quiz_id, question_id):
        full_path = f'{self.ub_url}courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}'
        return requests.delete(url=full_path,headers=self.headers)

    # Files

    File_Data_FOR_UPLOADING = {
        "name" : "file 1", # str
        "parent_folder_path" : "folder name", # str
    }
    File_Data_FOR_UPDATING = {
        "name" : "file 1", # str
        "parent_folder_id" : 6156165, # str or int
    }

    def getFiles(self, course_id,per_page=50, response = False):
        full_path = f'{self.ub_url}courses/{course_id}/files?per_page={per_page}'
        res =  requests.get(url=full_path,headers=self.headers)

        return res if response else res.json()

    def getFile(self, file_id):
        full_path = f'{self.ub_url}files/{file_id}'
        return requests.get(url=full_path,headers=self.headers).json()

    def getFolders(self, course_id, response = False):
        full_path = f'{self.ub_url}courses/{course_id}/folders/'
        res =  requests.get(url=full_path,headers=self.headers)

        return res if response else res.json()

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

        if 300 <= response.status_code <= 399:
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

    # Tabs

    Tab_Data = {
        "id": "context_external_tool_153670",
        "html_url": "/courses/1865191/external_tools/153670",
        "full_url": "https://bridgeport.instructure.com/courses/1865191/external_tools/153670",
        "position": 22, # int
        "hidden": True, # boolean
        "visibility": "admins", # str : public, members, admins, none
        "label": "Studio", # str
        "type": "external",
        "url": "https://bridgeport.instructure.com/api/v1/courses/1865191/external_tools/sessionless_launch?id=153670&launch_type=course_navigation"
    }

    def getTabs(self, course_id):
        full_path = f"{self.ub_url}courses/{course_id}/tabs"
        return requests.get(url=full_path,headers=self.headers).json()

    def updateTab(self, course_id, tab_id, tab_data):
        full_path = f"{self.ub_url}courses/{course_id}/tabs/{tab_id}"
        return requests.put(url=full_path,headers=self.headers,params=tab_data)

    # Grading Scale

    Scale_Data = {
        'title' : 'String',
        'grading_scheme_entry[][name]' : 'A-',
        'grading_scheme_entry[][value]' : 90
    }

    def createGradingScale(self, course_id, scale_data):
        full_path = f"{self.ub_url}courses/{course_id}/grading_standards"
        return requests.post(url=full_path,headers=self.headers, params=scale_data)

    def getGradingScales(self, course_id):
        full_path = f"{self.ub_url}courses/{course_id}/grading_standards"
        return requests.get(url=full_path,headers=self.headers).json()

    #! does not work, canvas might not let you delete w/ api
    # They do not provide any documentation on deleting grade scales
    def deleteGradingScale(self, course_id, scale_id):
        full_path = f'https://bridgeport.instructure.com/courses/1865191/grading_standards/{scale_id}'
        data = {'_method':'DELETE'}
        return requests.post(url=full_path,headers= self.headers | data)

    Course_Data = {
        'course[grading_standard_id]' : 134564
    }

    def updateCourseSettings(self, course_id, course_data):
        full_path = f"{self.ub_url}courses/{course_id}"
        return requests.put(url=full_path,headers=self.headers,params=course_data)
