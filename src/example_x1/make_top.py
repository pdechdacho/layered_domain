#"""
#   :synopsis: Driver run file for TPL example
#   :version: 2.0
#   :maintainer: Jeffrey Hyman
#.. moduleauthor:: Jeffrey Hyman <jhyman@lanl.gov>
#"""

from pydfnworks import *
import os
import numpy as np


jobname = os.getcwd() + "/top"
dfnFlow_file = os.getcwd() + '/dfn_explicit.in'
dfnTrans_file = os.getcwd() + '/PTDFN_control.dat'

DFN = DFNWORKS(jobname,
               dfnFlow_file=dfnFlow_file,
               dfnTrans_file=dfnTrans_file,
               ncpu=12)

DFN.params['domainSize']['value'] = [20, 20, 10]
DFN.params['h']['value'] = 0.1
DFN.params['domainSizeIncrease']['value'] = [0.5, 0.5, 0.5]
DFN.params['ignoreBoundaryFaces']['value'] = False 
DFN.params['boundaryFaces']['value'] = [0, 0, 0, 0, 1, 1]
DFN.params['seed']['value'] = 2 # change for top and bottom. 
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


DFN.make_working_directory(delete=True)
DFN.check_input()
DFN.create_network()
DFN.dump_hydraulic_values()

# DFN.output_report()
DFN.mesh_network()
DFN.to_pickle("top")
# DFN.dfn_flow()
# DFN.dfn_trans()
