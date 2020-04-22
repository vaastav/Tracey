from potara.summarizer import Summarizer
from potara.document import Document
from os import listdir
from os.path import isfile, join
import sys
import os
numOfTraces = sys.argv[1]

mypath = "../../preprocessed/scalability/" + str(numOfTraces)

tasks = [x[0] for x in os.walk(mypath)]
tasks = tasks[1:]

os.mkdir("results/scalability/" + str(numOfTraces))

skippedTasks = 0

for task in tasks:

    s = Summarizer()

    files = [f for f in listdir(task) if isfile(join(mypath, f))]
    if(len(files) < 4):
        print("Skipped " + os.path.basename(task))
        skippedTasks += 1
        continue
    print(os.path.basename(task))
    print(str(len(files)) + " files.")
    print(files)
    # Adding docs, preprocessing them and computing some infos for the summarizer
    s.setDocuments([Document(task + "/"+ str(i))
                    for i in files])
       
    # Summarizing, where the actual work is done
    s.summarize()

    # You can then print the summary
    print(s.summary)
    print("")
    with open("results/scalability/"+str(numOfTraces) + "/" + \
            os.path.basename(task) + ".txt", "w+") as summFile:
        summFile.write(''.join(s.summary))
with open("results/scalability/" + str(numOfTraces) +"/numSkipped.csv", "w+") as skipped:
    skipped.write("skippedTasks,totalTasks,\n" + str(skippedTasks) + "," + str(len(tasks)) +",\n")
