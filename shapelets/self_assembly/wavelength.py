########################################################################################################################
# Copyright 2023 the authors (see AUTHORS file for full list).                                                         #
#                                                                                                                      #
# This file is part of shapelets.                                                                                      #
#                                                                                                                      #
# Shapelets is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General       #
# Public License as published by the Free Software Foundation, either version 2.1 of the License, or (at your option)  #
# any later version.                                                                                                   #
#                                                                                                                      #
# Shapelets is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied      #
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more  #
# details.                                                                                                             #
#                                                                                                                      #
# You should have received a copy of the GNU Lesser General Public License along with shapelets. If not, see           #
# <https://www.gnu.org/licenses/>.                                                                                     #
########################################################################################################################

import numbers 

import numpy as np

from ..functions import orthonormalpolar2D_n0, orthonormalpolar2D_n1

__all__ = [
    'make_grid',
    'lambda_to_beta_n0',
    'get_opt_kernel_n0',
    'lambda_to_beta_n1',
    'get_opt_kernel_n1',
    'get_wavelength',
]

def make_grid(N: int):
    r""" 
    Make discretized grid based on width (N).
    
    Parameters
    ----------
    * N: int
        * The width of the kernel (odd numbers only)

    Returns
    -------
    * grid_x: np.ndarray
        * The grid's x coordinate space
    * grid_y: np.ndarray
        * The grid's y coordinate space
    
    Notes
    -----
    As per convention, N should only be an odd number. Additionally, note that grid_x = grid_y.

    """
    if N % 2 == 0:
        print('Detected even grid size, adding 1 to enforce odd rule See self_assembly.wavelength.make_grid() docs.')
        N += 1
    if N < 3:
        raise ValueError('N must be at least 3 or greater.')
    
    bounds = [-(N-1)/2.0, (N-1)/2.0]
    grid = np.linspace(bounds[0], bounds[1], N)
    grid_x, grid_y = np.meshgrid(grid, grid)

    return grid_x, grid_y

def lambda_to_beta_n0(m: int, l: float) -> float:
    r""" 
    Converts lambda (l), the characteristic wavelength of the image[1]_ to the appropriate beta value for orthonormal polar shapelets[2]_ with $n=0$ (see shapelets.functions.orthonormalpolar2D_n0).
    
    Parameters
    ----------
    * m: int
        * Shapelet degree of rotational symmetry
    * l: float
        * The characteristic wavelength of the image[1]_
    
    Returns
    -------
    * beta: float
        * The characteristic shapelet length scale parameter based on ref.[2]_

    References
    ----------
    .. [1] http://dx.doi.org/10.1103/PhysRevE.91.033307
    .. [2] https://doi.org/10.1088/1361-6528/aaf353

    """
    if m == 4:   
        f = np.sqrt(2) / 2
    elif m == 3: 
        f = 1 / np.sqrt(3)
    elif m == 2: 
        f = 1 / 2
    elif m == 1: 
        f = 1 / 4
    else:        
        f = 1

    beta = (l / np.sqrt(m)) * f
    return beta

def get_opt_kernel_n0(m: int, beta: float) -> np.ndarray:
    r""" 
    Determines the optimal filter (kernel) width for an $n=0$ orthonormal polar shapelet function[1]_ based on $\beta$, the shapelet length-scale parameter.
    
    Parameters
    ----------
    * m: int
        * Shapelet degree of rotational symmetry
    * beta: float
        * The characteristic shapelet length scale parameter.
    
    Returns
    -------
    * shapelet: np.ndarray
        * Shapelet function casted onto a discrete domain with the appropriate filter width.

    References
    ----------
    .. [1] https://doi.org/10.1088/1361-6528/aaf353

    """
    # start with small kernel size and scale up until satisfied
    N = 21 # minimum

    grid_x, grid_y = make_grid(N = N)
    shapelet = orthonormalpolar2D_n0(m=m, x1=grid_x, x2=grid_y, beta=beta)

    accept = False

    while not accept:
        edgeweight = np.abs(np.real(shapelet[int(shapelet.shape[0]/2), -1])) \
            / np.real(shapelet).max()
        if edgeweight > 0.0001:
            N += 4
            grid_x, grid_y = make_grid(N = N)
            shapelet = orthonormalpolar2D_n0(m=m, x1=grid_x, x2=grid_y, beta=beta)
        else:
            accept = True
    
    return shapelet

def lambda_to_beta_n1(m: int, l: float, verbose=False) -> float:
    r""" 
    Converts lambda (l), the characteristic wavelength of the image[1]_ to the appropriate beta value for orthonormal polar shapelets[2]_ with $n=1$ (see shapelets.functions.orthonormalpolar2D_n1).
    
    Parameters
    ----------
    * m: int
        * Shapelet degree of rotational symmetry
    * l: float
        * The characteristic wavelength of the image[1]_
    
    Returns
    -------
    * beta: float
        * The characteristic shapelet length scale parameter based on ref.[2]_

    References
    ----------
    .. [1] http://dx.doi.org/10.1103/PhysRevE.91.033307
    .. [2] https://hdl.handle.net/10012/20779

    """
    lambda_opt = np.round(l*1.5, 0)
    beta = 1

    accept = False

    while not accept:

        # get appropriate sized kernel
        shapelet = get_opt_kernel_n1(m = m, beta = beta)

        # extract the midline to work with 1D data for simplicity
        halfpoint = int((shapelet.shape[0] - 1) / 2)
        data = np.real(shapelet[halfpoint, :])

        # now find the two peaks associated with two max / min of inner/outer shapelet lobes
        numpts = data.size
        peak_ind = np.array([])
        for p in range(halfpoint+1, numpts-1): # check all points except for the ends
            if (data[p-1] < data[p] > data[p+1]) or (data[p-1] > data[p] < data[p+1]):
                peak_ind = np.append(peak_ind, p)

        if peak_ind.size != 2:
            print("Error in expected number of peaks... kernel error. Skipping iteration...")
            breakpoint()
            beta += 2*0.1

        else:
            # want {peak_HP - halfpoint} to be close to 1.5*lambda
            peak_MP = np.round((peak_ind[1] - peak_ind[0]) / 2, 0) + peak_ind[0]
            distance = peak_MP - halfpoint
            reldistance = lambda_opt - distance
            if verbose:
                print(f"Current distance {distance}, target is {lambda_opt}")

            ## evaluate acceptability of solution ##

            # found solution
            if np.abs(reldistance) <= 1:
                beta_opt = beta
                if verbose: print(f"optimum beta found to be {beta_opt}")
                accept = True # stop

            # undershot solution
            if reldistance > 0:
                # adaptive stepping to speed up computations
                if reldistance < 2:
                    beta += 0.1
                else: 
                    beta += 3*reldistance * 0.1

            # overshot solution
            elif reldistance < 0:
                if verbose:
                    print("We have overshot target, iterating backwards.")
                beta -= reldistance*0.1
    
    return beta_opt

def get_opt_kernel_n1(m: int, beta: float) -> np.ndarray:
    r""" 
    Determines the optimal filter (kernel) width for an $n=1$ orthonormal polar shapelet function[1]_ based on $\beta$, the shapelet length-scale parameter.

    Parameters
    ----------
    * m: int
        * Shapelet degree of rotational symmetry
    * beta: float
        * The characteristic shapelet length scale parameter.
    
    Returns
    -------
    * shapelet: np.ndarray
        * Shapelet function casted onto a discrete domain with the appropriate filter width.

    References
    ----------
    .. [1] https://hdl.handle.net/10012/20779

    """
    # start with large kernel size and truncate down until satisfied
    N = 501

    grid_x, grid_y = make_grid(N = N)
    shapelet = orthonormalpolar2D_n1(m=m, x1=grid_x, x2=grid_y, beta=beta)

    accept = False

    while not accept:
        edgeweight = np.abs(np.real(shapelet[int(shapelet.shape[0]/2), -1])) / np.real(shapelet).max()

        if edgeweight < 0.001:
            N -= 4
            grid_x, grid_y = make_grid(N = N)
            shapelet = orthonormalpolar2D_n1(m=m, x1=grid_x, x2=grid_y, beta=beta)
        else:
            accept = True

    return shapelet

def get_wavelength(image: np.ndarray, rng: list = [0, 70], verbose: bool = True) -> float:
    r""" 
    Find characteristic wavelength of an image. Computed using method described in ref.[1]_.
    
    Parameters
    ----------
    * image: np.ndarray
        * The image to be processed
    * rng: list
        * Range of wavelengths to consider for maximum wavelength. I.e., will return max wavelength in range of [0, 70] (default)

    Returns
    -------
    * char_wavelength: float
        * The characteristic wavelength of the image

    References
    ----------
    .. [1] http://dx.doi.org/10.1103/PhysRevE.91.033307
    
    """
    if type(image) != np.ndarray:
        raise TypeError('image input must be numpy array.')

    # Step 1: Find spectral density
    DFT = np.fft.fft2(image)
    DFT[0, 0] = 0.1
    # Shift the Fourier transform to center it
    DFT_shifted = np.fft.fftshift(DFT)
    # Calculate the magnitude
    spec_d = np.absolute(DFT_shifted)
    
    # Step 2: Find associated frequencies for spectral density
    x, y = np.fft.fftfreq(image.shape[1]), np.fft.fftfreq(image.shape[0])
    # Meshgrid them to map over the image domain
    X, Y = np.meshgrid(x, y)
    # Convert to 2d frequency definition (2.16 in [2]), shift and return
    omega = np.sqrt(X**2 + Y**2)
    freqs = np.fft.fftshift(omega)
    
    # Step 3: Find the radially averaged spectral density, and associated frequencies
    rai_spec = radialavg(spec_d)
    # Use inverse of frequency for wavelength
    rai_wave = radialavg(freqs)
    rai_wave = rai_wave ** -1
    
    # Step 4: Find and return the maximum
    if rng is not None:
        rai_spec = np.where((rai_wave >= rng[0]) * (rai_wave <= rng[1]), rai_spec, 0)
    i_max = rai_spec.argmax()
    
    if verbose:
        print('Wavelength of image is {:.2f} pixels'.format(rai_wave[i_max]))
    
    assert isinstance(rai_wave[i_max], numbers.Real)
    
    return rai_wave[i_max]

def radialavg(image: np.ndarray) -> np.ndarray:
    r""" 
    Calculates the radially averaged intensity of an image. Based on work from ref.[1]_.
    
    Parameters
    ----------
    * image: np.ndarray
        * The image to be radially averaged
    
    Returns
    -------
    * rai: np.ndarray
        * A 1d array with one intensity per integer radius, excluding 0. eg. For image with radii [0, 1, 2, 3], len(rai) = 3

    References
    ----------
    .. [1] http://dx.doi.org/10.1103/PhysRevE.91.033307
    
    """
    # Determine two arrays, x and y, which contain the indices of the image.
    y, x = np.indices(image.shape[0:2])
    # Determine the center of the image.
    center = np.array([(x.max()-x.min())/2.0, (y.max()-y.min())/2.0])
    # Use the center to offset x and y such that r = 0 is in the center (0, 0).
    x = x - center[0]
    y = y - center[1]
    # Determine the shortest dimension, as the radius is only defined for that range.
    length = min(np.max(x), np.max(y))
    # Scale x and y based on the radial range. This method creates an elliptical average for non-square images.
    x = x * length / np.max(x) 
    y = y * length / np.max(y)
    # Convert from x and y to radius using the hypotenuse definition.
    r = np.hypot(x, y)
    # Flatten the radius array and sort the radii, returning the indices. Uses quicksort.
    ind = np.argsort(r.flat)
    # Cast r values and image values to 1d arrays, sorted by radius.
    r_sorted = r.flat[ind]
    image_sorted = image.flat[ind]
    # Round the radii to the nearest even number and cast to int.
    r_int = np.around(r_sorted).astype(int)
    # Calculate the spacing between each radii
    deltar = r_int[1:] - r_int[:-1] # Suderman: "Assumes all radii represented"
    # Return the indices for values of delta that are non-zero. This will be the places where (before) r changes.
    rind = np.where(deltar)[0]
    # Append rind such that the last radii is represented
    rind = np.append(rind, len(r_int) - 1)
    # Determine number of items in each bin by taking the difference between indices where the bins change.
    nr = rind[1:] - rind[:-1]
    # Compute an array for the cumulative sum of a_sorted.
    csim = np.cumsum(image_sorted, dtype=float)
    # Take the difference between cumulative sums to determine the sum of image intensities for each bin.
    tbin = csim[rind[1:]] - csim[rind[:-1]]
    # Divide the sum of the bin by the number in each bin, giving a radial average intensity for each radius.
    rai = tbin / nr
    
    return rai