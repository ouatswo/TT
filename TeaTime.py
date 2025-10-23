"""
TeaTime, 2025-10-04
Licenes: there isn't any
"""

import time, json, os
from pathlib import Path
from enum import Enum

class File:
    def __init__(self):
        self.folder = "TeaTime__do_not_edit_or_delete"
        Path(self.folder).mkdir(exist_ok=True)
        self.today = time.strftime("%Y-%m-%d")
        self.file = open(self.folder + '/' + self.today + ".txt", "a+")
    def save(self, task):
        self.file.write(f"{task.start:.0f} {task.end:.0f} {task.desc}\n")
        self.file.flush()
    def load(self):
        self.file.seek(0)
        tasks = []
        for line in self.file.readlines():
            line = line.strip().split(" ", 3)
            start = line[0]
            end   = line[1]
            desc  = " ".join(line[2:])
            task = Task(start, end, desc)
            tasks.append(task)
        return tasks

file        = File()

class TargetsFile:
    def __init__(self):
        self.filename = file.folder + '/' + "@targets.json"
        open(self.filename, "a+").close()
        with open(self.filename, "r", encoding="utf-8-sig") as f:
            fileContent = f.read().strip()
            if fileContent:
                self.targets = json.loads(fileContent)
            else:
                self.targets = dict()
    def update(self, target, value):
        self.targets[target] = value
        with open(file.folder + '/' + self.filename, "w", encoding="utf-8-sig") as f:
            f.seek(0)
            json.dump(self.targets, f, indent=4)
            f.flush()
    def get(self, target):
        if self.exists(target):
            return self.targets.get(target, None)
        else: 
            return None
    def exists(self, target):
        return self.targets.get(target, None) != None

targets     = TargetsFile()

class TimeProfile(Enum):
    TOTAL   = 1
    TODAY   = 2

class Database:
    def __init__(self):
        self.tasks      = []
        self.dictionary = dict()
    def new(self, task, profile):
        self.tasks.append(task)
        desc = task.desc
        if targets.exists(desc):
            task.target = targets.get(desc)
        if self.dictionary.get(desc) != None:
            self.dictionary[desc][0].append(task)
            if profile == TimeProfile.TOTAL:
                self.dictionary[desc][1] += task.dura
            elif profile == TimeProfile.TODAY:
                self.dictionary[desc][2] += task.dura
        else: 
            if profile == TimeProfile.TOTAL:
                self.dictionary[desc] = [[task], task.dura, 0]
            elif profile == TimeProfile.TODAY:
                self.dictionary[desc] = [[task], 0, task.dura]

db          = Database()

class Task:
    def __init__(self, start, end, desc):
        self.desc   = desc
        self.start  = start
        self.end    = end
        self.dura   = int(end)-int(start)
        self.target = None


total_time  = 0
today_time  = 0


def percent(current, target):
    result = f"{current:.1f}"
    if target == None:
        return result
    if target > current:
        result += '(-'+str(int(target-current))+')'
    elif target < current:
        result += '(+'+str(int(current-target))+')'
    return result

def items():
    result = [["Description", "Total", "Today"]]
    sorted_items = sorted(db.dictionary.items(), key=lambda x: x[1][1], reverse=True)
    for desc, tasks_and_dura in sorted_items:
        today_perc = (tasks_and_dura[2]/today_time*100)
        total_perc = (tasks_and_dura[1]/total_time*100)
        
        target = targets.get(desc)
        today = percent(today_perc, target)
        total = percent(total_perc, target)
        result.append([desc, total, today])
    return result

def start_of_a_task(): 
    if len(db.tasks) == 0:
        # set start to 00:00 of localtime
        start  = time.localtime()
        start = time.mktime((start.tm_year, start.tm_mon, start.tm_mday,
            0, 0, 0, start.tm_wday, start.tm_yday, start.tm_isdst))
    else:
        # or end of last event as start of a new
        start = int(db.tasks[len(db.tasks)-1].end)
    return start

def is_valid(desc): # oogh, i know
    ds = desc.split()
    if len(ds) == 1 and ds[0] != "!help":
        return True

def help():
    print("\033[2J\033[H", end="")
    print("TeaTime, log events.\nCommands:\n@target %task% %percent%")

def command(cmd):
    ds = cmd.split()
    if ds[0] == "@target":
        targets.update(ds[1], float(ds[2]))

if __name__ == "__main__":
    # total profile
    files = list(Path(file.folder).glob("*.txt"))
    for file_name in files:
        file.file = open(file_name, "r")
        for task in file.load():
            total_time += task.dura
            db.new(task, TimeProfile.TOTAL)

    file = File()
    for task in file.load():
        today_time += task.dura
        db.new(task, TimeProfile.TODAY)
    
    desc = ""
    while True:
        if not desc == "@help":
            print("\033[2J\033[H", end="")
        rows = items()
        widths = [max(len(cell) for cell in col) for col in zip(*rows)]

        for i, row in enumerate(rows):
            line = " | ".join(cell.ljust(widths[j]) for j, cell in enumerate(row))
            print(line)
            if i == 0:
                print("-+-".join("-" * w for w in widths))

        start = start_of_a_task()
        desc  = input(f"> Describe what you did in one word in last {(time.time()-int(start)):.0f} seconds (@help): ")
        end   = time.time()
        
        if desc.strip() == "":
            continue
        elif desc == "@help":
            help()
        elif is_valid(desc):
            curr_task = Task(start, end, desc)
            total_time += curr_task.dura
            today_time += curr_task.dura
            db.new(curr_task, TimeProfile.TODAY)
            db.new(curr_task, TimeProfile.TOTAL)
            file.save(curr_task)
        else:
            command(desc)
        