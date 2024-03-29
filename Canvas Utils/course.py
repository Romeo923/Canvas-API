from Utils import (
    download,
    formatDate,
    naturalSort,
    print_stderr,
    generateUploadDates,
    url_encode,
    separator,
)
import os
from glob import glob
import pandas as pd
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock
import threading
from inp import Inp
from canvasAPI import CanvasAPI
import yaml
from tqdm import tqdm


class Course:
    def __init__(self, canvasAPI: CanvasAPI, course_id: str, course_dir: str, inp: Inp):
        self.api = canvasAPI  # canvasAPI object, handles all api calls
        self.course_id = course_id  # course id for current course
        self.course_dir = course_dir  # path to course directory
        self.inp = inp  # Inp object, handles all reading and writing to inp.yaml
        self._errors: list[str] = list()

    def initCourse(self):
        (
            ASSIGNMENTS,
            QUIZZES,
            FILES,
            FILE_EXTS,
            GRADING_SCALE,
            TABS,
            CLASS_SCHEDULE,
            VIDEOS,
            *_,
        ) = self.inp

        assignments = self.inp[ASSIGNMENTS]
        quizzes = self.inp[QUIZZES]
        files = self.inp[FILES]
        file_exts = self.inp[FILE_EXTS]
        grading_scale = self.inp[GRADING_SCALE]
        my_tabs = self.inp[TABS]
        schedule = self.inp[CLASS_SCHEDULE]
        videos = self.inp[VIDEOS]

        self.api.groups.enableGroupWeights()

        self.reorderTabs(my_tabs)
        self._initGradeScales(grading_scale)
        self._initAssignments(assignments, schedule, file_exts)
        self._initQuizzes(quizzes, schedule)
        self._initFiles(files, file_exts)
        self._initVideos(videos)

        self.save()
        print_stderr("\n")

        if self._errors:
            print_stderr(f"{len(self._errors)} error(s) occurred during upload:")
            [print_stderr(error) for error in self._errors]
            print_stderr("\n")

    def _initGradeScales(self, grading_scale):
        # * creates grading scales
        scale_title = "TEST Grading Scale"
        scale_data: list[tuple[str, str]] = [("title", scale_title)]
        canvas_schemes = [scheme["title"] for scheme in self.api.getGradingScales()]

        if scale_title not in canvas_schemes:
            print("\nUploading Grading Scales...")
            for grade in grading_scale:
                scale_data.append(("grading_scheme_entry[][name]", grade))
                scale_data.append(
                    ("grading_scheme_entry[][value]", grading_scale[grade])
                )

            scale_id = self.api.createGradingScale(scale_data).json()["id"]
            self.api.updateCourseSettings({"course[grading_standard_id]": scale_id})
            print("Upload Complete!\n")

    def _initAssignments(self, assignments, schedule, file_exts):
        # * inits assignments

        def _uploadAssignment(dir):
            dir_settings = assignments[dir]

            no_overlap = dir_settings["no_overlap"]
            dates = generateUploadDates(dir_settings, schedule)
            overlap_gen = (
                generateUploadDates(assignments[overlap], schedule)
                for overlap in no_overlap
            )
            overlap_dates = [date for overlap in overlap_gen for date in overlap]
            upload_dates = (
                formatDate(date) for date in dates if date not in overlap_dates
            )

            group_data = {"name": dir, "group_weight": dir_settings["group_weight"]}
            group_rules = {"rules": dir_settings["rules"]}
            id = self.initGroup(group_data)

            assignment_data = {
                "assignment[points_possible]": dir_settings["max_points"],
                "assignment[grading_type]": "points",
                "assignment[published]": dir_settings["published"],
                "assignment[assignment_group_id]": id,
            }

            names = [f"{dir}-{i+1}" for i in range(dir_settings["amount"] or 0)]

            # * Assignment w/File
            if dir_settings["file_upload"]:
                path = os.path.join(self.course_dir, dir)
                dir_filter = "".join(
                    [f"[{x.lower()}{x.upper()}]" for x in dir if x.isalpha()]
                )
                filter = f"{dir_filter}[- ]*.*"
                filter2 = f"{dir_filter}.*"
                files = naturalSort(
                    glob(filter, root_dir=path) + glob(filter2, root_dir=path)
                )

                names = [
                    f[0]
                    for file in files
                    if (f := file.split(".", 1)) and f[-1] in file_exts
                ]

            for i, name in enumerate(names):
                try:
                    date = next(upload_dates)
                except StopIteration:
                    self._errors.append(
                        "Assignments have exceed end date.\n"
                        + f"Could not upload: {dir}'s {i+1}-{dir_settings['amount']}"
                    )
                    break

                assignment_data["assignment[name]"] = name
                assignment_data["assignment[submission_types][]"] = dir_settings['submit_type']
                assignment_data["assignment[allowed_extensions]"] = dir_settings['submit_ext']
                assignment_data["assignment[due_at]"] = date

                self.uploadAssignment(assignment_data)
            self.editGroup(id, group_rules)
            return dir

        with ThreadPool() as pool:
            tasks = tqdm(
                pool.imap_unordered(_uploadAssignment, assignments),
                total=len(assignments),
            )
            for task in tasks:
                tasks.set_description(f"Uploaded Assignments for {task}")
        # [_uploadAssignment(assignment) for assignment in assignments]

    def _initQuizzes(self, quiz_settings, schedule):
        path = os.path.join(self.inp.root_dir, self.inp.course_id, "quizzes.yaml")
        if not os.path.exists(path):
            return
        with open(path, "r") as f:
            quiz_yaml = yaml.safe_load(f)

        _, _, *quizzes = quiz_yaml

        no_overlap = quiz_settings["no_overlap"]
        dates = generateUploadDates(quiz_settings, schedule)
        overlap_gen = (
            generateUploadDates(self.inp["Assignments"][overlap], schedule)
            for overlap in no_overlap
        )
        overlap_dates = [date for overlap in overlap_gen for date in overlap]
        upload_dates = (formatDate(date) for date in dates if date not in overlap_dates)

        def _uploadQuizzes(args):
            quiz, date = args
            gid = self.inp.IDs["Groups"][quiz_settings["group"]]
            desc, time, *groups = quiz_yaml[quiz]

            quiz_data = {
                "quiz[title]": quiz,
                "quiz[description]": url_encode(quiz_yaml[quiz][desc]),
                "quiz[quiz_type]": quiz_settings["quiz_type"],
                "quiz[assignment_group_id]": gid,
                "quiz[time_limit]": quiz_yaml[quiz][time],
                "quiz[show_correct_answers]": quiz_settings["show_correct_answers"],
                "quiz[shuffle_answers]": quiz_settings["shuffle_answers"],
                "quiz[due_at]": date,
                "quiz[published]": quiz_settings["published"],
            }

            self.uploadQuiz(quiz_data)
            quiz_id = self.inp.IDs["Quizzes"][quiz]

            for group in groups:
                group_data = {
                    "quiz_groups": [
                        {
                            "name": group,
                            "pick_count": quiz_yaml[quiz][group]["pick_count"],
                            "question_points": quiz_yaml[quiz][group][
                                "points_per_question"
                            ],
                        }
                    ]
                }

                # TODO self.createQuizGroup()
                res = self.api.quizzes.groups.create(quiz_id, group_data)
                data = res.json()
                group_id = data["quiz_groups"][0]["id"]
                questions = quiz_yaml[quiz][group]["questions"]

                for question in questions:
                    question_answers = questions[question]["Answers"]
                    answers = []
                    for answer in question_answers:
                        answer_data = {
                            "text": url_encode(question_answers[answer]["answer_text"]),
                            "weight": 100 if question_answers[answer]["correct"] else 0,
                        }

                        answers.append(answer_data)
                    question_data = {
                        "question": {
                            "question_name": questions[question]["question_name"],
                            "question_text": url_encode(
                                questions[question]["question_text"]
                            ),
                            "question_type": questions[question]["question_type"],
                            # "position" : question,
                            "quiz_group_id": group_id,
                            "points_possible": questions[question]["points_possible"],
                            "answers": answers,
                        }
                    }
                    self.uploadQuizQuestion(quiz_id, question_data)
            return quiz

        with ThreadPool() as pool:
            tasks = tqdm(
                pool.imap_unordered(_uploadQuizzes, zip(quizzes, upload_dates)),
                total=len(quizzes),
            )
            for task in tasks:
                tasks.set_description(f"Uploaded {task}")

    def _initFiles(self, file_settings, file_exts):
        # * inits files

        def _uploadFiles(dir):
            dir_settings = file_settings[dir]

            path = os.path.join(self.course_dir, dir)
            dir_filter = "".join(
                [f"[{x.lower()}{x.upper()}]" for x in dir if x.isalpha()]
            )
            filter = f"{dir_filter}[- ]*.*"
            filter2 = f"{dir_filter}.*"
            files = naturalSort(
                glob(filter, root_dir=path) + glob(filter2, root_dir=path)
            )

            folder_data = {
                "name": dir_settings["parent_folder"],
                "parent_folder_path": "",
            }
            parent_folder_id = self.createFolder(dir, folder_data)

            # * uploads each file

            uploading = (
                file
                for file in files
                if (f := file.split(".", 1)) and f[-1] in file_exts
            )
            for file in uploading:
                # tasks.set_description(f'{dir}: Uploading {file_name}')

                file_data = {"name": file, "parent_folder_id": parent_folder_id}

                file_path = os.path.join(self.course_dir, dir, file)
                data = self.uploadFile(file_path, file_data)

                name, _ = file.split(".", 1)
                if self.inp.existsAssignments(name):
                    file_id = data["id"]
                    file_name = data["filename"]
                    file_preview = f'<p><a class="instructure_file_link instructure_scribd_file auto_open" title="{file_name}" href="https://bridgeport.instructure.com/courses/{self.course_id}/files/{file_id}?wrap=1" target="_blank" rel="noopener" data-api-endpoint="{self.api.ub_url}/courses/{self.course_id}/files/{file_id}" data-api-returntype="File">{file_name}</a></p>'
                    self.editAssignment(name, {"assignment[description]": file_preview})

            return dir

        with ThreadPool() as pool:
            tasks = tqdm(
                pool.imap_unordered(_uploadFiles, file_settings),
                total=len(file_settings),
            )
            for task in tasks:
                tasks.set_description(f"Uploaded {task} Files")

    def _initVideos(self, videos):
        if not videos:
            return

        lock = Lock()

        def _attatchVideo(video):
            media_id = videos[video]
            display_media_tabs = "false"  # false = true for some reason
            display_download = "true"

            embed = f'<p><iframe class="lti-embed" style="width: 800px; height: 880px;" title="{video}" src="/courses/{self.course_id}/external_tools/retrieve?display=borderless&amp;url=https%3A%2F%2Fbridgeport.instructuremedia.com%2Flti%2Flaunch%3Fcustom_arc_display_download%3D{display_download}%26custom_arc_launch_type%3Dembed%26custom_arc_media_id%3D{media_id}%26custom_arc_start_at%3D0" width="800" height="880" allowfullscreen="allowfullscreen" webkitallowfullscreen="webkitallowfullscreen" mozallowfullscreen="mozallowfullscreen" allow="geolocation *; microphone *; camera *; midi *; encrypted-media *; autoplay *; clipboard-write *; display-capture *" data-studio-resizable="{display_media_tabs}" data-studio-tray-enabled="{display_media_tabs}" data-studio-convertible-to-link="true"></iframe></p>'

            if self.inp.existsAssignments(video):
                self.editAssignment(video, {"assignment[description]": embed})

            else:
                lock.acquire()
                if "Videos" not in self.inp.IDs["Groups"]:
                    group_data = {"name": "Videos", "group_weight": 0}
                    id = self.initGroup(group_data)
                else:
                    id = self.inp.IDs["Groups"]["Videos"]
                lock.release()

                data = {
                    "assignment[name]": video,
                    "assignment[points_possible]": 0,
                    "assignment[grading_type]": "not_graded",
                    "assignment[published]": True,
                    "assignment[assignment_group_id]": id,
                    "assignment[description]": embed,
                }
                self.uploadAssignment(data)

            return video

        with ThreadPool() as pool:
            tasks = tqdm(pool.imap_unordered(_attatchVideo, videos), total=len(videos))
            for task in tasks:
                tasks.set_description(f"Uploaded Video: {task}")

    def syncCourse(self):
        def _sync(items, section):
            def syncTask():
                print_stderr(f"Syncing {section}...")

                for item in items:
                    name = item["name"] if "name" in item else item["display_name"]
                    id = item["id"]
                    self.inp.IDs[section][name] = id

                print_stderr(f"{section} has been synced!")

            return syncTask

        tasks = [
            _sync(self.api.groups.listGenerator(), "Groups"),
            _sync(self.api.assignments.listGenerator(), "Assignments"),
            _sync(self.api.files.listGenerator(), "Files"),
            _sync(self.api.folders.listGenerator(), "Folders"),
        ]

        threads = [threading.Thread(target=task) for task in tasks]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.inp.IDs["Folders"]["sylbs"] = None
        self.save()

    def reorderTabs(self, tab_names: list[str]):
        # * update each tab's visibility and position

        canvas_tabs = list(self.api.tabs.listGenerator())
        tasks = tqdm(canvas_tabs)
        for tab in tasks:
            hidden = tab["label"] not in tab_names
            position = tab["position"] if hidden else tab_names.index(tab["label"]) + 1
            data = {"hidden": hidden, "position": position, "label": tab["label"]}

            self.api.tabs.edit(tab["id"], data)
            tasks.set_description(f"Adjusted '{tab['label']}' Tab")

    def resetCourse(self):
        self.api.groups.disableGroupWeights()

        def _del_assignments():
            print_stderr("deleting assignments")
            self.api.assignments.deleteAll()
            print_stderr("assignments deleted")

        def _del_quizzes():
            print_stderr("deleting quizzes")
            self.api.quizzes.deleteAll()
            print_stderr("quizzes deleted")

        def _del_groups():
            print_stderr("deleting groups")
            self.api.groups.deleteAll()
            print_stderr("groups deleted")

        def _del_files():
            print_stderr("deleting files")
            self.api.files.deleteAll()
            print_stderr("files deleted")

        def _del_folders():
            print_stderr("deleting folders")
            self.api.folders.deleteAll()
            print_stderr("folders deleted")

        tasks = [_del_assignments, _del_quizzes, _del_groups, _del_files, _del_folders]

        threads = [threading.Thread(target=task) for task in tasks]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        print_stderr("\nCanvas Reset...")

    def resetIDs(self):
        self.inp.reset()
        print_stderr("\nids.yaml reset...\n")

    def save(self):
        self.inp.save()

    def initGroup(self, group_data: dict) -> int:
        id = self.api.groups.create(group_data).json()["id"]
        name = group_data["name"]
        self.inp.IDs["Groups"][name] = id
        return id

    def editGroup(self, group_id: int | str, group_data: dict):
        return self.api.groups.edit(group_id, group_data)

    def uploadAssignment(self, data: dict):
        response = self.api.assignments.create(data)
        aid = response.json()["id"]
        name = data["assignment[name]"]
        self.inp.IDs["Assignments"][name] = aid

    def uploadFile(self, path: str, data: dict):
        response = self.api.files.create(path)
        file_id = response.json()["id"]
        response = self.api.files.edit(file_id, data).json()
        name = response["display_name"]
        self.inp.IDs["Files"][name] = file_id
        return response

    def createFolder(self, dir, data: dict):
        folder_id = None
        if data["name"] is not None:
            folder_id = self.api.folders.create(data).json()["id"]
        self.inp.IDs["Folders"][dir] = folder_id
        return folder_id

    def editAssignment(self, name: str, data: dict):
        aid = self.inp.IDs["Assignments"][name]
        return self.api.assignments.edit(aid, data)

    def shiftAssignments(self, name, date):
        curr_dir = os.getcwd().split(separator)[-1]
        if curr_dir not in self.inp["Assignments"]:
            print_stderr(
                f"\nError: {curr_dir} is not the group directory for {name}\nPlease change working directory\n"
            )

        no_overlap = self.inp["Assignments"][curr_dir]["no_overlap"]
        new_dates = generateUploadDates(
            self.inp["Assignments"][curr_dir],
            self.inp["Class Schedule"],
            start_date=date,
        )
        overlap_gen = (
            generateUploadDates(
                self.inp["Assignments"][overlap], self.inp["Class Schedule"]
            )
            for overlap in no_overlap
        )
        overlap_dates = [date for overlap in overlap_gen for date in overlap]
        upload_dates = (
            formatDate(date) for date in new_dates if date not in overlap_dates
        )

        canvas_assignments = self.api.assignments.list(
            data={"order_by": "due_at", "per_page": 100}
        ).json()
        if len(canvas_assignments) == 100:
            print_stderr(
                "\nWarning! 100 assignments have been pulled from canvas.\nDue to pagination, not all assignments may have been pulled.\n\n"
            )
        shifting = (
            (assignment["name"], assignment["id"], assignment["due_at"])
            for assignment in canvas_assignments
            if assignment["assignment_group_id"] == self.inp.IDs["Groups"][curr_dir]
        )
        for assignment in shifting:
            if assignment[0] == name:
                break

        for assignment, date in zip(shifting, upload_dates):
            self.editAssignment(assignment[0], {"assignment[due_at]": date})

        for assignment in shifting:
            self.deleteAssignment(assignment[0])
            print_stderr(f"Removed Assignment: {assignment[0]}")

    def downloadAssignmentSubmissions(self, name: str, ext: str):
        assignment_id = self.inp.IDs["Assignments"][name]
        submissions_response = self.api.assignments.listSubmissions(assignment_id)
        submissions = submissions_response.json()
        submissions_links = submissions_response.links
        count = 0

        for submission in submissions:
            if "attachments" not in submission:
                continue
            student_id = submission["user_id"]
            for attachment in submission["attachments"]:
                submission_url = attachment["url"]
                download(submission_url, f"{student_id}.{ext}", f"./submissions/{name}")
                count += 1

        while "next" in submissions_links:
            submissions_response = self.api.get(submissions_links["next"]["url"])
            submissions = submissions_response.json()
            submissions_links = submissions_response.links

            for submission in submissions:
                if "attachments" not in submission:
                    continue
                student_id = submission["user_id"]
                for attachment in submission["attachments"]:
                    submission_url = attachment["url"]
                    download(
                        submission_url, f"{student_id}.{ext}", f"./submissions/{name}"
                    )
                    count += 1

        print_stderr(
            f"\n{count} submissions have been download to ./submissions/{name}/\n"
        )

    def uploadQuiz(self, data: dict):
        quiz_response = self.api.quizzes.create(data)
        quiz_id = quiz_response.json()["id"]
        name = data["quiz[title]"]
        self.inp.IDs["Quizzes"][name] = quiz_id
        self.inp.IDs["Quizzes"][quiz_id] = {}

    def uploadQuizQuestion(self, quiz_id: int | str, data: dict):
        question_response = self.api.quizzes.questions.create(quiz_id, data)
        question_id = question_response.json()
        question_id = question_id["id"]
        name = data["question"]["question_name"]
        self.inp.IDs["Quizzes"][quiz_id][name] = question_id

    # TODO Implement
    def createQuizGroup(self, quiz_id: int | str, data: dict):
        pass

    # TODO: implement
    def deleteQuiz(self, name: str):
        quiz_id = self.inp.IDs["Quizzes"][name]
        del self.inp.IDs["Quizzes"][name]
        del self.inp.IDs["Quizzes"][quiz_id]
        return self.api.quizzes.delete(quiz_id)

    # ? potentially unnecessary
    def editFile(self, data):
        name = data["name"]
        file_id = self.inp.IDs["Files"][name]
        self.api.files.edit(file_id, data)

    def deleteAssignment(self, name: str):
        aid = self.inp.IDs["Assignments"][name]
        del self.inp.IDs["Assignments"][name]
        return self.api.assignments.delete(aid)

    def deleteFile(self, file_name: str):
        fid = self.inp.IDs["Files"][file_name]
        del self.inp.IDs["Files"][file_name]
        return self.api.files.delete(fid)

    def deleteAssignmentFile(self, name: str):
        return self.deleteAssignment(name), self.deleteFile(name)

    def deleteFolder(self, folder_name: str):
        fid = self.inp.IDs["Folders"][folder_name]
        del self.inp.IDs["Folders"][folder_name]
        return self.api.folders.delete(fid)

    # TODO: check quizzes
    def exists(self, name: str) -> bool:
        if self.inp.exists(name):
            return True

        assignments = self.api.assignments.listGenerator()

        for assignment in assignments:
            if name == assignment["name"]:
                self.inp.IDs["Assignments"][name] = assignment["id"]
                return True

        files = self.api.files.listGenerator()

        for file in files:
            if name == file["display_name"]:
                self.inp.IDs["Files"][name] = file["id"]
                return True

        self.save()
        return False

    def gradeAssignment(self, student_id, assignment, grade):
        if grade >= 0:
            grade_data = {
                "submission[posted_grade]": str(grade),
            }
        else:
            grade_data = {
                "submission[excuse]": True,
            }

        assignment_id = self.inp.IDs["Assignments"][assignment]
        self.api.assignments.grade(assignment_id, student_id, grade_data)

    # TODO optimize
    # ? move to canvas.py
    def grade(self, override=False):
        from canvas import GRADE

        try:
            grades = pd.read_csv("grades.csv", index_col=False)
        except FileNotFoundError:
            print_stderr(
                "\nFailed to locate grades.csv\nPlease cd into the directory containing grades.csv\n"
            )
            return

        id, *assignments = grades

        student_ids = [int(student_id) for student_id in grades[id][1:]]
        max_points = (int(grades[assignment][0]) for assignment in assignments)

        # data to be submitted after confirming no issues with grade changes
        submission_data = []
        for assignment, points in zip(assignments, max_points):
            try:
                self.editAssignment(assignment, {"assignment[published]": True})
            except:
                print_stderr(
                    f"\nFailed to publish assignment: {assignment}.\nMake sure assignment exists before attempting to grade it.\n"
                )
                return

            # format grade data and check for grading issues
            for i, student in enumerate(student_ids):
                new_grade = int(grades[assignment][i + 1])
                submission_data.append((assignment, student, new_grade, points))

                try:
                    current_grade = self.api.assignments.getSubmission(
                        self.inp.IDs["Assignments"][assignment], student
                    ).json()["grade"]
                except:
                    print_stderr(
                        f"\nFailed to retrieve data for student: {student}\nMake sure {student} is enrolled in course {self.course_id} on canvas.\n"
                    )
                    return

                if current_grade is not None:
                    current_grade = int(current_grade)

                    if not override:
                        print_stderr(
                            f'\nAssignment "{assignment}" has already been graded.\nTo replace grades, enter {GRADE} true\nAborting...\n'
                        )
                        return
                    if 0 <= new_grade < current_grade:
                        print_stderr(
                            f'\nError: Grade for student {student} will be lowered from {current_grade} to {new_grade} for Assignment "{assignment}".\nEnter grades manually.\nAborting...\n'
                        )
                        return

        # post grades and update maximun points for each assignment
        tasks = tqdm(submission_data)
        for assignment, student_id, grade, points in tasks:
            if points == -1:
                self.editAssignment(
                    assignment, {"assignment[omit_from_final_grade]": True}
                )
            else:
                self.editAssignment(assignment, {"assignment[points_possible]": points})
            self.gradeAssignment(student_id, assignment, grade)
            tasks.set_description(
                f"Grading Assignment: {assignment} for Student: {student_id: <30}"
            )
