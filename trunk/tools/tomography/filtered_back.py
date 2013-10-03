#!/usr/bin/env python

"""
    Read in sinogram h5 file and do 2D FBP for each slice
    Store the sub-results in folder sub_tomo/  
    @author: Wei Xu
    @affilication: CSC @ BNL
    @date created: Aug. 6, 2013
    @date last modified: Aug. 6, 2013
"""

import sys
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
import Image
from time import time
from mpi4py import MPI
import parallel_beam as pb
import h5py

def recon2d(filepath):
    """
        Reconstruct a set of 2D slices
    """
    # Set up MPI environment
    comm = MPI.COMM_WORLD
    nodeID = comm.Get_rank()
    total = comm.Get_size()
    slice_start = 0
    slice_end = 0

    file = h5py.File(filepath) #sinogram stack
    theta = file['/theta']
    size = len(file['/sinogram']) #number of slices

    # Compute starting and ending slices for this core
    label = size / total
    label_rest = size - label * total

    if nodeID < label_rest:
        slice_start = nodeID * (label + 1)
        slice_end = (nodeID + 1) * (label + 1) #doesn't count the last number
    else:
        slice_start = label_rest * (label + 1) + (nodeID - label_rest) * label
        slice_end = label_rest * (label + 1) + (nodeID - label_rest + 1) * label #range doesn't cound the last number

    for i in range(slice_start, slice_end):
        #t0 = time()
        name = 'slice_'+str(i)
        sinogram = file['/sinogram/'+name] #take one sinogram
        reconed_slice = pb.iradon(sinogram[...], theta[...])
#        print 'recon done for', i
        dict = {}
        dict['slice'] = reconed_slice
        scipy.io.savemat('sub_tomo/'+name, dict, oned_as='row')
        #t1 = time()
    
        #print i, ':', t1-t0                                                                                                                                       

    file.close() #hdf5 file                            

if __name__ == '__main__':
    filename = ''
    if len(sys.argv) < 2:
        filename = 'tomo.h5'
    else:
        filename = sys.argv[1]

    t0 = time()                                                                     
    recon2d(filename) 
    t1 = time()
    
    print t1-t0    
