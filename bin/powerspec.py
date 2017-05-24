from layerline import generate_layerline_bessel_pairs_from_rise_and_rotation
import numpy as np
from scipy import special
from scipy.ndimage.interpolation import zoom
from scipy.ndimage.filters import gaussian_filter

def convert_pitch_unit_pair_to_rise_rotation_pairs(pitch, unit_number):
    rise = pitch / unit_number
    rotation = 360.0 / unit_number
    rise_rotation_pair = (rise, rotation)
    return rise_rotation_pair


def make_combined_sim_real_powerspectrum(im, im_theo):
    im = im / im.max()
    im_theo = im_theo / im_theo.max()
    minwidth = min(im.shape[1], im_theo.shape[1])/2
    minheight = min(im.shape[0], im_theo.shape[0])
    return np.hstack((im_theo[0:minheight,0:minwidth], im[0:minheight, -minwidth:]))


def compute_Bfactor_mask(power_size, pixelsize, B):
    grid_x, grid_y = (np.mgrid[0:power_size, 0:power_size] - power_size/2.0) / float(power_size) / pixelsize
    center_dist = np.hypot(grid_x, grid_y)
    center_dist[center_dist==0.0] = center_dist[center_dist!=0].min()
    d = 1.0/center_dist
    return np.exp(-B/(4*d**2))

def create_single_layer_line(linex, linex_fine, bessel_order, layer_line_length):
    """
    >>> from spring.segment3d.segclassreconstruct import SegClassReconstruct
    >>> b_len = np.pi * 180.0 / 1.2
    >>> ll_len = 50
    >>> b_fine = np.linspace(0, b_len, 100 * ll_len)
    >>> b = np.linspace(0, b_len, ll_len)
    >>> s = SegClassReconstruct()
    >>> ll = s.create_single_layer_line(b, b_fine, 4, ll_len)
    >>> np.round(ll, 2)
    array([ 0.  ,  0.26,  0.18,  0.15,  0.13,  0.11,  0.09,  0.08,  0.06,
            0.04,  0.03,  0.01,  0.  ,  0.01,  0.02,  0.03,  0.04,  0.05,
            0.05,  0.06,  0.06,  0.06,  0.05,  0.05,  0.04,  0.03,  0.02,
            0.01,  0.  ,  0.01,  0.02,  0.02,  0.03,  0.04,  0.04,  0.04,
            0.04,  0.04,  0.04,  0.04,  0.03,  0.03,  0.02,  0.01,  0.01,
            0.  ,  0.01,  0.02,  0.02,  0.03])
    """
    bessel_function = np.abs(special.jv(bessel_order, linex_fine))
    layer_line = np.zeros((layer_line_length))
    for each_pixel, each_val in enumerate(layer_line):
        bessel_index_closest = np.argmin(np.abs(linex_fine - linex[each_pixel]))
        layer_line[each_pixel] += abs(bessel_function[bessel_index_closest])
    
    return layer_line


def prepare_ideal_power_spectrum_from_layer_lines(layerline_bessel_pairs, width_of_helix, power_size,
pixelsize):
    if type(power_size) != tuple:
        power_width = power_size
    else:
        power_size, power_width = power_size
    bessel_length = np.pi * width_of_helix / pixelsize
    layer_line_length = power_width / 2
    linex = np.linspace(0, bessel_length, layer_line_length)
    linex_fine = np.linspace(0, bessel_length, 100 * layer_line_length)
    
    ideal_layer_line_power = np.zeros((power_size / 2, layer_line_length))
    for each_layer_line_pair in layerline_bessel_pairs:
        layer_line_position_in_pixel = int(round(each_layer_line_pair[0] * pixelsize * power_size))
        if layer_line_position_in_pixel < power_size / 2:
            bessel_order = abs(each_layer_line_pair[1])
            layer_line = create_single_layer_line(linex, linex_fine, bessel_order, layer_line_length)
            ideal_layer_line_power[layer_line_position_in_pixel] += layer_line
                
    ideal_power = np.hstack((np.fliplr(np.flipud(ideal_layer_line_power)), np.flipud(ideal_layer_line_power)))
    upper_half = np.roll(ideal_power, 1, axis=0)
    lower_half = np.flipud(ideal_power)
    ideal_power = np.vstack((upper_half, lower_half))
    
    return gaussian_filter(ideal_power,0.7)



if __name__=='__main__':
	pixelsize=1.35
	width = 180.0
	sym = (1.408, 22.03)
	power_size = 100
	layerline_bessel_pairs = generate_layerline_bessel_pairs_from_rise_and_rotation(sym, 1, width, 5.0, 300, 10)
	a = prepare_ideal_power_spectrum_from_layer_lines(layerline_bessel_pairs, width, 
		power_size, pixelsize)
