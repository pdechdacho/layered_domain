#"""
#   :synopsis: Driver run file for TPL example
#   :version: 2.0
#   :maintainer: Jeffrey Hyman
#.. moduleauthor:: Jeffrey Hyman <jhyman@lanl.gov>
#"""
import numpy as np 
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


# """Extract fracture and matrix nodes on the left boundary."""

import numpy as np
# Load material IDs for all cells/nodes.
# Expected convention:
#   1 = matrix
#   2 = fracture
DFN.material_ids = np.genfromtxt("tag_frac.dat").astype(int)

# Get zero-based indices for matrix and fracture entries.
matrix_ids = np.where(DFN.material_ids == 1)[0]
fracture_ids = np.where(DFN.material_ids == 2)[0]

# Load left-boundary IDs from the EX file.
# The first line is a header, and the first column contains boundary IDs.
boundary_ids = np.genfromtxt(
    "boundary_left_w.ex",
    skip_header=1,
    usecols=0,
).astype(int)

# Convert arrays to sets for fast membership checks.
matrix_id_set = set(matrix_ids)
fracture_id_set = set(fracture_ids)
boundary_id_set = set(boundary_ids)

# Identify fracture and matrix IDs that lie on the left boundary.
fracture_boundary_ids = sorted(fracture_id_set & boundary_id_set)
matrix_boundary_ids = sorted(matrix_id_set & boundary_id_set)

# Write fracture boundary IDs.
# Add 1 because the output file expects one-based indexing.
with open("frac_left.txt", "w") as fout:
    for node_id in fracture_boundary_ids:
        fout.write(f"{node_id + 1}\n")

# Write a filtered EX file containing only matrix boundary connections.
with open("matrix_left.ex", "w") as fout:
    fout.write(f"CONNECTIONS\t\t{len(matrix_boundary_ids)}\n")

    with open("boundary_left_w.ex", "r") as fin:
        next(fin)  # Skip header line.

        for line in fin:
            boundary_id = int(line.split()[0])

            if boundary_id in matrix_boundary_ids:
                fout.write(line)

DFN.pflotran()
DFN.parse_pflotran_h5() 
