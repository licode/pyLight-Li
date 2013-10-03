from ptycho_trans_pc import ptycho_trans_pc
import numpy as npy
import sys
import os
import zipfile
import shutil

# Exmaple usage: 
# python recon_ptycho_pc.py <data file> <object config file> <probe
# config file> <scan number> <replicated number>
# <iterations> <image output> <zip output>
# <data file>: correspond to "assemble_array_221_64*64.npy" in the example
# <object config file>: if this value is "default", then do
# random guess on object, else load the obj
# <probe config file>: if this value is "default", then do
# random guess on probe, else load the probe
# <image output>: correspond to "recon_221_r1_rp.png" in the example,
# this should be a separate output file, besides being compressed in the
# zip.
# <zip output>: the zip filename for all output, correspond to recon_result.tar.gz


#loading data
#tmp = npy.load('./assemble_array_'+sys.argv[1]+'_64x64.npy')
tmp = npy.load(sys.argv[1])
nx,ny,nz = npy.shape(tmp)

#shift data center to corner
for i in range(nz):
    tmp[:,:,i] = npy.fft.fftshift(tmp[:,:,i])
    
#create data list
diffamp = [npy.copy(tmp[:,:,i]) for i in range(nz)]
del(tmp)

recon = ptycho_trans_pc(diffamp)
recon.nx_prb = nx
recon.ny_prb = ny
recon.num_points = nz

recon.scan_num = sys.argv[4]  #scan number
recon.sign = sys.argv[5]      #saving file name
recon.x_range_um = 10.        #scan range in x direction (um)
recon.y_range_um = 10.        #scan range in y direction (um)
recon.mesh_flag = False       #True to use mesh scan pattern, False to use spiral scan
recon.x_dr_um = 0.1           #scan step size in x direction (um)
recon.y_dr_um = 0.4           #scan step size in y direction (um)
recon.dr_um = 0.4             #radius increment size (um)
recon.nth = 5.                #number of points in first ring
recon.x_roi = nx              #data array size in x
recon.y_roi = ny              #data array size in y
recon.lambda_nm = 0.1378      #x-ray wavelength (nm)
recon.z_m = 2.                #detector-to-sample distance (m)
recon.ccd_pixel_um = 55.      #detector pixel size (um)

recon.amp_max = 1.            #up limit of allowed object amplitude range
recon.amp_min = 0.6           #low limit of allowed object amplitude range
recon.pha_max = 0.5           #up limit of allowed object phase range
recon.pha_min = -3.14         #low limit of allowed object phase range

#parameters for partial coherence calculation
recon.pc_flag = False
recon.update_coh_flag = False
recon.kernal_n = 16           #kernal size
recon.pc_sigma = 0.2          #initial guess of kernal sigma

#reconstruction feedback parameters
recon.alpha = 1.e-8
recon.beta = 1.

recon.n_iterations = npy.int(sys.argv[6])   #number of iterations
recon.start_update_probe = 2                #iteration number for probe updating

# Saved image file name and


# Processing the object file and probe file
# if they exist, load to the reconstruction class

if "default.npy" in sys.argv[2]:
    recon.init_obj_flag = True                 #True to start with a random guess. False to load a pre-existing array
else:
    recon.init_obj_flag = False                 #True to start with a random guess. False to load a pre-existing array
    recon.obj = npy.load(sys.argv[2])

recon.init_obj_flag = True                  #True to start with a random guess. False to load a pre-existing array

if "default.npy" in sys.argv[3]:
    recon.init_prb_flag = True                 #True to start with a random guess. False to load a pre-existing array
else:
    recon.init_prb_flag = False                 #True to start with a random guess. False to load a pre-existing array
    recon.prb = npy.load(sys.argv[3])

recon.savepic = sys.argv[7]

recon.savezip = sys.argv[8]

recon.sf_flag = True

recon.recon_code = 'recon_ptycho_pc'        #Copy the code

recon.recon_ptycho_pc()

recon.save_recon_pc()

recon.display_recon_pc()

zf = zipfile.ZipFile(recon.savezip, "w")
for dirname, subdirs, files in os.walk("result/"):
    zf.write(dirname)
    for filename in files:
        zf.write(os.path.join(dirname, filename))
zf.close()

shutil.rmtree("result")

