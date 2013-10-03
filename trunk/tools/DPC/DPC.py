#! /usr/bin/env python

import os
import sys
import shutil
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imsave
from scipy.optimize import fmin
from time import time
from mpi4py import MPI
import h5py


class DPC:
    def __init__(self):
        self.file = None
        self.outfile = None
        self.refstart = 1
        self.yrange1 = 46
        self.yrange2 = 61
        self.startpoint = [1, 0]
        self.maxiter = 1000
        self.maxfun = 1000
        self.disp = 0
        self.__directory = '.'
    
    def __del__(self):
        if self.file is not None:
            self.file.close()
        if self.outfile is not None:
            self.outfile.close()
        
    def loadMeta(self):
        self.row = self.file['/row'][0]
        self.column = self.file['/column'][0]
        self.L = self.file['/L'][0]
        self.p = self.file['/p'][0]
        self.dx = self.file['/dx'][0]
        self.dy = self.file['/dy'][0]
        self.energy = self.file['/energy'][0]
        self.lambda_ = self.file['/lambda'][0]
        
        # prepare final output
        self.totalnum = self.row*self.column
        self.a = np.zeros(self.totalnum, dtype='d')
        self.gx = np.zeros(self.totalnum, dtype='d')
        self.gy = np.zeros(self.totalnum, dtype='d')
    
    def fitPairs(self, fx1, fy1, fx2, fy2):
        vx = fmin(self.RSS, self.startpoint, args = (fx1, fx2), maxiter = self.maxiter, maxfun = self.maxfun, disp = self.disp)  
        vy = fmin(self.RSS, self.startpoint, args = (fy1, fy2), maxiter = self.maxiter, maxfun = self.maxfun, disp = self.disp)     
                                                                                
        vx[1] = -vx[1] * len(fx1) * self.p / (self.lambda_*self.L)                         
        vy[1] = vy[1] * len(fy1) * self.p / (self.lambda_*self.L)  
        
        return [vx[0], vx[1], vy[1]] 
    
    def decompose(self, image):
        '''
        Preparation of each image before fitting
        '''
        xline1 = [sum(x) for x in zip(*image)]
        yline1 = [sum(x) for x in image]
        yline1 = yline1[self.yrange1 : self.yrange2]

        fx1 = np.fft.fftshift(np.fft.ifft(xline1))
        fy1 = np.fft.fftshift(np.fft.ifft(yline1))
        
        return [fx1, fy1]
    
    def RSS(self, v, xdata, ydata):
        '''
        Define the function to be minimized in the Nelder Mead algorithm
        '''
        length = len(xdata)
        fittedCurve = np.zeros(length, dtype=complex)
        for i in range(length):
            temp = v[0] * xdata[i] * np.exp(1j*v[1]*(i+1-(np.floor(length/2.0)+1)))
            fittedCurve[i] = temp
        rss = (abs(ydata-fittedCurve)**2).sum()
        return rss

    def fitAll(self, inputfile):
        '''
        Main DPC process:
        1. fitting
        2. reconstruction
        Input is a hdf5 file
        '''
        t0 = time()
    
        self.file = h5py.File(inputfile)
        self.loadMeta()
        
        # read the reference image: only one reference image
        refname = 'SOFC_' + '%05d' % self.refstart
        refdata = self.file['/Data/' + refname]
        [fx1, fy1] = self.decompose(refdata[...])
                                                                                
        # set up environmental parameters
        comm = MPI.COMM_WORLD
        frame_start = 0
        frame_end = 0
        nodeID = comm.Get_rank()
        # environment related numbers
        ntotal = comm.Get_size()
        label_x = self.column * self.row / ntotal #int type
        label_rest = self.column * self.row - label_x * ntotal
    
        if nodeID < label_rest:
            frame_start = nodeID*(label_x+1) + 1
            frame_end = (nodeID+1)*(label_x+1) + 1 #range doesn't count the last number
        else:
            frame_start = label_rest*(label_x+1) + (nodeID-label_rest)*label_x + 1
            frame_end = label_rest*(label_x+1) + (nodeID-label_rest+1)*label_x + 1 #range doesn't count the last number
        
        # create corresponding file to save a, gx and gy
        #if not os.path.exists(directory):
            #os.mkdir(directory)
        out_file_name = self.__directory + '/' + str(nodeID) + '.txt'
        out_file = open(out_file_name, 'wb')
        
        for framenum in range(frame_start, frame_end):                                     
            franame = 'SOFC_' + '%05d' % framenum                                          
            filedata = self.file['/Data/' + franame]                              
            [fx2, fy2] = self.decompose(filedata[...])                                          
                                                                                                                                                                                                               
            [vx0, vx1, vy1] = self.fitPairs(fx1, fy1, fx2, fy2)                       
                                                                                
            out_file.write(str(vx0))
            out_file.write(' ')                                                     
            out_file.write(str(vx1))
            out_file.write(' ')                                                    
            out_file.write(str(vy1)) 
            out_file.write(' ')           
    
        out_file.close()
    
        t1 = time()
        print nodeID, ' spent ', t1-t0 
   
        # synchronize threads
        comm.Barrier()
        
    def mergeDiffPhase(self, node_num = 1, outname = 'output.h5', namea = 'a.tif', namegx = 'gx.tif', namegy = 'gy.tif'):
        '''
        collect results from all the nodes
        '''
        i = 0
        for n in range(int(node_num)):
            filename = self.__directory + '/' + str(n) + '.txt'
            txtfile = open(filename, 'rb')
            result = np.array(txtfile.read().split(), dtype='d')
    
            for m in range(len(result)):
                if m % 3 == 0:
                    self.a[i] = result[m]
                elif m % 3 == 1:
                    self.gx[i] = result[m]
                elif m % 3 == 2:        
                    self.gy[i] = result[m]
                    i += 1
            
            txtfile.close()

        self.a = self.a.reshape(self.row, self.column)
        imsave(namea, self.a)
        self.gx = self.gx.reshape(self.row, self.column)
        imsave(namegx, self.gx)
        self.gy = self.gy.reshape(self.row, self.column)
        imsave(namegy, self.gy)
        
        # save to hdf5 format
        self.outfile = h5py.File(outname, 'w')
        self.outfile.create_dataset('/a', self.a.shape, self.a.dtype, self.a)
        self.outfile.create_dataset('/gx', self.gx.shape, self.gx.dtype, self.gx)
        self.outfile.create_dataset('/gy', self.gy.shape, self.gy.dtype, self.gy)
        
        # clean up the temporary folder
#        shutil.rmtree('experiment')
#        if not os.path.exists('experiment'):
#            os.makedirs('experiment')
#            os.system('touch Readme.md') #for github, folder couldn't be empty
#        op = 'rm ' + self.__directory + '/*.txt'
#        os.system(op)

    def reconstructPhi(self, namephi = 'phi.tif'):
        '''
        reconstruct the final phase image using gx and gy
        '''
        w = 1 # Weighting parameter
        tx = np.fft.fftshift(np.fft.fft2(self.gx))
        ty = np.fft.fftshift(np.fft.fft2(self.gy))
        c = np.arange(self.totalnum, dtype=complex).reshape(self.row, self.column)
        for i in range(self.row):
            for j in range(self.column):
                kappax = 2 * np.pi * (j+1-(np.floor(self.column/2.0)+1)) / (self.column*self.dx)
                kappay = 2 * np.pi * (i+1-(np.floor(self.row/2.0)+1)) / (self.row*self.dy)
                if kappax == 0 and kappay == 0:
                    c[i, j] = 0
                else:
                    cTemp = -1j * (kappax*tx[i][j]+w*kappay*ty[i][j]) / (kappax**2 + w*kappay**2)
                    c[i, j] = cTemp
        c = np.fft.ifftshift(c)
        self.phi = np.fft.ifft2(c)
        self.phi = self.phi.real
        imsave(namephi, self.phi)
        
        if self.outfile is None:
            raise 'Not yet create a h5 file! Run merge function first!'
        
        self.outfile.create_dataset('/phi', self.phi.shape, self.phi.dtype, self.phi)
        
    def collect(self, outname = 'output.h5', namea = 'a.tif', namegx = 'gx.tif', namegy = 'gy.tif', namephi = 'phi.tif'):
        '''
        For MPI call
        '''
        comm = MPI.COMM_WORLD
        nodeID = comm.Get_rank()
        node_num = comm.Get_size()
        
        if nodeID == 0:
            self.mergeDiffPhase(node_num, outname, namea, namegx, namegy)
            self.reconstructPhi(namephi)
            filelist = glob.glob("*.txt")
            for f in filelist:
                os.remove(f)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        inputfile = sys.argv[1]
    else:
        inputfile = 'dpc.h5'

    if len(sys.argv) >= 3:
        outputfile = sys.argv[2]
    else:
        outputfile = 'result_dpc.h5'

    if len(sys.argv) >= 4:
        namea = sys.argv[3]

    if len(sys.argv) >= 5:
        namegx = sys.argv[4]

    if len(sys.argv) >= 6:
        namegy = sys.argv[5]
 
    if len(sys.argv) >= 7:
        namephi = sys.argv[6]

    dpc = DPC()
    dpc.fitAll(inputfile)
    dpc.collect(outputfile, namea, namegx, namegy, namephi)
