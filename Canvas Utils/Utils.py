import datetime
import yaml
import os
import sys
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

    with open(os.path.join(root_dir, "inp.yaml"),"r") as f:
        all_settings = yaml.safe_load(f)

    login_token, _, _, *cids = all_settings

    course_id = [cid for cid in cids if cid in cwd]
    if len(course_id) == 0:
        print_stderr('\nError: Could not find Course ID\nPlease run from a subdirectory of the course directory\n')
        sys.exit()

    course_id = course_id[0]

    token = all_settings[login_token]
    course_settings = all_settings[course_id]

    canvasAPI = CanvasAPI(token)
    inp = Inp(root_dir, course_settings, course_id)

    return canvasAPI, course_id, os.path.join(root_dir, course_id), inp

def _findRootDir(dirs):

    if len(dirs) == 0:
        print_stderr('\n\nError, Could not find root directory or inp.json\nPlease run file from root directory or any of its subdirectories\n\n')
        sys.exit()

    full_path = os.path.join(*dirs)
    curr_dirs = os.listdir(full_path)

    if 'inp.yaml' in curr_dirs: return full_path

    return _findRootDir(dirs[:-1])

def dateGenerator(start_date, end_date, interval):
    date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
    end = datetime.datetime.strptime(end_date, '%m/%d/%Y')
    timedelta = datetime.timedelta(1) if interval == 'daily' else datetime.timedelta(7) if interval == 'weekly' else datetime.timedelta(interval)
    while date <= end:
        yield date
        date += timedelta
        if (interval == 0): break

def generateUploadDates(assignment, schedule, start_date = None):
    start = start_date if start_date else assignment['start_date']
    end = assignment['end_date']
    interval = assignment['interval']

    dates = dateGenerator(start, end, interval)

    week = {'Mon':0,'Tue':1,'Wed':2,'Thu':3,'Fri':4,'Sat':5,'Sun':6}
    days = [week[day] for day in schedule['days']]
    holy_days = [datetime.datetime.strptime(day, '%m/%d/%Y') for day in schedule['holy_days']]

    for date in dates:
        if date in holy_days: continue
        if date.weekday() in days:
            yield date

def formatDate(date: datetime.datetime):
    return f'{date.date()}T{date.time()}'

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
