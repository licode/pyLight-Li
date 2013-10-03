import numpy as npy
from matplotlib.colors import hsv_to_rgb
import matplotlib.pyplot as plt
import sys
import math

scan_num = sys.argv[1]
try_num = sys.argv[2]

dir_name = './result/data'
prb_file_name = 'recon_'+scan_num+'_'+try_num+'_probe_ave_rp'
obj_file_name = 'recon_'+scan_num+'_'+try_num+'_object_ave_rp'

data_prb = npy.load(dir_name+'/'+prb_file_name+'.npy')

H_mean = npy.mean(npy.angle(data_prb))
H = ((npy.angle(data_prb) - H_mean + math.pi) * 180. / math.pi)/360.

V = npy.abs(data_prb) / npy.max(npy.abs(data_prb))
S = npy.ones_like(V)

HSV = npy.dstack((H,S,V))
RGB = hsv_to_rgb(HSV)

plt.figure(20)
plt.imshow(npy.fliplr(npy.rot90(npy.flipud(RGB))))
plt.savefig('./result/images/'+prb_file_name+'_hsv.png')

#+++++++++++++++++++++++++++++++++

data_obj = npy.load(dir_name+'/'+obj_file_name+'.npy')

H_mean = npy.mean(npy.angle(data_obj))
H = ((npy.angle(data_obj) - H_mean + math.pi) * 180. / math.pi)/360.

V = npy.abs(data_obj) / npy.max(npy.abs(data_obj))
S = npy.ones_like(V)

HSV = npy.dstack((H,S,V))
RGB = hsv_to_rgb(HSV)

plt.figure(25)
plt.imshow(npy.fliplr(npy.rot90(npy.flipud(RGB))))
plt.savefig('./result/images/'+obj_file_name+'_hsv.png')

plt.show()
