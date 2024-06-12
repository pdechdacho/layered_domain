#"""
#   :synopsis: Driver run file for TPL example
#   :version: 2.0
#   :maintainer: Jeffrey Hyman
#.. moduleauthor:: Jeffrey Hyman <jhyman@lanl.gov>
#"""

from pydfnworks import *
import os
import numpy as np

def translate_DFN(DFN, z0, offset = 0):
    for i in range(DFN.num_frac):
        DFN.centers[i] += [0,0,z0]

    for i in range(1,DFN.num_frac+1):
        key = f'fracture-{i}'
        for j in range(len(DFN.polygons[key])):
            DFN.polygons[key][j] += [0,0,z0]
        if offset > 0:
            new_key = f'fracture-{i + offset}'
            DFN.polygons[new_key] = DFN.polygons[key] 

    return DFN 


jobname = "combined_UDFM"
DFN = DFNWORKS(jobname,
               ncpu=12)
DFN.params['domainSize']['value'] = [20, 20, 20]
DFN.params['h']['value'] = 0.1
DFN.params['domainSizeIncrease']['value'] = [0.5, 0.5, 0.5]
DFN.params['ignoreBoundaryFaces']['value'] = False 
DFN.params['boundaryFaces']['value'] = [0, 0, 0, 0, 1, 1]
DFN.params['seed']['value'] = 3
DFN.params['disableFram']['value'] = True
DFN.params['tripleIntersections']['value'] = True
DFN.params['keepIsolatedFractures']['value']= True 
DFN.params['keepOnlyLargestCluster']['value'] = False

DFN.add_fracture_family(
    shape="ell",
    distribution="tpl",
    alpha=1.8,
    min_radius=1.0,
    max_radius=20.0,
    kappa=1.0,
    theta=0.0,
    phi=0.0,
    #aspect=2,
    p32=0.4,
    hy_variable='aperture',
    hy_function='correlated',
    number_of_points=8,
    hy_params={
        "alpha": 10**-5,
        "beta": 0.5
    })

DFN.h = 0.1
DFN.x_min = -10
DFN.y_min = -10
DFN.z_min = -10
DFN.x_max = 10
DFN.y_max = 10
DFN.z_max = 10

DFN.domain = {"x": 20, "y": 20, "z": 20 }

src_dir = os.getcwd()

DFN.make_working_directory(delete=True)
DFN.check_input()

TOP_DFN = DFNWORKS(pickle_file = f"{src_dir}/top.pkl")
BOTTOM_DFN = DFNWORKS(pickle_file = f"{src_dir}/bottom.pkl")


TOP_DFN = translate_DFN(TOP_DFN, 5)
BOTTOM_DFN = translate_DFN(BOTTOM_DFN, -5, TOP_DFN.num_frac)

## combine DFN
DFN.num_frac = TOP_DFN.num_frac + BOTTOM_DFN.num_frac 
DFN.centers = np.concatenate((TOP_DFN.centers, BOTTOM_DFN.centers))
DFN.polygons = TOP_DFN.polygons.copy() 
DFN.polygons = DFN.polygons| BOTTOM_DFN.polygons
DFN.normal_vectors = np.concatenate((TOP_DFN.normal_vectors, BOTTOM_DFN.normal_vectors))

DFN.map_to_continuum(l = 5, orl = 3, path = src_dir)