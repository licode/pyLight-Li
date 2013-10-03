import numpy as npy
#import cstuff as c
import align_class as ac
import matplotlib.pyplot as plt
import sys

#plt.ion()

scan_num = sys.argv[1]
try_num = sys.argv[2]

dir_name = './result/data/'
file_name = 'recon_'+scan_num+'_'+try_num
prb_file_name = 'recon_'+scan_num+'_'+try_num+'_probe_ave'
obj_file_name = 'recon_'+scan_num+'_'+try_num+'_object_ave'
#f=file(file_name+'.bin')
#ndim,nx,ny,nbytes,ntotal = npy.fromfile(f,dtype='int32',count=5).byteswap()
#print ndim,nx,ny,nbytes,ntotal
#data_tmp = npy.fromfile(f,dtype=npy.complex64).byteswap()
#f.close()

#data_tmp.resize(ny,nx)

data_tmp = npy.load(dir_name+'/'+prb_file_name+'.npy')
nx,ny=npy.shape(data_tmp)

if npy.mod(nx, 2) == 1:
    nx = nx - 1
if npy.mod(ny, 2) == 1:
    ny = ny - 1

prb_data = data_tmp[0:nx,0:ny]

amp = npy.abs(prb_data)
pha = npy.angle(prb_data)

'''
plt.figure(11)
plt.subplot(121)
plt.imshow(amp)
plt.subplot(122)
plt.imshow(pha)
'''

prb_array = ac.remove_phase_ramp(amp * npy.exp(1j*pha),0,0.1,1)
#index = npy.where(abs(array) < 0.1)
#array[index] = complex(0.,0.)

data_tmp = npy.load(dir_name+'/'+obj_file_name+'.npy')
nx,ny=npy.shape(data_tmp)

if npy.mod(nx, 2) == 1:
    nx = nx - 1
if npy.mod(ny, 2) == 1:
    ny = ny - 1

obj_data = data_tmp[0:nx,0:ny]

amp = npy.abs(obj_data)
pha = npy.angle(obj_data)

'''
plt.figure(11)
plt.subplot(121)
plt.imshow(amp)
plt.subplot(122)
plt.imshow(pha)
'''

obj_array = ac.remove_phase_ramp(amp * npy.exp(1j*pha),0,0.1,1)

plt.figure(12)
plt.subplot(221)
plt.imshow(npy.flipud(npy.transpose(npy.abs(prb_array))))
plt.colorbar()
plt.subplot(222)
plt.imshow(npy.flipud(npy.transpose(npy.angle(prb_array))))
plt.colorbar()
plt.subplot(223)
plt.imshow(npy.flipud(npy.transpose(npy.abs(obj_array))))
plt.colorbar()
plt.subplot(224)
plt.imshow(npy.flipud(npy.transpose(npy.angle(obj_array))))
plt.colorbar()

plt.savefig('./result/images/'+file_name+'_rp.png')
plt.savefig(sys.argv[3])

npy.save(dir_name+'/'+prb_file_name+'_rp',prb_array)
npy.save(dir_name+'/'+obj_file_name+'_rp',obj_array)

#array_save = c.Sp4Array()
#c.numpy_ToSp4(array,array_save)

#c.Sp4ArraySave(array_save,file_name+'.sp4')

plt.show()
