import datetime
import json
import os
import sys
import copy
from canvasAPI import CanvasAPI

separator = '/' if sys.platform == 'darwin' else '\\'


def loadSettings():
    
    #! Black Magic, edit with caution
    
    # checks if computer is running macOS (darwin) or windows (win32)
    # dirs are separated by / in macOS and \ in windows
    
    cwd = os.getcwd().split(separator)
    cwd[0] += separator 
    root_dir = findRootDir(cwd)

    with open(os.path.join(root_dir,'inp.json')) as f:
        all_settings = json.load(f)

    login_token, *cids = all_settings

    course_id = [cid for cid in cids if cid in cwd]
    if len(course_id) == 0: 
        print('\nError: Could not find Course ID\nPlease run from a subdirectory of the course directory\n')
        sys.exit()

    course_id = course_id[0]
    default_settings = all_settings['Default']
    course_settings = all_settings[course_id]
    _, *overrides = course_settings
    
    new_settings = copy.deepcopy(default_settings)
    
    for section in overrides:
        
        if section in default_settings:
            
            match course_settings[section]:
                case dict() as var:
                    for key in var:
                        
                        match var[key]:
                            case dict():
                                for setting in var[key]:
                                    new_settings[section][key][setting] = var[key][setting]
                            case list():
                                new_settings[section][key] = var[key]
                                
                case list() as var:
                    new_settings[section] = var
        else : 
            new_settings[section] = course_settings[section]

    token = all_settings[login_token]
    canvasAPI = CanvasAPI(token)

    return canvasAPI, course_id, new_settings, all_settings, root_dir

def save(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, indent= 2)

def findRootDir(dirs):
    
    if len(dirs) == 0:
        print('\n\nError, Could not fild root directory or inp.json\nPlease run file from root directory or any of its subdirectories\n\n')
        sys.exit()
    
    full_path = os.path.join(*dirs)
    curr_dirs = os.listdir(full_path)

    if 'inp.json' in curr_dirs: return full_path
    
    return findRootDir(dirs[:-1])
    
def formatDate(date, interval, schedule, holy_days, amount):
    if date == None or interval == None: return date
    
    week = {'Mon':0,'Tue':1,'Wed':2,'Thu':3,'Fri':4,'Sat':5,'Sun':6}
    sched = [week[day] for day in schedule]
    
    timedelta = datetime.timedelta(1) if interval == 'daily' else datetime.timedelta(7) if interval == 'weekly' else datetime.timedelta(interval)
    month, day, year = date.split('/')
    exceptions = [holy_day.split('/') for holy_day in holy_days]
    date = datetime.datetime(int(year),int(month),int(day))
    exception_dates = [datetime.datetime(int(y),int(m),int(d)) for m, d, y in exceptions]
    
    dates = []
    i = 0
    
    while i < amount:
        date += timedelta
        weekday = date.weekday()
        if interval == 'daily' and weekday not in sched: continue
        if date not in exception_dates:
            dates.append(f'{date.date()}T{date.time()}')
            i += 1
    return dates

def progressBar(progress, task):
    bar = '█' * int(progress/2) + '-' * (50 - int(progress/2))
    print(f'\r|{bar}| {progress:.2f}% {task}                              ', end = '\r')
