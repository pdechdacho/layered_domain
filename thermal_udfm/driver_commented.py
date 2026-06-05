"""
DFNWorks driver for a UDFM thermal-flow example.

This script:
1. Builds a deterministic fracture network.
2. Meshes the network with DFNWorks.
3. Maps the fracture network to a continuum grid using the UDFM workflow.
4. Upscales fracture/matrix properties for PFLOTRAN.
5. Splits the left boundary into matrix and fracture inflow regions.
6. Runs PFLOTRAN and parses the resulting HDF5 output.
"""

import os

import numpy as np
from pydfnworks import *


# -----------------------------------------------------------------------------
# Paths and DFNWorks job setup
# -----------------------------------------------------------------------------

# Use the current working directory as the base directory for the example.
src_path = os.getcwd()

# DFNWorks writes generated files, mesh files, and PFLOTRAN input/output here.
jobname = src_path + "/output"

# PFLOTRAN input deck used by DFNWorks when DFN.pflotran() is called.
dfnFlow_file = src_path + "/udfm_multi_material_thermal_commented.in"

# Create the DFNWorks driver object.
# flow_solver="PFLOTRAN" tells DFNWorks which flow code to prepare/run.
# ncpu controls the number of processors used for parallel steps.
DFN = DFNWORKS(
    jobname,
    dfnFlow_file=dfnFlow_file,
    flow_solver="PFLOTRAN",
    ncpu=8,
)


# -----------------------------------------------------------------------------
# DFN generation parameters
# -----------------------------------------------------------------------------

# Physical domain dimensions in x, y, and z.
DFN.params["domainSize"]["value"] = [100.0, 100.0, 100.0]

# Target mesh size on fractures.
DFN.params["h"]["value"] = 0.1

# Request visualization files from DFNWorks.
DFN.params["visualizationMode"]["value"] = True


# -----------------------------------------------------------------------------
# Deterministic fracture network definition
# -----------------------------------------------------------------------------
# Each call adds one user-defined rectangular fracture. The translation gives the
# fracture center, the normal_vector controls orientation, and aperture controls
# hydraulic opening.

# Large horizontal fracture shifted toward the negative x side of the domain.
DFN.add_user_fract(
    shape="rect",
    radii=100,
    translation=[-40, 0, 0],
    normal_vector=[0, 0, 1],
    aperture=1.0e-3,
)

# Large vertical fracture through the domain center.
DFN.add_user_fract(
    shape="rect",
    radii=100,
    aspect_ratio=0.65,
    translation=[0, 0, 0],
    normal_vector=[1, 0, 0],
    aperture=1.0e-3,
)

# Upper-right horizontal fracture with a larger aperture.
DFN.add_user_fract(
    shape="rect",
    radii=60,
    translation=[40, 0, 20],
    normal_vector=[0, 0, 1],
    aperture=2.0e-3,
)

# Lower-right horizontal fracture.
DFN.add_user_fract(
    shape="rect",
    radii=60,
    translation=[40, 0, -20],
    normal_vector=[0, 0, 1],
    aperture=1.0e-3,
)


# -----------------------------------------------------------------------------
# DFN generation and meshing
# -----------------------------------------------------------------------------

# Create a clean working directory. delete=True removes any previous output.
DFN.make_working_directory(delete=True)

# Validate DFNWorks inputs before generating the network.
DFN.check_input()

# Generate the fracture geometry and intersection network.
DFN.create_network()

# Mesh the fracture network.
DFN.mesh_network()


# -----------------------------------------------------------------------------
# UDFM mapping and property upscaling
# -----------------------------------------------------------------------------

# Map the DFN mesh to a structured continuum grid.
# l is the continuum cell size, and orl is the overlap refinement level.
DFN.map_to_continuum(l=30, orl=3)

# Compute equivalent continuum properties for PFLOTRAN.
# mat_perm and mat_por are the background matrix permeability and porosity.
DFN.upscale(mat_perm=1e-15, mat_por=0.01)

# Convert DFNWorks zone files to PFLOTRAN EX region files.
DFN.zone2ex(zone_file="all")


# -----------------------------------------------------------------------------
# Split the left boundary into matrix and fracture inflow regions
# -----------------------------------------------------------------------------
# PFLOTRAN will apply different thermal inflow conditions to matrix and fracture
# cells on the left boundary. This block builds two region files:
#   frac_left.txt  : fracture cells on the left boundary
#   matrix_left.ex : matrix connections on the left boundary

# Material IDs are written by the UDFM workflow.
# Expected convention:
#   1 = matrix continuum cells
#   2 = fracture continuum cells
DFN.material_ids = np.genfromtxt("tag_frac.dat").astype(int)

# Find zero-based indices for matrix and fracture cells.
matrix_ids = np.where(DFN.material_ids == 1)[0]
fracture_ids = np.where(DFN.material_ids == 2)[0]

# Read cell/connection IDs from the full left-boundary EX file.
# The first row is the EX header, and the first column stores the IDs.
boundary_ids = np.genfromtxt(
    "boundary_left_w.ex",
    skip_header=1,
    usecols=0,
).astype(int)

# Use sets for fast and clear boundary/material intersections.
matrix_id_set = set(matrix_ids)
fracture_id_set = set(fracture_ids)
boundary_id_set = set(boundary_ids)

# Identify which left-boundary IDs belong to each material class.
fracture_boundary_ids = sorted(fracture_id_set & boundary_id_set)
matrix_boundary_ids = sorted(matrix_id_set & boundary_id_set)

# Write the fracture inflow region.
# The +1 converts from Python zero-based indexing to PFLOTRAN one-based IDs.
with open("frac_left.txt", "w") as fout:
    for node_id in fracture_boundary_ids:
        fout.write(f"{node_id + 1}\n")

# Write the matrix inflow region by filtering the original left-boundary EX file.
# This preserves the EX connection data format expected by PFLOTRAN.
with open("matrix_left.ex", "w") as fout:
    fout.write(f"CONNECTIONS\t\t{len(matrix_boundary_ids)}\n")

    with open("boundary_left_w.ex", "r") as fin:
        next(fin)  # Skip original header.

        for line in fin:
            boundary_id = int(line.split()[0])

            if boundary_id in matrix_boundary_ids:
                fout.write(line)


# -----------------------------------------------------------------------------
# Run PFLOTRAN and parse output
# -----------------------------------------------------------------------------

# Launch PFLOTRAN using the input card defined above.
DFN.pflotran()

# Convert PFLOTRAN HDF5 output into DFNWorks post-processing format.
DFN.parse_pflotran_h5()
