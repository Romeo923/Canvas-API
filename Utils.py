import datetime
import json
import os
import sys
from canvasAPI import CanvasAPI


def loadSettings():
    cwd = os.getcwd().split('\\')
    cwd[0] += '\\'
    inp = findInp(cwd)

    with open(inp) as f:
        all_settings = json.load(f)

    login_token, *cids = all_settings

    course_id = [cid for cid in cids if cid in cwd]
    if len(course_id) == 0: 
        print('Could not find Course ID')
        sys.exit()

    course_id = course_id[0]

    token = all_settings[login_token]
    canvasAPI = CanvasAPI(token)

    return canvasAPI, course_id, all_settings, inp

def save(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, indent= 2)

def findInp(dirs):
    
    file = 'inp.json'
    full_path = os.path.join(*dirs)
    curr_dirs = os.listdir(full_path)

    if file in curr_dirs: return os.path.join(full_path,file)
    
    return findInp(dirs[:-1])
    
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
    i, j = (0, 0)
    if date.weekday() not in sched: 
        print("Start date not valid for given class schedule")
        sys.exit(0)
    
    while i < amount:
        date += j*timedelta
        weekday = date.weekday()
        if date not in exception_dates and weekday in sched:
            dates.append(f'{date.date()}T{date.time()}')
            i += 1
        j += 1
    return dates

def progressBar(progress, task):
    bar = '█' * int(progress/2) + '-' * (50 - int(progress/2))
    print(f'\r|{bar}| {progress:.2f}% {task}                              ', end = '\r')