#this is an example script example.sh
#
#These commands set up the Grid Environment for your job:

#PBS -m abe
#PBS -S /bin/bash
#PBS -l nodes=1
#PBS -l walltime=00:01:00
#PBS -N ExampleJob

## We requested nodes and procesors per node.  ${PBS_NODEFILE} lists
## these node.  Count the number of processors selected.
NODECOUNT=`sort -u ${PBS_NODEFILE} | wc -l`
PROCCOUNT=`sort ${PBS_NODEFILE} | wc -w`

#print the time and date
date
echo $NODECOUNT
echo $PROCCOUNT
echo `pwd`
echo $0
cat $0
#job info
cd pyLight/trunk/tools/DPC
python TOMO.py 90 60 dummy

