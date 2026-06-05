#"""
#   :synopsis: Driver run file for TPL example
#   :version: 2.0
#   :maintainer: Jeffrey Hyman
#.. moduleauthor:: Jeffrey Hyman <jhyman@lanl.gov>
#"""

from pydfnworks import *
import os

src_path = os.getcwd()
jobname = src_path + "/output"
dfnFlow_file = src_path + '/udfm_multi_material_thermal.in'

DFN = DFNWORKS(jobname,
               dfnFlow_file=dfnFlow_file,
               flow_solver="PFLOTRAN",
               ncpu=8)

DFN.params['domainSize']['value'] = [100.0, 100.0, 100.0]
DFN.params['h']['value'] = 0.1
DFN.params['visualizationMode']['value'] = True

DFN.add_user_fract(shape='rect',
                   radii=100,
                   translation=[-40, 0, 0],
                   normal_vector=[0, 0, 1],
                   aperture=1.0e-3)

DFN.add_user_fract(shape='rect',
                   radii=100,
                   aspect_ratio=.65,
                   translation=[0, 0, 0],
                   normal_vector=[1, 0, 0],
                   aperture=1.0e-3)

DFN.add_user_fract(shape='rect',
                   radii=60,
                   translation=[40, 0, 20],
                   normal_vector=[0, 0, 1],
                   aperture=2.0e-3)

DFN.add_user_fract(shape='rect',
                   radii=60,
                   translation=[40, 0, -20],
                   normal_vector=[0, 0, 1],
                   aperture=1.0e-3)

DFN.make_working_directory(delete=True)
DFN.check_input()
# define_paths()
DFN.create_network()
DFN.mesh_network()

DFN.map_to_continuum(l=30, orl=3)
DFN.upscale(mat_perm=1e-15, mat_por=0.01)

DFN.zone2ex(zone_file='all')

### Grab fracture inflow nodes 
import numpy as np 

DFN.material_ids = np.genfromtxt('tag_frac.dat').astype(int)

## Tag cells and boundaries 
matrix_id = np.where(DFN.material_ids == 1)[0]
frac_id = np.where(DFN.material_ids == 2)[0]

boundary_ids = np.genfromtxt('boundary_left_w.ex', skip_header = 1)[:,0].astype(int)
frac_boundary = list(set(frac_id).intersection(set(boundary_ids)))
 
with open('frac_left.txt', 'w') as fout:
    for i in frac_boundary:
        fout.write(f"{i+1}\n")

matrix_boundary = list(set(matrix_id).intersection(set(boundary_ids)))

with open('matrix_left.ex', 'w') as fout:
    fout.write(f'CONNECTIONS\t\t{len(matrix_boundary)}\n')
    with open('boundary_left_w.ex', 'r') as fin:
        fin.readline() ## header
        for line in fin.readlines():
            index = int(line.split()[0])
            if index in matrix_boundary:
                fout.write(line)



DFN.pflotran()
DFN.parse_pflotran_h5() 
