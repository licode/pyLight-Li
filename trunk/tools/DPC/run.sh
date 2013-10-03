#!/bin/bash

# print date and time
date
NODECOUNT=`sort -u ${PBS_NODEFILE} | wc -l`
PROCCOUNT=`sort ${PBS_NODEFILE} | wc -w`
let i=$NODECOUNT*$PROCCOUNT
mpirun -np $i ./DPC.py $1 $2 $3 $4 $5 $6

date

