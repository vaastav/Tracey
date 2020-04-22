echo Start Test

echo 5 Traces
time python scaleSumm.py 5 >> logfile

echo 10 Traces
time python scaleSumm.py 10 >> logfile

echo 25 Traces
time python scaleSumm.py 25 >> logfile

echo 100 Traces
time python scaleSumm.py 100 >> logfile

echo 1000 Traces
time python scaleSumm.py 1000 >> logfile

echo 10000 Traces
time python scaleSumm.py 10000 >> logfile

echo 22290 Traces
time python scaleSumm.py 22290 >> logfile

