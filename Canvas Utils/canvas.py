import os
from course import Course
from Utils import *

#* change/modify strings here to change flags
INIT = '--init' # initialized canvas
INDEX = '--index' # upload duplicate file with name indexing
REPLACE = '--replace' # edit assignments / replace files
SHIFT = '--shift' # shift assignment due dates
DELETE = '--delete' # delete a file or assignment
GRADE = '--grade' # grade assignments
DOWNLOAD = '--download' # download assignments submissions
HELP = '--help'

def init(course: Course, args: list[str], kwargs: dict):
    if len(args) > 0 or len(kwargs) > 0:
        print_stderr(f"\n'{INIT}' flag does not take any arguments, additional args and kwargs will not be used\n")

    course.resetCourse()
    course.resetInp()
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

    course.save()
    print_stderr(f'\n{upload_name} has been modified.\n')

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

    if course.exists(name):
        if ext in course.inp['File Extentions']:
            course.deleteFile(name)
        else:
            course.deleteAssignment(full_name)
    else:
        print_stderr(f'\n{full_name} does not exist.\n')
        return

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
            'name': name,
            'parent_folder_id': folder_id
        }

        course.uploadFile(path, file_data)
        print_stderr(f'Uploaded file {full_name}.\n')
    else:
        assignment_data = generateData(course, args, kwargs)
        assignment_data["assignment[name]"] = name
        assignment_data["assignment[assignment_group_id]"] = course.inp['IDs']['Groups'][cwd]

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
            assignment_data["assignment[submission_types][]"] = "online_upload"
            path = os.path.join(os.getcwd(),assignment)
            course.uploadAssignmentFile(assignment_data, file_data, path)
            print_stderr(f'Uploaded asignment: {name} with file {assignment} attatched.\n')
        else:
            course.uploadAssignment(assignment_data)
            print_stderr(f'Uploaded assignment {name}.\n')


    course.save()

def download(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0:
        print_stderr(f"\nNo arguments given. \n'{DOWNLOAD}' requires an assignment name as an argument.\n")
        return

    full_name, *args = args
    name, ext = full_name.split('.',1) if '.' in full_name else (full_name, "")

    if course.exists(name):
        if ext in course.inp['File Extentions']:
            print_stderr(f'\nFailed to gather submissions for {full_name}.\n')
        else:
            print_stderr("Downloading...")
            course.downloadAssignmentSubmissions(full_name)
    else:
        print_stderr(f'\n{full_name} does not exist.\n')
        return

def grade(course: Course, args: list[str], kwargs: dict):
    if len(args) == 0 and len(kwargs) == 0:
        course.grade()
        return

    arg, *_ = args
    if arg.lower() == 'true' or arg.lower() == 'false':
        course.grade(True if arg.lower() == 'true' else False)
        return

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
    print_stderr(f"{'(Download)': <10} >  |Required: Assignment name")
    print_stderr(f"{HELP: <10} | canvas.py {HELP}")
    print_stderr(f"{'(Help)': <10} >  |takes no arguments")
    print_stderr(f"\nRemember to cd into the appropriate directory.\nUploading does not require any flags, just give the name and settings as arguments.\nIf the flag you want isnt listed, make Romeo impliment it\n")

def generateData(course: Course,args: list[str], kwargs: dict):

    for arg in args:
        if validDate(arg):
            cwd = os.getcwd().split(separator)[-1]

            no_overlap = course.inp['Assignments'][cwd]['no_overlap']
            overlap_dates = []
            for overlap in no_overlap:
                overlap_dates += generateDates(
                    course.inp['Assignments'][overlap]['start_date'],
                    course.inp['Assignments'][overlap]['end_date'],
                    course.inp['Assignments'][overlap]['interval'],
                    course.inp['Class Schedule']['days'],
                    course.inp['Class Schedule']['holy_days'],
                    course.inp['Assignments'][overlap]['amount']
                )

            kwargs["assignment[due_at]"] = generateDates(
                arg,
                "12/30/3333",
                1,
                course.inp['Class Schedule']['days'],
                course.inp['Class Schedule']['holy_days'],
                1,
                overlap_dates
            )[0]

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
        INDEX: index,
        REPLACE: replace,
        SHIFT: shift,
        DELETE: delete,
        GRADE: grade,
        DOWNLOAD: download,
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
