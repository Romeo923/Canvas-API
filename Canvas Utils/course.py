from Utils import *
import os
import pandas as pd
from multiprocessing.pool import ThreadPool
import threading
from inp import Inp
from canvasAPI import CanvasAPI
import yaml
from tqdm import tqdm

class Course:
    def __init__(self, canvasAPI: CanvasAPI, course_id: str, course_dir: str, inp: Inp):
        self.api = canvasAPI # canvasAPI object, handles all api calls
        self.course_id = course_id # course id for current course
        self.course_dir = course_dir # path to course directory
        self.inp = inp # Inp object, handles all reading and writing to inp.yaml
        self._errors = list()

    def initCourse(self):
        ASSIGNMENTS, QUIZZES, FILES, FILE_EXTS, GRADING_SCALE, TABS, CLASS_SCHEDULE, *_ = self.inp

        assignments = self.inp[ASSIGNMENTS]
        quizzes = self.inp[QUIZZES]
        files = self.inp[FILES]
        file_exts = self.inp[FILE_EXTS]
        grading_scale = self.inp[GRADING_SCALE]
        my_tabs = self.inp[TABS]
        schedule = self.inp[CLASS_SCHEDULE]

        canvas_tabs = self.api.getTabs(self.course_id)
        self.api.enableGroupWeights(self.course_id)

        self._initTabs(canvas_tabs, my_tabs)
        self._initGradeScales(grading_scale)
        self._initAssignments(assignments, schedule, file_exts)
        self._initQuizzes(quizzes, schedule)
        self._initFiles(files, file_exts)

        self.save()
        print_stderr('\n')
        if self._errors:
            print_stderr(f'{len(self._errors)} error(s) occurred during upload:')
            [print_stderr(error) for error in self._errors]
            print_stderr('\n')

    def _initTabs(self, canvas_tabs, my_tabs):
        #* update each tab's visibility and position

        visible = [tab for tab in canvas_tabs if tab['label'] in my_tabs]
        for tab in visible : tab['hidden'] = False
        visible.sort(key=lambda tab : my_tabs.index(tab['label']))
        hidden = [tab for tab in canvas_tabs if tab['label'] not in my_tabs]
        for tab in hidden : tab['hidden'] = True

        tablist = [(i, tab) for i, tab in enumerate(visible+hidden)]
        def _uplaodTab(args):
            i, tab = args
            tab['position'] = i + 1
            self.api.updateTab(self.course_id, tab['id'], tab)
            return tab['label']

        with ThreadPool() as pool:
            tasks = tqdm(pool.imap_unordered(_uplaodTab, tablist), total=len(tablist))
            for task in tasks:
                tasks.set_description(f'Adjusted {task} Tab')

    def _initGradeScales(self, grading_scale):
        #* creates grading scales
        scale_title = 'TEST Grading Scale'
        scale_data = [ ('title', scale_title) ]
        canvas_schemes = [scheme['title'] for scheme in self.api.getGradingScales(self.course_id)]

        if scale_title not in canvas_schemes:
            print('\nUploading Grading Scales...')
            for grade in grading_scale:

                scale_data.append(('grading_scheme_entry[][name]', grade))
                scale_data.append(('grading_scheme_entry[][value]', grading_scale[grade]))


            scale_id = self.api.createGradingScale(self.course_id, scale_data).json()['id']
            self.api.updateCourseSettings(self.course_id,{'course[grading_standard_id]': scale_id})
            print('Upload Complete!\n')

    def _initAssignments(self, assignments, schedule, file_exts):
        #* inits assignments

        def _uploadAssignment(dir):

            dir_settings = assignments[dir]

            no_overlap = dir_settings['no_overlap']
            dates = generateUploadDates(dir_settings, schedule)
            overlap_gen = (generateUploadDates(assignments[overlap], schedule) for overlap in no_overlap)
            overlap_dates = [date for overlap in overlap_gen for date in overlap]
            upload_dates = (formatDate(date) for date in dates if date not in overlap_dates)

            group_data = {
                "name" : dir,
                "group_weight" : dir_settings['group_weight']
            }
            group_rules = {"rules" : dir_settings['rules']}
            id = self.initGroup(group_data)

            assignment_data = {
                "assignment[points_possible]" : dir_settings['max_points'],
                "assignment[grading_type]": "points",
                "assignment[published]": dir_settings['published'],
                "assignment[assignment_group_id]" : id,
            }

            #* Assignment w/File
            if dir_settings['file_upload']:

                path = os.path.join(self.course_dir, dir)
                files = naturalSort(os.listdir(path))

                folder_data = {
                    "name" : dir_settings['parent_folder'],
                    "parent_folder_path" : ""
                }

                parent_folder_id = self.createFolder(dir, folder_data)

                #* create each assignment, upload file, attach file to assignment
                uploading = (f for file in files if (f := file.split('.',1)) and f[-1] in file_exts and dir.lower() in f[0].lower())
                for file in uploading:
                    file_name, ext = file
                    try:
                        date = next(upload_dates)
                    except StopIteration:
                        self._errors.append(f'Assignments have exceed end date.\nCould not upload: {[file, *uploading]}')
                        break

                    assignment_data["assignment[name]"] = file_name
                    assignment_data["assignment[submission_types][]"] = ["on_paper","online_upload"]
                    assignment_data["assignment[due_at]"] = date

                    file_data = {
                        "name":f'{file_name}.{ext}',
                        "parent_folder_id": parent_folder_id
                    }

                    file_path = os.path.join(self.course_dir, dir, f'{file_name}.{ext}')

                    self.uploadAssignmentFile(assignment_data, file_data, file_path)

            #* Assignment w/o File
            else:

                # Creates the specified number of Assignments
                for i in range(dir_settings['amount']):
                    try:
                        date = next(upload_dates)
                    except StopIteration:
                        self._errors.append(f"Assignments have exceed end date.\nCould not upload: {dir}'s {i+1}-{dir_settings['amount']}")
                        break

                    assignment_data["assignment[name]"] = f'{dir}-{i+1}'
                    assignment_data["assignment[submission_types][]"] = ["on_paper"]
                    assignment_data["assignment[due_at]"] = date

                    self.uploadAssignment(assignment_data)
            self.editGroup(id, group_rules)
            return dir

        with ThreadPool() as pool:
            tasks = tqdm(pool.imap_unordered(_uploadAssignment, assignments), total=len(assignments))
            for task in tasks:
                tasks.set_description(f'Uploaded Assignments for {task}')
        # [_uploadAssignment(assignment) for assignment in assignments]

    def _initQuizzes(self, quiz_settings, schedule):
        with open(os.path.join(self.inp.root_dir, 'quizzes.yaml'), 'r') as f:
            quiz_yaml = yaml.safe_load(f)

        _, _, *quizzes = quiz_yaml

        no_overlap = quiz_settings['no_overlap']
        dates = generateUploadDates(quiz_settings, schedule)
        overlap_gen = (generateUploadDates(self.inp['Assignments'][overlap], schedule) for overlap in no_overlap)
        overlap_dates = [date for overlap in overlap_gen for date in overlap]
        upload_dates = (formatDate(date) for date in dates if date not in overlap_dates)

        def _uploadQuizzes(args):
            quiz, date = args
            gid = self.inp.IDs['Groups'][quiz_settings['group']]
            quiz_data = {
                "quiz[title]" : quiz,
                "quiz[description]" : quiz_yaml[quiz]['description'],
                "quiz[quiz_type]" : quiz_settings['quiz_type'],
                "quiz[assignment_group_id]" : gid,
                "quiz[time_limit]" : quiz_yaml[quiz]['time_limit'],
                "quiz[show_correct_answers]" : quiz_settings['show_correct_answers'],
                "quiz[shuffle_answers]" : quiz_settings['shuffle_answers'],
                "quiz[due_at]" : date,
                "quiz[published]" : quiz_settings['published'],
            }

            self.uploadQuiz(quiz_data)
            quiz_id = self.inp.IDs['Quizzes'][quiz]
            questions = quiz_yaml[quiz]['Questions']

            for question in questions:
                question_answers = questions[question]['Answers']
                answers = []
                for answer in question_answers:
                    answer_data = {
                        "text" : question_answers[answer]["answer_text"],
                        "weight" : 100 if question_answers[answer]['correct'] else 0
                    }

                    answers.append(answer_data)
                question_data = {
                    "question":{
                        "question_name" : questions[question]['question_name'],
                        "question_text" : questions[question]['question_text'],
                        "question_type" : questions[question]['question_type'],
                        # "position" : question,
                        "quiz_group_id" : None,
                        "points_possible" : questions[question]['points_possible'],
                        "answers" : answers
                    }

                }
                self.uploadQuizQuestion(quiz_id,question_data)
            return quiz

        with ThreadPool() as pool:
            tasks = tqdm(pool.imap_unordered(_uploadQuizzes, zip(quizzes, upload_dates)), total=len(quizzes))
            for task in tasks:
                tasks.set_description(f'Uploaded {task}')

    def _initFiles(self, file_settings, file_exts):

        #* inits files

        def _uploadFiles(dir):
            dir_settings = file_settings[dir]

            path = os.path.join(self.course_dir, dir)
            files = naturalSort(os.listdir(path))

            folder_data = {
                "name" : dir_settings['parent_folder'],
                "parent_folder_path" : ""
            }
            parent_folder_id = self.createFolder(dir, folder_data)

            #* uploads each file

            uploading = (file for file in files if (f := file.split('.',1)) and f[-1] in file_exts and dir.lower() in f[0].lower())
            for file in uploading:
                # tasks.set_description(f'{dir}: Uploading {file_name}')

                file_data = {
                    "name": file,
                    "parent_folder_id" : parent_folder_id
                }

                file_path = os.path.join(self.course_dir, dir, file)
                self.uploadFile(file_path, file_data)
            return dir

        with ThreadPool() as pool:
            tasks = tqdm(pool.imap_unordered(_uploadFiles, file_settings), total=len(file_settings))
            for task in tasks:
                tasks.set_description(f'Uploaded {task} Files')

    def syncCourse(self):

        def _sync(task, section):

            def syncTask():

                print_stderr(f'Syncing {section}...')
                task_response = task(self.course_id, response = True)
                task_data = task_response.json()
                task_links = task_response.links

                for element in task_data:
                    name = element['name'] if 'name' in element else element['display_name']
                    id = element['id']
                    self.inp.IDs[section][name] = id

                while 'next' in task_links:
                    task_response = self.api.get(task_links['next']['url'])
                    task_data = task_response.json()
                    task_links = task_response.links

                    for element in task_data:
                        name = element['name'] if 'name' in element else element['display_name']
                        id = element['id']
                        self.inp.IDs[section][name] = id

                print_stderr(f'{section} has been synced!')

            return syncTask

        tasks = [
            _sync(self.api.getCourseGroups, "Groups"),
            _sync(self.api.getAllAssignments, "Assignments"),
            _sync(self.api.getFiles, "Files"),
            _sync(self.api.getFolders, "Folders")
        ]

        threads = [threading.Thread(target=task) for task in tasks]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.inp.IDs['Folders']['sylbs'] = None
        self.save()

    def resetCourse(self):
        self.api.disableGroupWeights(self.course_id)

        def _del_assignments():
            assignments = self.api.getAllAssignments(self.course_id)
            print_stderr("deleting assignments")
            while len(assignments) > 0:
                for assignment in assignments:
                    self.api.deleteAssignment(self.course_id, assignment['id'])
                assignments = self.api.getAllAssignments(self.course_id)
            print_stderr(f"assignments deleted")

        def _del_quizzes():
            quizzes = self.api.getQuizzes(self.course_id)
            print_stderr("deleting quizzes")
            while len(quizzes) > 0:
                for quiz in quizzes:
                    self.api.deleteQuiz(self.course_id, quiz['id'])
                quizzes = self.api.getQuizzes(self.course_id)
            print_stderr(f"quizzes deleted")

        def _del_groups():
            groups = self.api.getCourseGroups(self.course_id)
            print_stderr('deleting groups')
            while len(groups) > 0:
                for group in groups:
                    self.api.deleteGroup(self.course_id, group['id'])
                groups = self.api.getCourseGroups(self.course_id)
            print_stderr(f"groups deleted")


        def _del_files():
            files = self.api.getFiles(self.course_id)
            print_stderr("deleting files")
            while len(files) > 0:
                for file in files:
                    self.api.deleteFile(file['id'])
                files = self.api.getFiles(self.course_id)
            print_stderr(f"files deleted")


        def _del_folders():
            folders = self.api.getFolders(self.course_id)
            print_stderr("deleting folders")
            while len(folders) > 1:
                for folder in folders:
                    self.api.deleteFolder(folder['id'])
                folders = self.api.getFolders(self.course_id)
            print_stderr(f"folders deleted")

        tasks = [
            _del_assignments,
            _del_quizzes,
            _del_groups,
            _del_files,
            _del_folders
        ]

        threads = [threading.Thread(target=task) for task in tasks]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        print_stderr('\nCanvas Reset...')

    def resetIDs(self):
        self.inp.reset()
        print_stderr('\nids.yaml reset...\n')

    def save(self):
        self.inp.save()

    def initGroup(self, group_data: dict) -> int:
        id = self.api.createGroup(self.course_id, group_data).json()['id']
        name = group_data['name']
        self.inp.IDs['Groups'][name] = id
        return id

    def editGroup(self, group_id: int | str, group_data:dict):
        return self.api.updateGroup(self.course_id, group_id, group_data)

    def uploadAssignment(self, data: dict):
        response = self.api.createAssignment(self.course_id, data)
        aid = response.json()['id']
        name = data["assignment[name]"]
        self.inp.IDs['Assignments'][name] = aid

    def uploadFile(self, path: str, data: dict):
        response = self.api.uploadFile(self.course_id, path)
        file_id = response.json()['id']
        response = self.api.updateFile(file_id, data).json()
        name = response['display_name']
        self.inp.IDs['Files'][name] = file_id
        return response

    def createFolder(self, dir, data: dict):
        folder_id = None
        if data['name'] is not None:
            folder_id = self.api.createFolder(self.course_id,data).json()['id']
        self.inp.IDs['Folders'][dir] = folder_id
        return folder_id

    def uploadAssignmentFile(self, assignment_data: dict, file_data: dict, path: str):
        response, file_id = self.api.createAssignmentWithFile(self.course_id, assignment_data, path)
        self.api.updateFile(file_id, file_data)

        assignment_name = assignment_data["assignment[name]"]
        assignment_id = response.json()['id']
        file_name = file_data['name']
        self.inp.IDs['Assignments'][assignment_name] = assignment_id
        self.inp.IDs['Files'][file_name] = file_id

    def editAssignment(self, name: str, data: dict):
        aid = self.inp.IDs['Assignments'][name]
        return self.api.updateAssignment(self.course_id, aid, data)

    def shiftAssignments(self, name, date):
        curr_dir = os.getcwd().split(separator)[-1]
        if curr_dir not in self.inp['Assignments']:
            print_stderr(f'\nError: {curr_dir} is not the group directory for {name}\nPlease change working directory\n')

        no_overlap = self.inp['Assignments'][curr_dir]['no_overlap']
        new_dates = generateUploadDates(self.inp['Assignments'][curr_dir], self.inp['Class Schedule'], start_date=date)
        overlap_gen = (generateUploadDates(self.inp['Assignments'][overlap], self.inp['Class Schedule']) for overlap in no_overlap)
        overlap_dates = [date for overlap in overlap_gen for date in overlap]
        upload_dates = (formatDate(date) for date in new_dates if date not in overlap_dates)

        canvas_assignments = self.api.getAllAssignments(self.course_id,data={'order_by':'due_at'},per_page=100)
        if len(canvas_assignments) == 100: print_stderr('\nWarning! 100 assignments have been pulled from canvas.\nDue to pagination, not all assignments may have been pulled.\n\n')
        shifting = ((assignment['name'], assignment['id'], assignment['due_at']) for assignment in canvas_assignments if assignment['assignment_group_id'] == self.inp.IDs['Groups'][curr_dir])
        for assignment in shifting:
            if assignment[0] == name: break

        for assignment, date in zip(shifting, upload_dates):
            self.editAssignment(assignment[0],{'assignment[due_at]':date})

        for  assignment in shifting:
            self.deleteAssignment(assignment[0])
            print_stderr(f'Removed Assignment: {assignment[0]}')

    def downloadAssignmentSubmissions(self, name: str, ext: str):
        assignment_id = self.inp.IDs['Assignments'][name]
        submissions_response = self.api.getAllSubmissions(self.course_id,assignment_id)
        submissions = submissions_response.json()
        submissions_links = submissions_response.links
        count = 0

        for submission in submissions:
            if 'attachments' not in submission: continue
            student_id = submission['user_id']
            for attachment in submission['attachments']:
                submission_url = attachment['url']
                download(submission_url,f'{student_id}.{ext}',f'./submissions/{name}')
                count += 1

        while 'next' in submissions_links:
            submissions_response = self.api.get(submissions_links['next']['url'])
            submissions = submissions_response.json()
            submissions_links = submissions_response.links

            for submission in submissions:
                if 'attachments' not in submission: continue
                student_id = submission['user_id']
                for attachment in submission['attachments']:
                    submission_url = attachment['url']
                    download(submission_url,f'{student_id}.{ext}',f'./submissions/{name}')
                    count += 1

        print_stderr(f'\n{count} submissions have been download to ./submissions/{name}/\n')

    def uploadQuiz(self, data: dict):
        quiz_response = self.api.createQuiz(self.course_id, data)
        quiz_id = quiz_response.json()['id']
        name = data["quiz[title]"]
        self.inp.IDs['Quizzes'][name] = quiz_id
        self.inp.IDs['Quizzes'][quiz_id] = {}

    def uploadQuizQuestion(self, quiz_id: int | str, data: dict):
        question_response = self.api.createQuizQuestion(self.course_id, quiz_id, data)
        question_id = question_response.json()
        question_id = question_id['id']
        name = data['question']["question_name"]
        self.inp.IDs['Quizzes'][quiz_id][name] = question_id

    # TODO: implement
    def deleteQuiz(self, name: str):
        quiz_id = self.inp.IDs['Quizzes'][name]
        del self.inp.IDs['Quizzes'][name]
        del self.inp.IDs['Quizzes'][quiz_id]
        return self.api.deleteQuiz(self.course_id, quiz_id)

    #? potentially unnecessary
    def editFile(self, data):
        name = data['name']
        file_id = self.inp.IDs['Files'][name]
        self.api.updateFile(file_id, data)

    def deleteAssignment(self, name: str):
        aid = self.inp.IDs['Assignments'][name]
        del self.inp.IDs['Assignments'][name]
        return self.api.deleteAssignment(self.course_id, aid)

    def deleteFile(self, file_name: str):
        fid = self.inp.IDs['Files'][file_name]
        del self.inp.IDs['Files'][file_name]
        return self.api.deleteFile(fid)

    def deleteAssignmentFile(self, name: str):
        return self.deleteAssignment(name), self.deleteFile(name)

    def deleteFolder(self, folder_name: str):
        fid = self.inp.IDs['Folders'][folder_name]
        del self.inp.IDs['Folders'][folder_name]
        return self.api.deleteFile(fid)

    # TODO: check quizzes
    def exists(self, name: str) -> bool:
        if self.inp.exists(name):
            return True

        size = 50
        assignments = self.api.getAllAssignments(self.course_id)
        while len(assignments) == size:
            size += 50
            assignments = self.api.getAllAssignments(self.course_id, size)

        for assignment in assignments:
            if name == assignment['name']:
                self.inp.IDs['Assignments'][name] = assignment['id']
                return True

        files = self.api.getFiles(self.course_id)
        while len(files) == size:
            size += 50
            files = self.api.getFiles(self.course_id, size)

        for file in files:
            if name == file['display_name']:
                self.inp.IDs['Files'][name] = file['id']
                return True

        self.save()
        return False

    def gradeAssignment(self, student_id, assignment, grade):

        if grade >= 0:
            grade_data = {
                "submission[posted_grade]" : str(grade),
            }
        else:
            grade_data = {
                "submission[excuse]" : True,
            }

        assignment_id = self.inp.IDs['Assignments'][assignment]
        self.api.gradeAssignment(self.course_id,assignment_id,student_id,grade_data)

    # TODO optimize
    #? move to canvas.py
    def grade(self, override = False):
        from canvas import GRADE
        try:
            grades = pd.read_csv('grades.csv',index_col=False)
        except FileNotFoundError:
            print_stderr('\nFailed to locate grades.csv\nPlease cd into the directory containing grades.csv\n')
            return

        id, *assignments = grades

        student_ids = [int(student_id) for student_id in grades[id][1:]]
        max_points = (int(grades[assignment][0]) for assignment in assignments)

        submission_data = [] # data to be submitted after confirming no issues with grade changes
        for assignment, points in zip(assignments,max_points):

            try:
                self.editAssignment(assignment, {"assignment[published]" : True})
            except:
                print_stderr(f'\nFailed to publish assignment: {assignment}.\nMake sure assignment exists before attempting to grade it.\n')
                return

            # format grade data and check for grading issues
            for i, student in enumerate(student_ids):
                new_grade = int(grades[assignment][i+1])
                submission_data.append( (assignment, student, new_grade, points) )

                try:
                    current_grade = self.api.getSubmission(self.course_id, self.inp.IDs['Assignments'][assignment], student)['grade']
                except:
                    print_stderr(f'\nFailed to retrieve data for student: {student}\nMake sure {student} is enrolled in course {self.course_id} on canvas.\n')
                    return

                if current_grade is not None:
                    current_grade = int(current_grade)

                    if not override:
                        print_stderr(f'\nAssignment "{assignment}" has already been graded.\nTo replace grades, enter {GRADE} true\nAborting...\n')
                        return
                    if 0 <= new_grade < current_grade:
                        print_stderr(f'\nError: Grade for student {student} will be lowered from {current_grade} to {new_grade} for Assignment "{assignment}".\nEnter grades manually.\nAborting...\n')
                        return

        # post grades and update maximun points for each assignment
        tasks = tqdm(submission_data)
        for assignment, student_id, grade, points in tasks:
            self.editAssignment(assignment,{"assignment[points_possible]" : points})
            self.gradeAssignment(student_id, assignment, grade)
            tasks.set_description(f'Grading Assignment: {assignment} for Student: {student_id: <30}')
