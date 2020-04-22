from os import listdir, mkdir
from os.path import isfile, join
import os

mypath = "deathstarbench_trace_summaries"

allFiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

# Control number of files for preprocessing 
#files = files[0:0]

numOfFiles = [5, 10, 25, 100, 1000, 10000, 22290]


for fileNum in numOfFiles:
    print("Processing " + str(fileNum) + " files.")
    files = allFiles[0:fileNum]
    tasks = {}
    os.mkdir("preprocessed/scalability/" + str(fileNum))
    for file in files:
        with open(mypath + "/" + file) as openFile:
            lines = openFile.readlines()
            newlines = lines[1:]
            for task in newlines:
                taskID = task[0:task.find(".")]
                if taskID not in tasks:
                    tasks[taskID] = []
                tasks[taskID].append(task)

    for taskKey in tasks.keys():
        if not os.path.exists("preprocessed/scalability/" + str(fileNum) + "/" + ''.join(e for e in taskKey if e.isalnum())):
            os.mkdir("preprocessed/scalability/" + str(fileNum) + "/" + ''.join(e for e in taskKey if e.isalnum()))
        counter = 0
        for traceTask in tasks[taskKey]:
            with open("preprocessed/scalability/" + str(fileNum) + "/" + ''.join(e for e in taskKey if e.isalnum())+"/" + str(counter) + ".txt", "w+") as taskFile:
                taskFile.write(traceTask)
                counter += 1

### Processing all data at once
'''
print("Processing " + str(len(files)) + " files.") 

tasks = {}

for file in files:
    with open(mypath + "/" + file) as openFile:
        lines = openFile.readlines()
        newlines = lines[1:]
        for task in newlines:
            taskID = task[0:task.find(".")]
            if taskID not in tasks:
                tasks[taskID] = []
            tasks[taskID].append(task)

for taskKey in tasks.keys():
    if not os.path.exists("preprocessed/potara/" + ''.join(e for e in taskKey if e.isalnum())):
        os.mkdir("preprocessed/potara/" + ''.join(e for e in taskKey if e.isalnum()))
    counter = 0
    for traceTask in tasks[taskKey]:
        with open("preprocessed/potara/" + ''.join(e for e in taskKey if e.isalnum())+"/" + str(counter) + ".txt", "w+") as taskFile:
            taskFile.write(traceTask)
            counter += 1
    taskText = ''.join(tasks[taskKey])
    with open("preprocessed/BERT/" + ''.join(e for e in taskKey if e.isalnum()) + ".txt", "w+") as taskFile:
            taskFile.write(taskText)
'''

