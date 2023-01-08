import datetime
import json
import os
import sys
import mergedeep
import re
import requests
import zipfile
import io
from inp import Inp
from canvasAPI import CanvasAPI

separator = '/' if sys.platform == 'darwin' else '\\'


def loadSettings() -> tuple[CanvasAPI, str, Inp]:

    # checks if computer is running macOS (darwin) or windows (win32)
    # dirs are separated by / in macOS and \ in windows

    cwd = os.getcwd().split(separator)
    cwd[0] += separator
    root_dir = _findRootDir(cwd)

    with open(os.path.join(root_dir,'inp.json')) as f:
        all_settings = json.load(f)

    login_token, *cids = all_settings

    course_id = [cid for cid in cids if cid in cwd]
    if len(course_id) == 0:
        print_stderr('\nError: Could not find Course ID\nPlease run from a subdirectory of the course directory\n')
        sys.exit()

    course_id = course_id[0]
    default_settings = all_settings['Default']
    course_settings = all_settings[course_id]

    overrides = {override : course_settings[override] for override in course_settings if override != 'IDs'}
    new_settings = mergedeep.merge({},default_settings, overrides)

    groups = [*new_settings['Assignments']] + [*new_settings['Files']]

    missing = [group_dir for group_dir in groups if group_dir not in os.listdir(os.path.join(root_dir,course_id))]
    if len(missing) > 0:
        print(f"\nError! Group directory missing for group(s):\n{set(missing)}\n\n")
        sys.exit(0)

    token = all_settings[login_token]
    canvasAPI = CanvasAPI(token)
    inp = Inp(os.path.join(root_dir,'inp.json'), new_settings, all_settings, course_id)

    return canvasAPI, course_id, os.path.join(root_dir, course_id), inp

def _findRootDir(dirs):

    if len(dirs) == 0:
        print_stderr('\n\nError, Could not fild root directory or inp.json\nPlease run file from root directory or any of its subdirectories\n\n')
        sys.exit()

    full_path = os.path.join(*dirs)
    curr_dirs = os.listdir(full_path)

    if 'inp.json' in curr_dirs: return full_path

    return _findRootDir(dirs[:-1])

# TODO optimize
#? reduce input parameters by passing Course object instead
def generateDates(start_date, end_date, interval, schedule, holy_days, amount, overlap=list()):
    if start_date == None or interval == None: return start_date

    week = {'Mon':0,'Tue':1,'Wed':2,'Thu':3,'Fri':4,'Sat':5,'Sun':6}
    sched = [week[day] for day in schedule]

    timedelta = datetime.timedelta(1) if interval == 'daily' else datetime.timedelta(7) if interval == 'weekly' else datetime.timedelta(interval)
    month, day, year = start_date.split('/')
    eMonth, eDay, eYear = end_date.split('/')
    exceptions = [holy_day.split('/') for holy_day in holy_days]
    start_date = datetime.datetime(int(year),int(month),int(day))
    end_date = datetime.datetime(int(eYear),int(eMonth),int(eDay))
    exception_dates = [datetime.datetime(int(y),int(m),int(d)) for m, d, y in exceptions] + [datetime.datetime(int(overlap_date[0]),int(overlap_date[1]),int(overlap_date[2])) for date in overlap if (overlap_date := date.split('T')[0].split('-'))]

    dates = []
    i = 0

    while i < amount and start_date <= end_date:
        weekday = start_date.weekday()
        if start_date not in exception_dates and not (interval == 'daily' and weekday not in sched):
            dates.append(f'{start_date.date()}T{start_date.time()}')
            i += 1
        start_date += timedelta
    return dates

def validDate(date: str) -> bool:
    try:
        datetime.datetime.strptime(date, '%m/%d/%Y')
        return True
    except ValueError:
        return False

def progressBar(total_tasks: int):
    completed_tasks = 0
    def bar(task):
        nonlocal completed_tasks
        completed_tasks += 1
        progress = 100*completed_tasks/total_tasks
        bar = '█' * int(progress/2) + '-' * (50 - int(progress/2))
        print_stderr(f'\r|{bar}| {progress:.2f}% {task: <50}', end = '\r')

    def overrideProgress(update: int):
        nonlocal completed_tasks
        completed_tasks += update

    return bar, overrideProgress

def naturalSort(items):

    convert = lambda text: int(text) if text.isdigit() else text.lower()
    natsort = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]

    return sorted(items, key=natsort)

def download(url: str, file_name: str, download_path: str):
    get_response = requests.get(url,stream=True)
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    with open(f'{download_path}/{file_name}', 'wb+') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def downloadZIP(url: str, file_name: str, download_path: str):
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    z.extractall(f'{download_path}/{file_name}')

def print_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
