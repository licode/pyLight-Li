#! usr/bin/env python

import time
import numpy as np
import sys
from scipy import interpolate
import matplotlib.pyplot as pl

display_flag = False

def radon (image, theta = np.arange (180)):
        theta = np.asarray (theta)
        
        if (not (isinstance (image, np.ndarray)) or (image.ndim != 2)):
                raise TypeError ("radon: first arg must be an MxN array")
        
        if (np.ndim (theta) != 1):
                raise TypeError ("radon: second arg must be a 1D vector");
        
        n, m = np.shape (image)
        
        # Center of image
        xc = (m + 1) / 2
        yc = (n + 1) / 2
        
        # Divide each pixel into 2x2 subpixels
        img_hires = (image.repeat (2, axis = 0)).repeat (2, axis = 1)
        
        x_max = np.ceil (np.hypot (*image.shape) / 2 + 1)
        
        Y,X = np.mgrid [0 : (n - 0.5) : 2j * n,  0 : (m - 0.5) : 2j * m]
        Y += 0.75 - yc
        X += 0.75 - xc
        
        Y = Y.flatten ()
        X = X.flatten ()
        img_hires = img_hires.flatten ()
        
        th = theta * np.pi / 180.
        
        projections = np.zeros ((2*x_max + 1, len (theta)))
        
        for i in range (len (theta)):
                # project each pixel to vector (-sin(th),cos(th))
                s = -np.sin (th [i]) * X + np.cos (th [i]) * Y + x_max
                indices_int = s.astype (int)
                frac = s - indices_int
                
                top_ind = np.max (indices_int)
                projections [0:top_ind + 1, i] =  np.bincount (indices_int, img_hires * (1 - frac))
                #img_hires*(1-frac) like weight for bincount
                projections [0:top_ind + 2, i] += np.bincount (indices_int + 1, img_hires * frac)
                if display_flag:
                    if i % 20 == 0:
                        print '.' # finish 20 projection

        return projections




def iradon (proj, theta = None, interp = "linear", filt = "Ram-Lak", 
            scaling = 1, output_size = None, ret_filter = False):
        
        if (theta is None):
                theta = np.linspace (0, 180, proj.shape [1], endpoint = False)
                
        elif (np.isscalar (theta) and (proj.shape [1] != 1)):
                theta = np.arange (proj.shape [1], dtype = 'float') * theta
                
        else:
                theta = np.array (theta*1.0)
    
        if (output_size is None):
                output_size = _determine_outsize (proj, theta)
        
        if (len (theta) != proj.shape [1]):
                raise RuntimeError ("iradon: Number of projections does not match number of angles")
        
        if (not np.isscalar (scaling)):
                raise TypeError ("iradon: Frequency scaling value must be a scalar")
        
        ## Convert angles to radians
        theta *= np.pi / 180
        
        ## First, filter the projections
        #filtered, filt_tf = rho_filter (proj, filt, scaling, True)
        filtered, filt_tf = m_rho_filter (proj, filt, scaling, True)
        
        
        ## Next, back-project
        #recon = _back_project (filtered, theta, interp, output_size);
        recon = _back_project (filtered, theta, interp, output_size);
        
        if (ret_filter):
                return recon, filt_tf
        else:
                return recon


def _determine_outsize (proj, theta):
        """
        Makes an informed guess as to the size of the required
        output image for iradon.
        """
        by_hypot = 2 * int (proj.shape [0] / (2 * np.sqrt (2)))
        closest_to_0 = np.argmin (abs (theta))
        if (-5 < theta [closest_to_0] < 5):
                min_width = _get_width (proj, closest_to_0)
        else:
                min_width = by_hypot
        
        closest_to_90 = np.argmin (abs (theta - 90))
        if (85 < theta [closest_to_90] < 95):
                min_height = _get_width (proj, closest_to_90)
        else:
                min_height = by_hypot
        
        return max (by_hypot, min_width, min_height)


def _get_width (proj, ind):
        """
        Returns the width of the non-zero part of the projection
        in column `ind'.
        """
        nonzero = np.nonzero (proj [:,ind])
        return np.max (nonzero) - np.min (nonzero) + 1


def _back_project (proj, theta, interpolation, dim):
        """
        Performs the back-projection step of the filtered back-
        projection algorithm.
        """
        ## Make an empty image
        recon = np.zeros ((dim, dim))
        
        ## Zero pad the projections if the requested image
        ## has a diagonal longer than the projections
        diagonal = np.ceil (dim * np.sqrt (2))
        if (proj.shape [0] < diagonal):
                diff = int (2 * np.ceil ((diagonal - proj.shape [0]) / 2))
                z = np.zeros ((diff / 2, proj.shape [1]))
                proj = np.append (z, proj, axis = 0)
                proj.resize ((proj.shape [0] + diff / 2, proj.shape [1]))
                del z
        
        ## Create the x & y values for each pixel
        centre = (dim + 1) / 2  # dim is integer, so will auto-floor
        
        #y,x = np.mgrid [dim - 1:-1:-1, 0:dim]
        y,x = np.mgrid [0:dim, 0:dim]
        x -= centre
        y -= centre
        
        ## s axis for projections, needed by interp1
        s = np.arange (proj.shape [0]) - proj.shape [0] / 2 #projection pixel locations
    
        if display_flag:
            pl.ion()
            pl.figure(10)
            pl.xlabel('Online Reconstruction')
            pl.imshow(recon, cmap = pl.cm.gray)
            pl.draw()
    
        ## Sum each projection's contribution
        s_dash = np.empty (x.shape) #voxel projected locations
        for i in range (len (theta)):
                np.subtract (y * np.cos (theta [i]), x * np.sin (theta [i]), s_dash)
                interpolated = interp1 (s_dash, s, proj [:, i], interpolation)
                np.add (recon, interpolated, recon)
        
                if display_flag:
                    if i % 10 == 0:
                        pl.imshow(recon, cmap = pl.cm.gray)
                        time.sleep(3)
                        pl.draw()
                        print '.' # finish 20 backprojection
    
        ## Scale the reconstructed values to their original size
        recon *= np.pi / ( 2 * len (theta))

        if display_flag:
            pl.imshow(recon, cmap = pl.cm.gray)
            pl.draw()
            pl.ioff()
            #for i in range(len(recon)):
            #for j in range(len(recon)):
            #   if recon[i,j] < 0:
#       recon[i,j] = 0

#       print "max", np.amax(recon), "min", np.amin(recon)
        return recon


def interp1 (x_new, x, y, interp_type):
        """
          interp1 (x_new, x, y, interp_type)
        
        Performs 1D interpolation.
        """
        if (interp_type.lower () == "nearest"):
                np.around (x_new, out = x_new)
                y_new = y [x_new.astype (int)]
        elif (interp_type.lower () == "linear"):
                y_new = np.interp (x_new, x, y)
        elif (interp_type.lower () == "spline"):
                tck = interpolate.splrep (x, y, s = 0)
                y_new = interpolate.splev (x_new, tck)
        else:
                raise ValueError ("interp1: Invalid interpolation method specified: %s" % interp_type)
        
        return y_new



def rho_filter (proj, f_type = "ram-lak", scaling = 1, ret_filter = False):
        """
          rho_filter (proj, f_type = "ram-lak", scaling = 1, 
                      ret_filter = False)
        
        Performs rho filtering on the parallel ray projections provided.
        """
        filtered_proj = proj.copy()
        
        if (f_type.lower () == "none"):
                if (ret_filter):
                        return filtered_proj, 1
                else:
                        return filtered_proj
        
        if not (0 <= scaling <= 1):
                raise ValueError ('rho_filter: Scaling factor must be in [0,1]')
        
        ## Extend the projections to a larger power of 2
        new_len = 2 * 2 ** np.ceil (np.log2 (filtered_proj.shape [0]))
        filtered_proj.resize ((new_len, filtered_proj.shape [1]))
        
        ## Scale the frequency response. int_len needs to be even
        rho_len = round (new_len * scaling / 2) + 1
        
        ## Create the basic filter response
        rho = scaling * np.linspace (0, 1, rho_len)
        
        ## Create the window to apply to the filter response
        f = np.linspace (0, 0.5, rho_len)
        if (f_type.lower() == 'ram-lak'):
                window = 1
        elif (f_type.lower() == 'hamming'):
                window = 0.54 + 0.46 * np.cos (2 * np.pi * f)
        elif (f_type.lower() == 'hann'):
                window = 0.5 + 0.5 * np.cos (2 * np.pi * f)
        elif (f_type.lower() == 'cosine'):
                window = np.cos (np.pi * f)
        elif (f_type.lower() == 'shepp-logan'):
                window = np.sinc (f)
        else:
                raise ValueError ("rho_filter: Unknown window type: %s" % f_type)
        
        ## Apply the window
        filt = window * rho
        
        ## Pad the response to the correct length
        len_diff = (new_len / 2 + 1) - rho_len
        if (len_diff != 0):
                filt.resize (new_len / 2 + 1)
                
        proj_fft = np.fft.rfft (filtered_proj, axis = 0)
        
        ## Perform the filtering
        for i in range (proj_fft.shape [1]):
                proj_fft [:, i] *= filt

        #proj_fft = np.fft.rfft (filtered_proj, axis = 0)
        
        ## Finally bring the projections back to the spatial domain
        filtered_proj = np.fft.irfft (proj_fft, axis = 0)
        
        ## Chop the projections back to their original size
        filtered_proj.resize ((proj.shape [0], filtered_proj.shape [1]))
        
        if (ret_filter):
                return filtered_proj, filt
        else:
                return filtered_proj



def m_rho_filter (proj, f_type = "ram-lak", scaling = 1, ret_filter = False):
        """
        modified rho_filter
        """
        filtered_proj = proj.copy()
        
        if (f_type.lower () == "none"):
                if (ret_filter):
                        return filtered_proj, 1
                else:
                        return filtered_proj
        
        if not (0 <= scaling <= 1):
                raise ValueError ('rho_filter: Scaling factor must be in [0,1]')
        
        ## Extend the projections to a larger power of 2
        #new_len = 2 * 2 ** np.ceil (np.log2 (filtered_proj.shape [0]))
        #filtered_proj.resize ((new_len, filtered_proj.shape [1]))
        
        ## Scale the frequency response. int_len needs to be even
        rho_len = round (filtered_proj.shape [0] * scaling / 2) + 1
        
        ## Create the basic filter response
        rho = scaling * np.linspace (0, 1, rho_len)
        
        ## Create the window to apply to the filter response
        f = np.linspace (0, 0.5, rho_len)
        if (f_type.lower() == 'ram-lak'):
                window = 1
        elif (f_type.lower() == 'hamming'):
                window = 0.54 + 0.46 * np.cos (2 * np.pi * f)
        elif (f_type.lower() == 'hann'):
                window = 0.5 + 0.5 * np.cos (2 * np.pi * f)
        elif (f_type.lower() == 'cosine'):
                window = np.cos (np.pi * f)
        elif (f_type.lower() == 'shepp-logan'):
                window = np.sinc (f)
        else:
                raise ValueError ("rho_filter: Unknown window type: %s" % f_type)
        
        ## Apply the window
        filt = window * rho
        
        ## Pad the response to the correct length
        #len_diff = (new_len / 2 + 1) - rho_len
        #if (len_diff != 0):
#                filt.resize (new_len / 2 + 1)
                
        proj_fft = np.fft.rfft (filtered_proj, axis = 0)
        
        ## Perform the filtering
        for i in range (proj_fft.shape [1]):
                proj_fft [:, i] *= filt

        #proj_fft = np.fft.rfft (filtered_proj, axis = 0)
        
        ## Finally bring the projections back to the spatial domain
        filtered_proj = np.fft.irfft (proj_fft, axis = 0)
        
        ## Chop the projections back to their original size
        #filtered_proj.resize ((proj.shape [0], filtered_proj.shape [1]))
        
        if (ret_filter):
                return filtered_proj, filt
        else:
                return filtered_proj


