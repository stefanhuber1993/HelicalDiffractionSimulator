import numpy as np
from scipy import special


def get_list_of_bessel_order_maxima(order_count):
    """
    >>> from spring.segment3d.segclassreconstruct import SegClassReconstruct
    >>> SegClassReconstruct().get_list_of_bessel_order_maxima(10)
    array([  0. ,   1.8,   3.1,   4.2,   5.3,   6.4,   7.5,   8.6,   9.6,  10.7])
    """
    arr = np.arange(0, 25, 0.1)
    primarymax = np.array([arr[np.argmax(special.jv(each_order, arr))] for each_order in range(order_count)])
    
    return primarymax

def adjust_bessel_order_if_out_of_plane_not_zero(out_of_plane_tilt, layer_line_position,
    assigned_bessel_order, helix_radius, bessel_maxima):
    """
    >>> from spring.segment3d.segclassreconstruct import SegClassReconstruct
    >>> s = SegClassReconstruct()
    >>> bes = s.get_list_of_bessel_order_maxima(20)
    >>> s.adjust_bessel_order_if_out_of_plane_not_zero(0, 0.1, 3, 180.0, bes) 
    3
    >>> s.adjust_bessel_order_if_out_of_plane_not_zero(3, 0.1, 3, 180.0, bes)
    0
    """
    if out_of_plane_tilt != 0:
        meridional_dist = np.tan(np.deg2rad(out_of_plane_tilt)) * layer_line_position
        pos_prim_point = 2 * np.pi * meridional_dist * helix_radius
        shifted_maxs = bessel_maxima - pos_prim_point
        adjusted_bessel_order = np.argmin(np.abs(shifted_maxs[abs(assigned_bessel_order)] - bessel_maxima))
        if assigned_bessel_order < 0:
            adjusted_bessel_order = -adjusted_bessel_order
    else:
        adjusted_bessel_order = assigned_bessel_order

    return adjusted_bessel_order


def adjust_reciprocal_layer_line_pitches_by_out_of_plane_angle(pitches, out_of_plane_tilt=0):
    """
    >>> from spring.segment3d.segclassreconstruct import SegClassReconstruct
    >>> s = SegClassReconstruct()
    >>> s.adjust_reciprocal_layer_line_pitches_by_out_of_plane_angle(0.1, 0)
    0.10000000000000001
    >>> s.adjust_reciprocal_layer_line_pitches_by_out_of_plane_angle(0.1, 12)
    0.10223405948650292
    """
    tilt_corrected_pitches = pitches / np.cos(np.deg2rad(out_of_plane_tilt)) 

    return tilt_corrected_pitches

def generate_layerline_bessel_pairs_from_rise_and_rotation(rise_rotation_pair, rot_sym, width_of_helix,
pixelsize, low_resolution_cutoff, high_resolution_cutoff, out_of_plane_tilt=0.0):
    """
    >>> from spring.segment3d.segclassreconstruct import SegClassReconstruct
    >>> s = SegClassReconstruct()
    >>> sym = (1.408, 22.03)
    >>> s.generate_layerline_bessel_pairs_from_rise_and_rotation(sym, 1, 180.0, 5.0, 300, 10) #doctest: +NORMALIZE_WHITESPACE
    [(0.086926286509040343, 2), (0.072087658592848908, 18), 
    (0.058298839853086926, -15), (0.043461254291798861, 1), 
    (0.028626227349497609, 17), (0.01483591478250549, -16)]
    >>> s.generate_layerline_bessel_pairs_from_rise_and_rotation(sym, 1, 180.0, 5.0, 300, 10, 3) #doctest: +NORMALIZE_WHITESPACE
    [(0.087045579450445165, 0), (0.072186587802618302, 16), 
    (0.058378846032642748, -13), (0.043520898170190836, 0), 
    (0.028665512438036268, 16), (0.014856274790782758, -16)]
    >>> s.generate_layerline_bessel_pairs_from_rise_and_rotation(sym, 2, 180.0, 5.0, 300, 10, 3) #doctest: +NORMALIZE_WHITESPACE
    [(0.087045579450445165, 0), (0.072186587802618302, 16), 
    (0.014856274790782758, -16)]
    """
    helical_rise = rise_rotation_pair[0]
    helical_rotation = rise_rotation_pair[1]
    pitch_of_helix = helical_rise * 360 / helical_rotation
    
    helix_radius = width_of_helix / 2.0
    maximum_n = int((np.pi * helix_radius)/pixelsize) + 2 
    pitch_grid = np.zeros((maximum_n, maximum_n))
    bessel_grid = np.zeros((maximum_n, maximum_n))
    
    n_combinations = m_combinations = list(range(-maximum_n / 2, maximum_n / 2, 1))
    for n_index, each_n in enumerate(n_combinations):
        n_is_multiple_of_rotational_symmetry = each_n % rot_sym
        if n_is_multiple_of_rotational_symmetry == 0:
            for m_index, each_m in enumerate(m_combinations):
                layer_line_position = each_n / pitch_of_helix + each_m / helical_rise
                if layer_line_position == 0:
                    pass
                else:
                    pitch_grid[n_index][m_index]=1 / layer_line_position
                    bessel_grid[n_index][m_index]=each_n
        
#        img = plt.imshow(pitch_grid, cmap=cm.jet, interpolation='nearest')
#        plt.savefig('test.pdf', dpi=600)
            
    pitch_sequence = pitch_grid.ravel()
    
    bessel_maxima = get_list_of_bessel_order_maxima(1000)
    unique_pitches = np.unique(np.round(np.abs(pitch_sequence), 3))
    pitches = []
    orders = []
    for each_unique_pitch in unique_pitches:
        if high_resolution_cutoff < each_unique_pitch < low_resolution_cutoff:
            n_m_indices_of_pitch = np.argwhere(np.round(pitch_grid, 3) == each_unique_pitch)
            
            bessel_orders = np.zeros(len(n_m_indices_of_pitch))
            for each_index, each_n_m_index in enumerate(n_m_indices_of_pitch):
                each_n_idx, each_m_idx = each_n_m_index
                bessel_order = bessel_grid[each_n_idx][each_m_idx]
                bessel_orders[each_index]=bessel_order
            
            if len(n_m_indices_of_pitch) > 0:
                min_index = np.argmin(np.abs(bessel_orders))
                assigned_bessel_order = int(bessel_orders[min_index])
            
                layer_line_position = 1 / each_unique_pitch
                pitches.append(layer_line_position)
                
                adjusted_bessel_order = adjust_bessel_order_if_out_of_plane_not_zero(out_of_plane_tilt,
                layer_line_position, assigned_bessel_order, helix_radius, bessel_maxima)
                
                orders.append(adjusted_bessel_order)

    pitches = np.array(pitches)
    
    tilt_corrected_pitches = adjust_reciprocal_layer_line_pitches_by_out_of_plane_angle(pitches,
    out_of_plane_tilt)
    
    unique_pitch_bessel_pairs = list(zip(tilt_corrected_pitches, orders))
        
    return unique_pitch_bessel_pairs


if __name__=='__main__':
    sym = (1.408, 22.03)
    print("Generating Layer-Line Bessel Pairs for Rise %.2fA and Rotation %.2f deg"%(sym))

    generate_layerline_bessel_pairs_from_rise_and_rotation(sym, 1, 180.0, 5.0, 300, 10)