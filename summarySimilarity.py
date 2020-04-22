from os import listdir
from os.path import isfile, join
import statistics

def processSent(sent):
    removeList = [" ", ":"]
    retVal = sent
    for removeChar in removeList:
        retVal = retVal.replace(removeChar, "")
    return(retVal)


numOfDocs = [5,10,25,100,500]

mydatapath = "../../../preprocessed/potara/TaskTextHandlerUploadTextcreatedtaskTextHandlerUploadTextUploadUrls"

files = [f for f in listdir(mydatapath) if isfile(join(mydatapath, f))]

#numOfDocs = numOfDocs[0:1]

for docNum in numOfDocs:
    analysisFiles = files[0:docNum]
    unqSentFreq = {}
    allSentences = []
    for traceFile in analysisFiles:
        with open(join(mydatapath, traceFile)) as openFile:
            lines = openFile.readlines()
            for task in lines:
                allSentences = allSentences + task.split(".")
    for sentence in allSentences:
        if sentence not in unqSentFreq:
            unqSentFreq[sentence] = 0
        unqSentFreq[sentence] += 1
    summary = []
    with open("summaryLong" + str(docNum) + ".txt") as summFile:
        summary = summFile.read().split(".")
    matches = []
    for sentence in summary:
       matchingKey = [key for key in unqSentFreq.keys() if processSent(sentence) == processSent(key)]
       if(len(matchingKey) > 0):
           matches.append(matchingKey[0])
    matchedFreq = statistics.mean([unqSentFreq[key] for key in matches])
    totalFreq = statistics.mean([unqSentFreq[key] for key in unqSentFreq.keys()])
    with open("analysisResults.csv", "a") as resultsFile:
        resultsFile.write(str(docNum)+","+str(len(matches))+","+str(len(unqSentFreq.keys()))+","\
                + str(matchedFreq) + "," + str(totalFreq) + ",\n")
