from potara.summarizer import Summarizer
from potara.document import Document
from os import listdir
from os.path import isfile, join

s = Summarizer()

numOfDocs = 500

mypath = "../../preprocessed/potara/TaskTextHandlerUploadTextcreatedtaskTextHandlerUploadTextUploadUrls"

files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

files = files[0:numOfDocs]

with open(str(numOfDocs) + "docs.txt", "w+") as docRecord:
    docRecord.write("\n".join([mypath + "/" + taskFile for taskFile in files]))


print(mypath)
print(str(len(files)) + " files.")
print(files)
# Adding docs, preprocessing them and computing some infos for the summarizer
s.setDocuments([Document(mypath + "/"+ str(i))
                for i in files])
       
# Summarizing, where the actual work is done
s.summarize()

# You can then print the summary
print(s.summary)

with open("results/summaryLong"+str(numOfDocs)+".txt", "w+") as summFile:
    summFile.write(''.join(s.summary))
