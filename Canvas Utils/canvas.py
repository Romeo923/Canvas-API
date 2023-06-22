import os
from course import Course
from Utils import *
import yaml

#! change/modify strings here to change flags

INIT = '--init' # initialized canvas
#* usage: canvas.py --init

UPLOAD = '--upload' # upload a new assignment or file

INDEX = '--index' # upload duplicate file with name indexing
#* usage: canvas.py --index filename.pdf
# will upload filename-1.pdf, filename-2.pdf, etc.

REPLACE = '--replace' # edit assignments / replace files
#* usage: canvas.py --replace filename.pdf
# will replace filename.pdf

QUIZ = '--quiz' # create or reupload quiz
#* usage: canvas.py --quiz quiz-name
# will create or reupload quiz-name with settings from quizzes.yaml

SHIFT = '--shift' # shift assignment due dates
#* usage: canvas.py --shift hmk-7 02/06/2023
# hmk-7 due date will be moved to 02/06/2023
# all subsequent hmks will be shifted according to inp file "interval" setting

REORDER = '--reorder'

DELETE = '--delete' # delete a file or assignment
# usage: canvas.py --delete quiz-3

GRADE = '--grade' # grade assignments
#* usage: canvas.py --grade
# will grade assignments from grades.csv data
# aborts if assignments has already been graded
#* usage: canvas.py --grade true
# will grade assignments from grades.csv data
# will override existing grade
# aborts if student grade gets lowered

DOWNLOAD = '--download' # download assignments submissions
# usage: canvas.py --download hmk-2 pdf
#        canvas.py --download hmk-2 htlm

SYNC = '--sync' # sync/retrieve all group, assignment, and file ids from canvas

DETAILS = '--details' # displays course details

HELP = '--help'

def init(course: Course, args: list[str], kwargs: dict):
    if len(args) > 0 or len(kwargs) > 0:
        print_stderr(f"\n'{INIT}' flag does not take any arguments, additional args and kwargs will not be used\n")

    course.resetCourse()
    course.resetIDs()
    course.initCourse()

def index(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0:
        print_stderr(f"\nNo arguments given. \n'{INDEX}' requires a file name as an argument.\n")
        return

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if course.exists(name):
        if ext in course.inp['File Extentions']:

            cwd = os.getcwd().split(separator)[-1]
            if not validCWD(course):
                print_stderr(f"Current directory {cwd} is not a valid directory.\nPlease cd into one of the following:\n{[*course.inp['Assignments']]} or {[*course.inp['Files']]}\n")
                return

            folder_id = course.inp['IDs']['Folders'][cwd]
            kwargs["on_duplicate"] = "rename"
            kwargs['name'] = name
            kwargs["parent_folder_id"] = folder_id
            response = course.uploadFile(os.path.join(os.getcwd(),full_name), kwargs)
            upload_name = response['display_name']

        else:
            print_stderr(f"\n{full_name} is not a valid file, try using '{REPLACE}' to edit an assignment\n")
            return
    else:
        print_stderr(f'\n{full_name} does not exist.\n')
        return

    course.save()
    print_stderr(f'\n{upload_name} has been uploaded.\n')

def replace(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0:
        print_stderr(f"\nNo arguments given. \n'{REPLACE}' requires an assignment or file name as an argument.\n")
        return

    cwd = os.getcwd().split(separator)[-1]
    if not validCWD(course):
        print_stderr(f"Current directory {cwd} is not a valid directory.\nPlease cd into one of the following:\n{[*course.inp['Assignments']]} or {[*course.inp['Files']]}\n")
        return

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if course.exists(name):
        if ext in course.inp['File Extentions']:

            folder_id = course.inp['IDs']['Folders'][cwd]
            kwargs["on_duplicate"] = "overwrite"
            kwargs['name'] = name
            kwargs["parent_folder_id"] = folder_id
            response = course.uploadFile(os.path.join(os.getcwd(),full_name), kwargs)
            upload_name = response['display_name']

        else:
            response = course.editAssignment(name, generateData(course, args, kwargs))
            upload_name = response.json()['name']
    else:
        print_stderr(f'\n{full_name} does not exist.\n')
        return

def quiz(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0:
        print_stderr(f"\nNo arguments given. \n'{QUIZ}' requires a quiz name as an argument.\n")
        return

    if not os.path.exists(os.path.join(course.inp.root_dir, course.inp.course_id, 'quizzes.yaml')):
        print_stderr(f"Could not locate quizzes.yaml\n")
        return

    with open(os.path.join(course.inp.root_dir, course.inp.course_id, 'quizzes.yaml'), 'r') as f:
            quiz_yaml = yaml.safe_load(f)

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if name not in course.inp.IDs['Quizzes']:
        print_stderr(f'\n{full_name} does not exist.\n')
        return

    course.deleteQuiz(name)

    quiz_settings = course.inp['Quizzes']
    quiz = quiz_yaml[name]
    gid = course.inp.IDs['Groups'][quiz_settings['group']]

    schedule = course.inp['Class Schedule']
    no_overlap = quiz_settings['no_overlap']
    dates = generateUploadDates(quiz_settings, schedule)
    overlap_gen = (generateUploadDates(course.inp['Assignments'][overlap], schedule) for overlap in no_overlap)
    overlap_dates = [date for overlap in overlap_gen for date in overlap]
    upload_dates = (formatDate(date) for date in dates if date not in overlap_dates)
    date = next(upload_dates)

    _, _, *quiz_names = quiz_yaml
    for quiz_name in quiz_names:
        if quiz_name == name:
            break
        date = next(upload_dates)

    quiz_data = {
        "quiz[title]" : name,
        "quiz[description]" : quiz['description'],
        "quiz[quiz_type]" : quiz_settings['quiz_type'],
        "quiz[assignment_group_id]" : gid,
        "quiz[time_limit]" : quiz['time_limit'],
        "quiz[show_correct_answers]" : quiz_settings['show_correct_answers'],
        "quiz[shuffle_answers]" : quiz_settings['shuffle_answers'],
        "quiz[due_at]" : date,
        "quiz[published]" : quiz_settings['published'],
    }

    course.uploadQuiz(quiz_data)
    quiz_id = course.inp.IDs['Quizzes'][name]
    questions = quiz_yaml[name]['Questions']
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
        course.uploadQuizQuestion(quiz_id,question_data)
    course.save()
    print_stderr(f'\n{name} has been reuploaded.\n')

def shift(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0:
        print_stderr(f"\nNo arguments given. \n'{SHIFT}' requires an assignment name and a date as arguments.\n")
        return

    cwd = os.getcwd().split(separator)[-1]
    if not validCWD(course):
        print_stderr(f"Current directory {cwd} is not a valid directory.\nPlease cd into one of the following:\n{[*course.inp['Assignments']]} or {[*course.inp['Files']]}\n")
        return

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if course.exists(name):
        if ext in course.inp['File Extentions']:
            print_stderr(f'\nCannot shift file: {full_name}, argument must be an assignment.\n')
        else:
            arg = args[0]
            if validDate(arg):
                course.shiftAssignments(full_name, arg)
            else:
                print_stderr(f'\n{arg} is not a valid date. Enter {SHIFT} {name} MM/DD/YYYY')
                return
    else:
        print_stderr(f'\n{full_name} does not exist.\n')
        return

    course.save()
    print_stderr(f"{full_name}'s date has been shifted to {arg}.\nAll subsequent assignments in its group have been shifted accordingly.\n")

def delete(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0:
        print_stderr(f"\nNo arguments given. \n'{DELETE}' requires an assignment or file name as an argument.\n")
        return

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if not course.exists(name):
        print_stderr(f'\n{full_name} does not exist.\n')
        return

    if ext in course.inp['File Extentions']:
        course.deleteFile(name)
    else:
        course.deleteAssignment(full_name)

    print_stderr(f'\n{full_name} has been deleted.\n')
    course.save()

def upload(course: Course, args: list[str], kwargs: dict):

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if course.exists(name):
        print_stderr(f'\n{full_name} already exists.\nTry using one of the following flags:')
        help()
        return

    cwd = os.getcwd().split(separator)[-1]
    if not validCWD(course):
        print_stderr(f"Current directory {cwd} is not a valid directory.\nPlease cd into one of the following:\n{[*course.inp['Assignments']]} or {[*course.inp['Files']]}\n")
        return

    if ext in course.inp['File Extentions']:

        path = os.path.join(os.getcwd(),full_name)
        folder_id = course.inp['IDs']["Folders"][cwd]
        file_data = {
            'name': full_name,
            'parent_folder_id': folder_id
        }

        course.uploadFile(path, file_data)
        print_stderr(f'Uploaded file {full_name}.\n')
    else:
        assignment_data = generateData(course, args, kwargs)
        assignment_data["assignment[name]"] = name
        assignment_data["assignment[assignment_group_id]"] = course.inp['IDs']['Groups'][cwd]
        assignment_data["assignment[submission_types][]"] = ["on_paper"]

        has_file = False
        for assignment in os.listdir(os.getcwd()):
            name, ext = assignment.split('.',1) if '.' in assignment else (assignment, "")
            if name == full_name and ext in course.inp['File Extentions']:
                has_file = True
                break

        if has_file:
            folder_id = course.inp['IDs']["Folders"][cwd]
            file_data = {
                'name': name,
                'parent_folder_id': folder_id
            }
            assignment_data["assignment[submission_types][]"] += ["online_upload"]
            path = os.path.join(os.getcwd(),assignment)
            course.uploadAssignmentFile(assignment_data, file_data, path)
            print_stderr(f'Uploaded asignment: {name} with file {assignment} attatched.\n')
        else:
            course.uploadAssignment(assignment_data)
            print_stderr(f'Uploaded assignment {name}.\n')


    course.save()

#! Temp implementation, in testing
def reorder(course: Course, args: list[str], kwargs: dict):

    course.reorderTabs(args[0])


def download(course: Course, args: list[str], kwargs: dict):
    if len(args) < 2:
        print_stderr(f"\n'{DOWNLOAD}' requires an assignment name and file extention as arguments.\n")
        return

    name, ext, *args = args

    if course.exists(name):
            print_stderr("Downloading...")
            course.downloadAssignmentSubmissions(name, ext)
    else:
        print_stderr(f'\n{name} does not exist.\n')

def grade(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0 and len(kwargs) == 0:
        course.grade()
        return

    arg, *_ = args
    if arg.lower() == 'true' or arg.lower() == 'false':
        course.grade(True if arg.lower() == 'true' else False)
        return

def sync(course: Course, args: list[str], kwargs: dict):
    if len(args) > 0 or len(kwargs) > 0:
        print_stderr(f"\n'{INIT}' flag does not take any arguments, additional args and kwargs will not be used\n")

    course.syncCourse()

def details(course: Course, args: list[str], kwargs: dict):
    if len(args) > 0 or len(kwargs) > 0:
        print_stderr(f"\n'{INIT}' flag does not take any arguments, additional args and kwargs will not be used\n")

    cid = course.course_id
    ASSIGNMENTS, QUIZZES, FILES, FILE_EXTS, GRADING_SCALE, TABS, CLASS_SCHEDULE, *_ = course.inp
    assignments = course.inp[ASSIGNMENTS]
    quizzes = course.inp[QUIZZES]
    files = course.inp[FILES]
    file_exts = course.inp[FILE_EXTS]
    grading_scales = course.inp[GRADING_SCALE]
    class_days, holy_days = course.inp[CLASS_SCHEDULE]

    print(f'\nCOURSE ID: {cid}')
    print(f'\nCOURSE SCHEDULE:\n  Meeting Days: {class_days}\n  Holy Days: {holy_days}')
    print(f'\nAccepted File Extentions: {file_exts}')
    print(f'\nCOURSE QUIZZES:')
    for setting in quizzes:
        value = quizzes[setting]
        print(f'  {setting}: {value}')
    print(f'\nCOURSE ASSIGNMENTS:')
    for assignment in assignments:
        print(f'\n  {assignment}:')
        for setting in assignments[assignment]:
            value = assignments[assignment][setting]
            print(f'    {setting}: {value}')



def help(*_):
    print_stderr(f"\n{'Flag': <10} | Usgae")
    print_stderr(f"{'-'*18}")
    print_stderr(f"{INIT: <10} | canvas.py {INIT}")
    print_stderr(f"{'(Init)': <10} >  |takes no arguments")
    print_stderr(f"{INDEX: <10} | canvas.py {INDEX} <file.ext>")
    print_stderr(f"{'(Index)': <10} >  |Required: File name")
    print_stderr(f"{REPLACE: <10} | canvas.py {REPLACE} <name | file.ext> <args | kwargs>")
    print_stderr(f"{'(Replace)': <10} >  |Required: Assignment or File name")
    print_stderr(f"{' ': <10} >  |Optional: int point value, boolean published value, or string date value")
    print_stderr(f"{SHIFT: <10} | canvas.py {SHIFT} <name> <MM/DD/YYYY>")
    print_stderr(f"{'(Shift)': <10} >  |Required: Assignment or File name, Starting date")
    print_stderr(f"{DELETE: <10} | canvas.py {DELETE} <name | file.ext>")
    print_stderr(f"{'(Delete)': <10} >  |Required: Assignment or File name")
    print_stderr(f"{GRADE: <10} | canvas.py {GRADE} <override>")
    print_stderr(f"{'(Grade)': <10} >  |Optional: boolean override value")
    print_stderr(f"{DOWNLOAD: <10} | canvas.py {DOWNLOAD} <name>")
    print_stderr(f"{'(Download)': <10} >  |Required: Assignment name, expected file extention")
    print_stderr(f"{HELP: <10} | canvas.py {HELP}")
    print_stderr(f"{'(Help)': <10} >  |takes no arguments")
    print_stderr(f"\nRemember to cd into the appropriate directory.\nUploading does not require any flags, just give the name and settings as arguments.\nIf the flag you want isnt listed, make Romeo impliment it\n")

def generateData(course: Course,args: list[str], kwargs: dict):

    for arg in args:
        if validDate(arg):
            cwd = os.getcwd().split(separator)[-1]

            no_overlap = course.inp['Assignments'][cwd]['no_overlap']
            dates = generateUploadDates(course.inp['Assignments'][cwd], course.inp['Class Schedule'], start_date=arg)
            overlap_gen = (generateUploadDates(course.inp['Assignments'][overlap], course.inp['Class Schedule']) for overlap in no_overlap)
            overlap_dates = [date for overlap in overlap_gen for date in overlap]
            upload_dates = (formatDate(date) for date in dates if date not in overlap_dates)

            kwargs["assignment[due_at]"] = next(upload_dates)

        elif arg.isdigit():
            kwargs["assignment[points_possible]"] = arg
        elif arg.lower() == 'true' or arg.lower() == 'false':
            kwargs["assignment[published]"] = True if arg.lower() == 'true' else False
        else:
            print_stderr(f'{arg} is not a valid argument')

    return kwargs

def validCWD(course: Course) -> bool:
    cwd = os.getcwd().split(separator)[-1]
    return cwd in course.inp['Assignments'] or cwd in course.inp['Files']

def main(*test_args):
    course = Course(*loadSettings())

    flags = {
        INIT: init,
        UPLOAD: upload,
        INDEX: index,
        REPLACE: replace,
        QUIZ: quiz,
        SHIFT: shift,
        REORDER: reorder,
        DELETE: delete,
        GRADE: grade,
        DOWNLOAD: download,
        SYNC: sync,
        DETAILS: details,
        HELP: help
    }

    args = test_args if test_args else sys.argv[1:]

    if len(args) == 0:
        print_stderr(f"\nNo arguments given.")
        help()
        return

    kwargs = dict(arg.split('=') for arg in args if '=' in arg)
    commands = [arg for arg in args if '=' not in arg]

    flag, *args = commands

    if '-' in flag[0]:
        if flag in flags:
            flags[flag](course, args, kwargs)
        else:
            print_stderr(f"\n'{flag}' is not a valid flag.")
            help()
    else:
        upload(course, commands, kwargs)

if __name__ == '__main__':
    main()
