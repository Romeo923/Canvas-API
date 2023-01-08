from Utils import *
import os
import pandas as pd
import threading
from inp import Inp
from canvasAPI import CanvasAPI

class Course:

    def __init__(self, canvasAPI: CanvasAPI, course_id: str, root_dir: str, inp: Inp):
        self.api = canvasAPI # canvasAPI object, handles all api calls
        self.course_id = course_id # course id for current course
        self.root_dir = root_dir # path to course directory
        self.inp = inp # Inp object, handles all reading and writing to inp.json

    def initCourse(self):
        ASSIGNMENTS, FILES, FILE_EXTS, GRADING_SCALE, TABS, CLASS_SCHEDULE, *other_settings = self.inp

        assignments = self.inp[ASSIGNMENTS]
        files = self.inp[FILES]
        file_exts = self.inp[FILE_EXTS]
        grading_scale = self.inp[GRADING_SCALE]
        my_tabs = self.inp[TABS]
        schedule = self.inp[CLASS_SCHEDULE]

        canvas_tabs = self.api.getTabs(self.course_id)

        assignment_amount = 0
        for assignment in assignments:
            if 'amount' in assignments[assignment]:
                assignment_amount += assignments[assignment]['amount']
            else:
                assignment_amount += len(os.listdir(os.path.join(self.root_dir, assignment)))

        file_amount = 0
        for file in files:
            file_amount += len(os.listdir(os.path.join(self.root_dir, file)))

        total_tasks = len(canvas_tabs) + assignment_amount + file_amount + 1

        self.progressBar, self.overrideProgress = progressBar(total_tasks)

        self.api.enableGroupWeights(self.course_id)

        tasks = [
            self._initTabs,
            self._initGradeScales,
            self._initAssignments,
            self._initFiles
        ]
        task_args = [
            (canvas_tabs, my_tabs),
            (grading_scale,),
            (assignments, schedule, file_exts),
            (files, file_exts)
        ]

        threads = [threading.Thread(target=task,args=arg) for task, arg in zip(tasks, task_args)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


        self.save()
        self.overrideProgress(-1)
        self.progressBar("Done...")
        print_stderr('\n')

    def _initTabs(self, canvas_tabs, my_tabs):
        #* update each tab's visibility and position

        visible = [tab for tab in canvas_tabs if tab['label'] in my_tabs]
        for tab in visible : tab['hidden'] = False
        visible.sort(key=lambda tab : my_tabs.index(tab['label']))
        hidden = [tab for tab in canvas_tabs if tab['label'] not in my_tabs]
        for tab in hidden : tab['hidden'] = True

        for i, tab in enumerate(visible+hidden):

            self.progressBar("Adjusting Tabs")
            tab['position'] = i + 1
            self.api.updateTab(self.course_id, tab['id'], tab)

    def _initGradeScales(self, grading_scale):
        #* creates grading scales
        self.progressBar(f'Updating Grading Scheme')
        scale_title = 'TEST Grading Scale'
        scale_data = [ ('title', scale_title) ]
        canvas_schemes = [scheme['title'] for scheme in self.api.getGradingScales(self.course_id)]

        if scale_title not in canvas_schemes:

            for i, grade in enumerate(grading_scale):

                self.progressBar("Creating Grade Scales")

                scale_data.append(('grading_scheme_entry[][name]', grade))
                scale_data.append(('grading_scheme_entry[][value]', grading_scale[grade]))


            scale_id = self.api.createGradingScale(self.course_id, scale_data).json()['id']
            self.api.updateCourseSettings(self.course_id,{'course[grading_standard_id]': scale_id})

    def _initAssignments(self, assignments, schedule, file_exts):
        #* inits assignments
        for i, dir in enumerate(assignments):

            self.progressBar(f'{dir}: Begining Uploads')
            self.overrideProgress(-1)

            dir_settings = assignments[dir]

            no_overlap = dir_settings['no_overlap']
            overlap_dates = []
            for overlap in no_overlap:
                overlap_dates += generateDates(self.inp['Assignments'][overlap]['start_date'],self.inp['Assignments'][overlap]['end_date'],self.inp['Assignments'][overlap]['interval'],self.inp['Class Schedule']['days'],self.inp['Class Schedule']['holy_days'],self.inp['Assignments'][overlap]['amount'])

            group_data = {
                "name" : dir,
                "group_weight" : dir_settings['group_weight']
            }

            group_rules = {"rules" : dir_settings['rules']}

            #* Assignment w/File
            if dir_settings['file_upload']:
                id = self.initGroup(group_data)

                path = os.path.join(self.root_dir, dir)
                files = naturalSort(os.listdir(path))
                total_files = len(files)

                folder_data = {
                    "name" : dir_settings['parent_folder'],
                    "parent_folder_path" : ""
                }

                parent_folder_id = self.createFolder(dir, folder_data)
                holy_days = schedule['holy_days']

                dates = generateDates(
                    dir_settings['start_date'],
                    dir_settings['end_date'],
                    dir_settings['interval'],
                    schedule['days'],
                    holy_days,
                    total_files,
                    overlap_dates
                )

                # create each assignment, upload file, attach file to assignment
                for j, (file_name, ext) in enumerate( uploading := [f for file in files if (f := file.split('.',1)) and f[-1] in file_exts and dir.lower() in f[0].lower()] ):

                    if j+1 > len(dates):
                        print_stderr(f'\nAssignments have exceed end date.\nCould not upload: {uploading[j+2:]}\n')
                        break

                    self.progressBar(f'{dir}: Uploading {file_name}')

                    assignment_data = {
                        "assignment[name]" : file_name,
                        "assignment[points_possible]" : dir_settings['max_points'],
                        "assignment[grading_type]": "points",
                        "assignment[published]": dir_settings['published'],
                        "assignment[due_at]" : dates[j],
                        "assignment[assignment_group_id]" : id,
                        "assignment[submission_types][]": "online_upload"
                    }

                    file_data = {
                        "name":file_name,
                        "parent_folder_id": parent_folder_id
                    }

                    file_path = os.path.join(self.root_dir, dir, f'{file_name}.{ext}')

                    self.uploadAssignmentFile(assignment_data, file_data, file_path)

            #* Assignment w/o File
            else:

                id = self.initGroup(group_data)
                holy_days = schedule['holy_days']

                dates = generateDates(
                    dir_settings['start_date'],
                    dir_settings['end_date'],
                    dir_settings['interval'],
                    schedule['days'],
                    holy_days,
                    dir_settings['amount'],
                    overlap_dates
                )

                # Creates the specified number of Assignments
                for j in range(dir_settings['amount']):

                    if j+1 > len(dates):
                        print_stderr(f"Assignments have exceed end date.{' '*50}\nCould not upload: {dir}'s {j+1}-{dir_settings['amount']}\n")
                        self.overrideProgress(dir_settings['amount'] - j)
                        break

                    self.progressBar(f'{dir}: Uploading {dir}-{j+1}')
                    # ----------------------------------------------------

                    assignment_data = {
                        "assignment[name]" : f'{dir}-{j+1}',
                        "assignment[points_possible]" : dir_settings['max_points'],
                        "assignment[grading_type]": "points",
                        "assignment[published]": dir_settings['published'],
                        "assignment[due_at]" : dates[j],
                        "assignment[assignment_group_id]" : id,
                    }

                    self.uploadAssignment(assignment_data)
            self.editGroup(id, group_rules)

    def _initFiles(self, file_settings, file_exts):

        #* inits files
        for i, dir in enumerate(file_settings):
            dir_settings = file_settings[dir]

            path = os.path.join(self.root_dir, dir)
            files = naturalSort(os.listdir(path))

            folder_data = {
                "name" : dir_settings['parent_folder'],
                "parent_folder_path" : ""
            }
            parent_folder_id = self.createFolder(dir, folder_data)

            #* uploads each file

            for j, (file_name, ext) in enumerate( [f for file in files if (f := file.split('.',1)) and f[-1] in file_exts and dir.lower() in f[0].lower()] ):

                self.progressBar(f'{dir}: Uploading {file_name}')

                file_data = {
                    "name": file_name,
                    "parent_folder_id" : parent_folder_id
                }

                file_path = os.path.join(self.root_dir, dir, f'{file_name}.{ext}')
                self.uploadFile(file_path, file_data)

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

    def resetInp(self):
        self.inp.reset()
        print_stderr('\ninp.json reset...\n')

    def save(self):
        self.inp.save()

    def initGroup(self, group_data: dict) -> int:
        id = self.api.createGroup(self.course_id, group_data).json()['id']
        name = group_data['name']
        self.inp['IDs']['Groups'][name] = id
        return id

    def editGroup(self, group_id: int | str, group_data:dict):
        return self.api.updateGroup(self.course_id, group_id, group_data)

    def uploadAssignment(self, data: dict):
        response = self.api.createAssignment(self.course_id, data)
        aid = response.json()['id']
        name = data["assignment[name]"]
        self.inp['IDs']['Assignments'][name] = aid

    def uploadFile(self, path: str, data: dict):
        response = self.api.uploadFile(self.course_id, path)
        file_id = response.json()['id']
        response = self.api.updateFile(file_id, data).json()
        name = response['display_name']
        self.inp['IDs']['Files'][name] = file_id
        return response

    def createFolder(self, dir, data: dict):
        folder_id = None
        if data['name'] is not None:
            folder_id = self.api.createFolder(self.course_id,data).json()['id']
        self.inp['IDs']['Folders'][dir] = folder_id
        return folder_id

    def uploadAssignmentFile(self, assignment_data: dict, file_data: dict, path: str):
        response, file_id = self.api.createAssignmentWithFile(self.course_id, assignment_data, path)
        self.api.updateFile(file_id, file_data)

        assignment_name = assignment_data["assignment[name]"]
        assignment_id = response.json()['id']
        file_name = file_data['name']
        self.inp['IDs']['Assignments'][assignment_name] = assignment_id
        self.inp['IDs']['Files'][file_name] = file_id

    def editAssignment(self, name: str, data: dict):
        aid = self.inp['IDs']['Assignments'][name]
        return self.api.updateAssignment(self.course_id, aid, data)

    #TODO optimize
    def shiftAssignments(self, name, date):
        curr_dir = os.getcwd().split(separator)[-1]
        if curr_dir not in self.inp['Assignments']:
            print_stderr(f'\nError: {curr_dir} is not the group directory for {name}\nPlease change working directory\n')

        interval = self.inp['Assignments'][curr_dir]['interval']
        end_date = self.inp['Assignments'][curr_dir]['end_date']
        no_overlap = self.inp['Assignments'][curr_dir]['no_overlap']
        days, holy_days = self.inp['Class Schedule']
        overlap_dates = []
        for overlap in no_overlap:
            overlap_dates += generateDates(self.inp['Assignments'][overlap]['start_date'],self.inp['Assignments'][overlap]['end_date'],self.inp['Assignments'][overlap]['interval'],self.inp['Class Schedule'][days],self.inp['Class Schedule'][holy_days],self.inp['Assignments'][overlap]['amount'])
        canvas_assignments = self.api.getAllAssignments(self.course_id,data={'order_by':'due_at'},per_page=100)
        if len(canvas_assignments) == 100: print_stderr('\nWarning! 100 assignments have been pulled from canvas.\nDue to pagination, not all assignments may have been pulled.\n\n')
        shifting = [(assignment['name'], assignment['id'], assignment['due_at']) for assignment in canvas_assignments if assignment['assignment_group_id'] == self.inp['IDs']['Groups'][curr_dir]]
        for i, assignment in enumerate(shifting):
            if assignment[0] == name:
                break
        shifting = shifting[i:]
        new_dates = generateDates(date,end_date,interval,self.inp['Class Schedule'][days],self.inp['Class Schedule'][holy_days],len(shifting),overlap_dates)
        if len(shifting) > len(new_dates):
            remove = shifting[len(new_dates):]
            shifting = shifting[:len(new_dates)]
            for assignment in remove:
                self.deleteAssignment(assignment[0])
                print_stderr(f'Removed Assignment: {assignment[0]}')

        for i, assignment in enumerate(shifting):
            self.editAssignment(assignment[0],{'assignment[due_at]':new_dates[i]})

    def downloadAssignmentSubmissions(self, name: str):
        assignment_id = self.inp['IDs']['Assignments'][name]
        submissions = self.api.getAllSubmissions(self.course_id,assignment_id)
        count = 0
        for submission in submissions:
            if 'attachments' not in submission: continue
            student_id = submission['user_id']
            for attachment in submission['attachments']:
                submission_url = attachment['url']
                download(submission_url,f'{student_id}.pdf',f'./submissions/{name}')
                count += 1

        print_stderr(f'\n{count} submissions have been download to ./submissions/{name}/\n')

    #? potentially unnecessary
    def editFile(self, data):
        name = data['name']
        file_id = self.inp['IDs']['Files'][name]
        self.api.updateFile(file_id, data)

    def deleteAssignment(self, name: str):
        aid = self.inp['IDs']['Assignments'][name]
        del self.inp['IDs']['Assignments'][name]
        return self.api.deleteAssignment(self.course_id, aid)

    def deleteFile(self, file_name: str):
        fid = self.inp['IDs']['Files'][file_name]
        del self.inp['IDs']['Files'][file_name]
        return self.api.deleteFile(fid)

    def deleteAssignmentFile(self, name: str):
        return self.deleteAssignment(name), self.deleteFile(name)

    def deleteFolder(self, folder_name: str):
        fid = self.inp['IDs']['Folders'][folder_name]
        del self.inp['IDs']['Folders'][folder_name]
        return self.api.deleteFile(fid)

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
                self.inp['IDs']['Assignments'][name] = assignment['id']
                return True

        files = self.api.getFiles(self.course_id)
        while len(files) == size:
            size += 50
            files = self.api.getFiles(self.course_id, size)

        for file in files:
            if name == file['display_name']:
                self.inp['IDs']['Files'][name] = file['id']
                return True

        self.save()
        return False

    def gradeAssignment(self, student_id, assignment, grade):
        grade_data = {
            "submission[posted_grade]" : str(grade),
        }
        assignment_id = self.inp['IDs']['Assignments'][assignment]
        self.api.gradeAssignment(self.course_id,assignment_id,student_id,grade_data)

    #TODO optimize
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
                    current_grade = self.api.getSubmission(self.course_id, self.inp['IDs']['Assignments'][assignment], student)['grade']
                except:
                    print_stderr(f'\nFailed to retrieve data for student: {student}\nMake sure {student} is enrolled in course {self.course_id} on canvas.\n')
                    return

                if current_grade is not None:
                    current_grade = int(current_grade)

                    if not override:
                        print_stderr(f'\nAssignment "{assignment}" has already been graded.\nTo replace grades, enter {GRADE} true\nAborting...\n')
                        return
                    if new_grade < current_grade:
                        print_stderr(f'\nError: Grade for student {student} will be lowered from {current_grade} to {new_grade} for Assignment "{assignment}".\nEnter grades manually.\nAborting...\n')
                        return

        # post grades and update maximun points for each assignment
        progress_bar, progress_override = progressBar(len(submission_data))
        for assignment, student_id, grade, points in submission_data:
            self.editAssignment(assignment,{"assignment[points_possible]" : points})
            self.gradeAssignment(student_id, assignment, grade)
            progress_bar(f'Grading Assignment: {assignment} for Student: {student_id: <30}')

        progress_override(-1)
        progress_bar(f"Grading Complete!{' '*50}\n")
