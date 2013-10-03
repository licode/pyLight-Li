#! /bin/bash

# Print date and time
date
NODECOUNT=`sort -u ${PBS_NODEFILE} | wc -l`
PROCCOUNT=`sort ${PBS_NODEFILE} | wc -w`
let i=$NODECOUNT*$PROCCOUNT
mpirun -np $i ./filtered_back.py $1

date

python collect.py $2

date
