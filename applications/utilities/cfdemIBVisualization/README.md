# CFDEMcoupling Visualization Tool

## Overview

This directory contains a Python visualization script that demonstrates the differences between the cfdemIB geometric method and standard Immersed Boundary Method (IBM) interpolation approaches used in CFD-DEM coupling.

## Purpose

The visualization tool helps understand the fundamental differences between:

1. **cfdemIB Geometric Method** (current CFDEMcoupling implementation):
   - Direct geometric intersection calculation
   - Vertex-based void fraction computation  
   - Sharp transitions at particle boundaries
   - Binary inside/outside determination

2. **Standard IBM with Discrete Delta Functions**:
   - Smooth Dirac delta function interpolation
   - Gradual transitions around particle boundaries
   - Support radius extending beyond particle surface
   - Continuous interpolation with smooth kernels

## Generated Visualizations

The script produces two high-quality PNG files:

### 1. `cfdem_ib_vs_ibm_comparison.png`
Comprehensive comparison including:
- 2D contour plots showing void fraction fields
- 3D surface plots demonstrating boundary sharpness
- Cross-sectional profiles highlighting transition differences
- Difference plot showing method variations
- Interpolation kernel function comparison
- Grid cell intersection illustration

### 2. `cfdem_ib_kernel_comparison.png`
Detailed kernel function analysis featuring:
- Sharp vs smooth kernel functions
- Multiple IBM smoothing parameters
- Gradient analysis showing transition sharpness
- Influence zone visualization

## Requirements

- Python 3.x
- matplotlib
- numpy

## Usage

1. **Install dependencies** (if not already installed):
   ```bash
   pip install matplotlib numpy
   ```

2. **Run the visualization script**:
   ```bash
   cd applications/utilities/cfdemIBVisualization
   python3 cfdem_ib_visualization.py
   ```

3. **Output files** will be generated in the same directory:
   - `cfdem_ib_vs_ibm_comparison.png`
   - `cfdem_ib_kernel_comparison.png`

## Technical Implementation

### cfdemIB Geometric Method
Based on the `IBVoidFraction.C` implementation in CFDEMcoupling:
- Uses `segmentParticleIntersection` method for geometric calculations
- Solves quadratic equations for sphere-line intersections
- Provides sharp, binary transitions at particle boundaries
- No smoothing or interpolation beyond geometric ratios

### Standard IBM Implementation
Implements typical IBM approaches:
- Smooth delta function kernels (Gaussian-based)
- Configurable support radius (1.2R to 2.0R)
- Tanh-based smooth transitions
- Continuous void fraction fields

## Key Differences Highlighted

| Aspect | cfdemIB Geometric | Standard IBM |
|--------|------------------|--------------|
| **Boundary Detection** | Binary inside/outside | Smooth interpolation |
| **Transition Type** | Sharp, discontinuous | Gradual, continuous |
| **Computational Cost** | Lower (geometric only) | Higher (kernel evaluation) |
| **Smoothness** | No smoothing | Inherently smooth |
| **Influence Zone** | Particle boundary only | Extended support radius |
| **Numerical Stability** | Sharp gradients | Smooth gradients |

## Educational Value

This tool is valuable for:
- Understanding CFD-DEM coupling fundamentals
- Comparing different void fraction calculation methods
- Visualizing the impact of smoothing in IBM approaches
- Educational demonstrations of CFDEMcoupling methodology
- Research presentations and documentation

## License

This visualization tool is distributed under the GNU General Public License v3, consistent with the CFDEMcoupling-PUBLIC license.

## Related Files

- Source implementation: `src/lagrangian/cfdemParticle/subModels/voidFractionModel/IBVoidFraction/`
- CFDEMcoupling documentation: `doc/CFDEMcoupling_Manual.html`
- Example usage in tutorials: `tutorials/`