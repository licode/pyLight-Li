import numpy as npy
from scipy import rand
import time
import pickle
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import scipy.misc as sm
import shutil
import scipy.fftpack as sf
import sys

class ptycho_trans_pc(object):

    def __init__(self,diffamp):
        
        self.verbose = True
        
        ##public attributes
        self.diff_array = diffamp  ##diffraction data
        self.nx_prb = None  ##number of pixels per side of array
        self.ny_prb = None  ##number of pixels per side of array
        self.num_points = None  ##number of scan points
        self.nx_obj = None  ## object x dimension
        self.ny_obj = None  ## object y dimension
        self.prb = None  ## probe array
        self.obj = None  ## object array
        self.prb_ave = None  ## averaged porbe
        self.obj_ave = None  ## averaged object
        self.prb_old = None  ## previous probe
        self.obj_old = None  ## previous object
        self.sign = None  ## saving file name
        self.scan_num = None ## scan number
        self.init_obj_flag = True  ## initialize random object flag
        self.init_prb_flag = True  ## initialize random probe flag
        self.update_product_flag = False ## update product flag
        self.product = None  ## product array
        self.beta = 1.e-8 ##general feedback parameter
        self.alpha = 1.0  ##espresso threshold coefficient
        self.n_iterations = 1000 ##number of iterations
        self.start_update_probe = 2 ## iteration number start updating probe
        self.end_update_probe = self.n_iterations  ## iteration number ends updating probe
        self.search_range = 10  ##search range for centering
        self.points =None  ## scan pattern
        self.point_info = None ## x,y start and end indecies
        self.sigma1 = 1.e-10  ## normalization weighting factor 1
        self.sigma2 = 5.e-5   ## normalization weighting factor 2
        self.amp_max = None  ## maximum object magnitude
        self.amp_min = None  ## minimum object magnitude
        self.pha_max = None  ## maximum object phase
        self.pha_min = None  ## minimum object phase
        self.ave_i = 0  ## average number
        self.error_obj = npy.zeros(self.n_iterations) ## chi square error for object
        self.error_prb = npy.zeros(self.n_iterations) ## chi square error for probe
        self.time_start = None  ## start time
        self.time_end = None  ## end time
        self.start_ave = 0.8  ## average starting iteration 
        self.display_error_flag = True ## display reconstruction result flag
        self.sf_flag = True ## use FFTW or numpy fft
        self.x_direction_flag = False
        
        ## experimental parameter
        self.x_range_um = None   # x scan range
        self.y_range_um = None   # y scan range
        self.dr_um = None        # radius increment
        self.nth = None          # number of points in the first ring
        self.x_roi = None        # x roi
        self.y_roi = None        # y roi
        self.lambda_nm = None    # wavelength
        self.z_m = None          # ccd distance
        self.ccd_pixel_um = None # ccd pixel size

        ## partial coherence parameter
        self.coh = None          # deconvolution kernal
        self.kernal_n = 16       # kernal size
        self.pc_sigma = 0.8      # kernal width
        self.n_coh = 20          # number of iteration for kernal updating loop
        self.pc_interval = 15    # how often to update coherence function 
        self.update_coh_flag = True  # update coherence function or not
        self.pc_flag = True          # use partial coherence or not
        self.conv_array1 = None
        self.conv_array2 = None
        self.conv_flag = True
        self.conv_complex_flag = False
        self.conv_norm_flag = True
        self.coh_real_space = None          # coherence function in real space
        self.coh_percent = 0.5                # percentage of points used for coherence updating
        self.coh_old = None  ## previous object
        self.error_coh = npy.zeros(self.n_iterations) ## chi square error for coherence
       
        # used to save pictures
        self.savepic = None
        self.savezip = None
 
    # calculate scan parttern
    def cal_scan_pattern(self):

        x_real_space_pixel_nm = self.lambda_nm * self.z_m * 1.e6 / (self.x_roi * self.ccd_pixel_um)
        y_real_space_pixel_nm = self.lambda_nm * self.z_m * 1.e6 / (self.y_roi * self.ccd_pixel_um)
   
        r_max_um = npy.sqrt((self.x_range_um/2.)**2+(self.y_range_um/2.)**2)
        num_ring = 1+int(r_max_um / self.dr_um)

        self.points = npy.zeros((2,self.num_points))
        i_positions = 0
        for i_ring in range(1,num_ring+2):
            radius_um = i_ring * self.dr_um
            angle_step = 2.* math.pi / (i_ring * self.nth)
            for i_angle in range(int(i_ring * self.nth)):
                angle = i_angle * angle_step
                x_um = radius_um * npy.cos(angle)
                y_um = radius_um * npy.sin(angle)
                if abs(x_um) <= (self.x_range_um/2): 
                    if abs(y_um) <= (self.y_range_um/2):
                        if self.x_direction_flag:
                            self.points[0,i_positions] = npy.round(-1.*x_um * 1.e3 / x_real_space_pixel_nm)
                        else:
                            self.points[0,i_positions] = npy.round(x_um * 1.e3 / x_real_space_pixel_nm)
                        self.points[1,i_positions] = npy.round(y_um * 1.e3 / y_real_space_pixel_nm)
                        i_positions = i_positions + 1

    # calculate mesh scan parttern
    def cal_scan_pattern_mesh(self):

        x_real_space_pixel_nm = self.lambda_nm * self.z_m * 1.e6 / (self.x_roi * self.ccd_pixel_um)
        y_real_space_pixel_nm = self.lambda_nm * self.z_m * 1.e6 / (self.y_roi * self.ccd_pixel_um)

        x_num_points = npy.int(self.x_range_um / self.x_dr_um)
        y_num_points = npy.int(self.y_range_um / self.y_dr_um)

        self.points = npy.zeros((2,1000))
        i_positions = 0
        for iy in range(y_num_points+1):
            #for ix in range(x_num_points): #combine case
            for ix in range(x_num_points+1):
                self.points[0,i_positions] = npy.round((ix - x_num_points/2) * self.x_dr_um * 1.e3 / x_real_space_pixel_nm)
                self.points[1,i_positions] = npy.round((iy - y_num_points/2) * self.y_dr_um * 1.e3 / y_real_space_pixel_nm)        
                i_positions += 1
     
    # difference map for ptychography
    def recon_dm_trans(self):

        for i, (x_start, x_end, y_start, y_end) in enumerate(self.point_info):
            prb_obj =  self.prb[:,:] * self.obj[x_start:x_end,y_start:y_end]
            tmp = 2. * prb_obj - self.product[i]

            if self.sf_flag:
                tmp_fft = sf.fftn(tmp) / npy.sqrt(npy.size(tmp))
            else:
                tmp_fft = npy.fft.fftn(tmp) / npy.sqrt(npy.size(tmp))
    
            amp_tmp = npy.abs(tmp_fft)
            ph_tmp = tmp_fft / (amp_tmp+self.sigma1)
            (index_x,index_y) = npy.where(self.diff_array[i] >= 0.)
            dev = amp_tmp - self.diff_array[i]
            power = npy.sum(npy.sum((dev[index_x,index_y])**2))/(self.nx_prb*self.ny_prb)
    
            if power > self.sigma2: 
                amp_tmp[index_x,index_y] = self.diff_array[i][index_x,index_y] + dev[index_x,index_y] * npy.sqrt(self.sigma2/power)

            if self.sf_flag:
                tmp2 =  sf.ifftn(amp_tmp*ph_tmp) *  npy.sqrt(npy.size(tmp))
            else:
                tmp2 = npy.fft.ifftn(amp_tmp*ph_tmp) * npy.sqrt(npy.size(tmp))
                    
            self.product[i] += self.beta*(tmp2 - prb_obj)

        del(prb_obj)
        del(tmp)
        del(amp_tmp)
        del(ph_tmp)
        del(tmp2)

    # update object
    def cal_object_trans(self):

        obj_update =npy.zeros([self.nx_obj,self.ny_obj]).astype(complex)
        norm_probe_array = npy.zeros((self.nx_obj,self.ny_obj)) + self.alpha
        prb_sqr = npy.abs(self.prb) ** 2
        prb_conj = self.prb.conjugate()
        for i, (x_start, x_end, y_start, y_end) in enumerate(self.point_info):
            norm_probe_array[x_start:x_end,y_start:y_end] += prb_sqr
            obj_update[x_start:x_end,y_start:y_end] += prb_conj * self.product[i]

        obj_update = obj_update / norm_probe_array
  
        (index_x,index_y) = npy.where(abs(obj_update) > self.amp_max)
        obj_update[index_x,index_y] = obj_update[index_x,index_y] * self.amp_max / npy.abs(obj_update[index_x,index_y])
        (index_x,index_y) = npy.where(abs(obj_update) < self.amp_min)
        obj_update[index_x,index_y] = obj_update[index_x,index_y] * self.amp_min / npy.abs(obj_update[index_x,index_y]+1.e-8)

        (index_x,index_y) = npy.where(npy.angle(obj_update) > self.pha_max)
        obj_update[index_x,index_y] = npy.abs(obj_update[index_x,index_y]) * npy.exp(1.j*self.pha_max)
        (index_x,index_y) = npy.where(npy.angle(obj_update) < self.pha_min)
        obj_update[index_x,index_y] = npy.abs(obj_update[index_x,index_y]) * npy.exp(1.j*self.pha_min)

        self.obj = obj_update

    #update probe
    def cal_probe_trans(self):

        weight = 0.1
        probe_update = weight * self.num_points * self.prb
        norm_obj_array = npy.zeros((self.nx_prb,self.ny_prb)) + weight * self.num_points
        obj_sqr = npy.abs(self.obj) ** 2
        obj_conj = npy.conjugate(self.obj)
        for i, (x_start, x_end, y_start, y_end) in enumerate(self.point_info):
            probe_update[:,:] += self.product[i] *obj_conj[x_start:x_end,y_start:y_end]
            norm_obj_array[:,:] += obj_sqr[x_start:x_end,y_start:y_end]

        probe_update = probe_update / norm_obj_array

        self.prb = probe_update

    # calculate object/probe dimensions
    def cal_obj_prb_dim(self):
        self.nx_obj = self.x_roi + npy.max(self.points[0,:]) - npy.min(self.points[0,:])
        self.ny_obj = self.y_roi + npy.max(self.points[1,:]) - npy.min(self.points[1,:])
        self.nx_obj = self.nx_obj + npy.mod(self.nx_obj,2)
        self.ny_obj = self.ny_obj + npy.mod(self.ny_obj,2)
        self.points[0,:] = self.points[0,:] + self.nx_obj / 2
        self.points[1,:] = self.points[1,:] + self.ny_obj / 2
        self.nx_prb = self.x_roi
        self.ny_prb = self.y_roi

        self.point_info = npy.array([(int(self.points[0,i] - self.nx_prb/2), int(self.points[0,i] + self.nx_prb/2), \
                                      int(self.points[1,i] - self.ny_prb/2), int(self.points[1,i] + self.ny_prb/2)) \
                                for i in range(self.num_points)])

    def init_obj(self):
        self.obj = npy.random.uniform(0,0.5,(self.nx_obj, self.ny_obj)) * \
            npy.exp(npy.random.uniform(0,0.5,(self.nx_obj, self.ny_obj))*1.j)
        
    def init_prb(self):
        #self.prb = npy.random.uniform(0,0.5,(self.nx_prb, self.ny_prb)) * \
        #    npy.exp(npy.random.uniform(0,0.5,(self.nx_prb, self.ny_prb))*1.j)
        self.prb = npy.zeros((self.nx_prb,self.ny_prb)).astype(complex) + 0.1
        self.prb[self.nx_prb/2-20:self.nx_prb/2+20,self.ny_prb/2-20:self.ny_prb/2+20] = 1.
 
    def init_product(self):
        self.product = [0 for i in range(self.num_points)]
        for i, (x_start, x_end, y_start, y_end) in enumerate(self.point_info):
            self.product[i] = self.prb[:,:] * self.obj[x_start:x_end,y_start:y_end]

    def cal_obj_error(self,it):
        self.error_obj[it] = npy.sqrt(npy.sum(npy.sum(npy.abs(self.obj - self.obj_old)**2))) / \
            npy.sqrt(npy.sum(npy.sum(npy.abs(self.obj)**2)))

    def cal_prb_error(self,it):
        self.error_prb[it] = npy.sqrt(npy.sum(npy.sum(npy.abs(self.prb - self.prb_old)**2))) / \
            npy.sqrt(npy.sum(npy.sum(npy.abs(self.prb)**2)))

    def save_recon_pc(self):

        save_root_dir = './result'
        if not os.path.exists(save_root_dir):
            os.makedirs(save_root_dir)

        save_dir = './result/data/'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_pic_dir = './result/images/'
        if not os.path.exists(save_pic_dir):
            os.makedirs(save_pic_dir)

        npy.save(save_dir+'recon_'+self.scan_num+'_'+self.sign+'_object_ave',self.obj_ave)
        npy.save(save_dir+'recon_'+self.scan_num+'_'+self.sign+'_probe_ave',self.prb_ave)
        npy.save(save_dir+'recon_'+self.scan_num+'_'+self.sign+'_object',self.obj)
        npy.save(save_dir+'recon_'+self.scan_num+'_'+self.sign+'_probe',self.prb)
        npy.save(save_dir+'error_'+self.scan_num+'_'+self.sign+'_object',self.error_obj)
        npy.save(save_dir+'error_'+self.scan_num+'_'+self.sign+'_probe',self.error_prb)
        if(self.update_coh_flag):
            npy.save(save_dir+'error_'+self.scan_num+'_'+self.sign+'_coh',self.error_coh)
        npy.save(save_dir+'time_'+self.scan_num+'_'+self.sign,self.time_end-self.time_start)
        if self.pc_flag:
            npy.save(save_dir+'recon_'+self.scan_num+'_'+self.sign+'_coh_fft',self.coh)
            tmp = npy.zeros((self.nx_prb,self.ny_prb))
            tmp[self.nx_prb/2-self.kernal_n/2:self.nx_prb/2+self.kernal_n/2, \
                self.ny_prb/2-self.kernal_n/2:self.ny_prb/2+self.kernal_n/2] = self.coh
            self.coh_real_space = npy.abs(npy.fft.fftshift(npy.fft.fftn(npy.fft.fftshift(tmp))))
            del(tmp)
            npy.save(save_dir+'recon_'+self.scan_num+'_'+self.sign+'_coh',self.coh_real_space)

        shutil.copy2('./'+self.recon_code+'.py',save_dir+self.recon_code+'_'+self.sign+'.py')

        sys.argv = ['rm_phase_ramp_recon_all.py',self.scan_num, self.sign, self.savepic]
        execfile("rm_phase_ramp_recon_all.py")
        sys.argv = ['save_hue_auto.py',self.scan_num, self.sign]
        execfile("save_hue_auto.py")

    def display_recon_pc(self):

        if self.pc_flag:
            plt.figure(1)
            plt.subplot(221)
            plt.imshow(npy.abs(self.prb_ave))
            plt.subplot(222)
            plt.imshow(npy.abs(self.obj_ave))
            plt.subplot(223)
            plt.imshow(npy.abs(self.coh_real_space))
            plt.subplot(224)
            x_real_space_pixel_nm = self.lambda_nm * self.z_m * 1.e6 / (self.x_roi * self.ccd_pixel_um)
            y_real_space_pixel_nm = self.lambda_nm * self.z_m * 1.e6 / (self.y_roi * self.ccd_pixel_um)
            x_display_um = (npy.arange(self.nx_prb) - self.nx_prb/2) * x_real_space_pixel_nm / 1.e3
            y_display_um = (npy.arange(self.ny_prb) - self.ny_prb/2) * y_real_space_pixel_nm / 1.e3
            plt.plot(x_display_um,npy.abs(self.coh_real_space[:,self.ny_prb/2]))
            plt.plot(y_display_um,npy.abs(self.coh_real_space[self.nx_prb/2,:]))
            #plt.axis([-8,8,0,1])
        else:
            plt.figure(1)
            plt.subplot(121)
            plt.imshow(npy.abs(self.prb_ave))
            plt.subplot(122)
            plt.imshow(npy.abs(self.obj_ave))

        save_pic_dir = './result/images/'
        if not os.path.exists(save_pic_dir):
            os.makedirs(save_pic_dir)
        plt.savefig(save_pic_dir+'recon_'+self.scan_num+'_'+self.sign+'.png')
        plt.show()

    # ptycho reconstruction
    def recon_ptycho_pc(self):
        if self.mesh_flag:
            self.cal_scan_pattern_mesh()
        else:
            self.cal_scan_pattern()
        self.cal_obj_prb_dim()
        if(self.init_prb_flag):
            self.init_prb()
        if(self.init_obj_flag):
            self.init_obj()

        self.init_product()
        if(self.pc_flag):
            self.init_kernal()

        self.time_start = time.time()
        for it in range(self.n_iterations):
            self.prb_old = self.prb.copy()
            self.obj_old = self.obj.copy()
            if(self.update_coh_flag):
                self.coh_old = self.coh.copy()
                
            if(self.pc_flag):
                self.recon_dm_trans_pc()
                if(self.update_coh_flag):
                    if it > 0:
                        if npy.mod(it, self.pc_interval) == 0:
                            self.cal_coh()
            else:
                self.recon_dm_trans()
                
            if(it >= self.start_update_probe):
                self.cal_object_trans()
                self.cal_probe_trans()
            else:
                self.cal_object_trans()

            self.cal_obj_error(it)
            self.cal_prb_error(it)
            if(self.update_coh_flag):
                self.cal_coh_error(it)

            if it == npy.floor(self.start_ave*self.n_iterations):
                self.obj_ave = self.obj.copy()
                self.prb_ave = self.prb.copy()
                self.ave_i = 1.
            
            if it > npy.floor(self.start_ave*self.n_iterations):
                self.obj_ave = self.obj_ave + self.obj
                self.prb_ave = self.prb_ave + self.prb
                self.ave_i = self.ave_i + 1

            if(self.update_coh_flag):
                print it,'object_chi=',self.error_obj[it],'probe_chi=',self.error_prb[it],'coh_chi=',self.error_coh[it]
            else:
                print it,'object_chi=',self.error_obj[it],'probe_chi=',self.error_prb[it]

            if self.update_product_flag:
                if npy.mod(it,5) == 0:
                    self.init_product()

        self.obj_ave = self.obj_ave / self.ave_i
        self.prb_ave = self.prb_ave / self.ave_i
        self.time_end = time.time()
        
        print '++++++++++++++++++++++++++++++++++++++++++++++++++'
        print 'object size:', self.nx_obj,'x',self.ny_obj
        print 'probe size:', self.nx_prb,'x',self.ny_prb
        print 'total scan points:', self.num_points
        print self.n_iterations, 'iterations take', self.time_end - self.time_start, 'sec'
        print '++++++++++++++++++++++++++++++++++++++++++++++++++'



            
