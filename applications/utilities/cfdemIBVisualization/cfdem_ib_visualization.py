#!/usr/bin/env python3
"""
CFDEMcoupling Visualization Script
==================================

This script generates 3D visualizations to demonstrate the differences between:
1. cfdemIB geometric method (current implementation)
2. Standard IBM with smooth interpolation methods

The visualization includes:
- Direct geometric intersection calculation vs smooth delta functions
- Sharp transitions vs gradual transitions around particle boundaries
- Binary inside/outside determination vs continuous interpolation
- 3D surface plots, cross-sectional views, and side-by-side comparisons

Author: Generated for CFDEMcoupling-PUBLIC
License: GPL v3 (consistent with CFDEMcoupling license)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import os


class CFDEMIBGeometric:
    """
    Implementation of cfdemIB geometric method for void fraction calculation.
    Based on the IBVoidFraction.C implementation in CFDEMcoupling.
    """
    
    def __init__(self, particle_center, particle_radius):
        self.center = np.array(particle_center)
        self.radius = particle_radius
    
    def segment_particle_intersection(self, point_inside, point_outside):
        """
        Compute intersection parameter lambda for line segment with particle sphere.
        Based on segmentParticleIntersection method in IBVoidFraction.C
        
        Solves quadratic equation: |point_inside + lambda*(point_outside - point_inside) - center|^2 = radius^2
        """
        direction = point_outside - point_inside
        to_center = point_inside - self.center
        
        a = np.dot(direction, direction)
        b = 2.0 * np.dot(direction, to_center)
        c = np.dot(to_center, to_center) - self.radius**2
        
        discriminant = b**2 - 4.0*a*c
        
        if discriminant < 0:
            return 0.0
        
        sqrt_d = np.sqrt(discriminant)
        lambda1 = (-b + sqrt_d) / (2.0*a)
        lambda2 = (-b - sqrt_d) / (2.0*a)
        
        # Find valid intersection in [0,1] range
        eps = 1e-12
        for lam in [lambda1, lambda2]:
            if -eps <= lam <= 1.0 + eps:
                return np.clip(lam, 0.0, 1.0)
        
        return 0.0
    
    def calculate_void_fraction(self, cell_center, cell_vertices):
        """
        Calculate void fraction for a cell using cfdemIB geometric method.
        Sharp binary determination with geometric intersection ratios.
        """
        # Check if cell center is inside particle
        center_distance = np.linalg.norm(cell_center - self.center)
        
        if center_distance > self.radius:
            # Cell center outside particle - check vertex intersections
            intersections = 0
            total_vertices = len(cell_vertices)
            
            for vertex in cell_vertices:
                vertex_distance = np.linalg.norm(vertex - self.center)
                
                if vertex_distance < self.radius:
                    # Vertex inside particle - compute intersection ratio
                    lambda_val = self.segment_particle_intersection(cell_center, vertex)
                    intersections += lambda_val
                elif vertex_distance > self.radius:
                    # Both points outside - check if line crosses particle
                    lambda_val = self.segment_particle_intersection(vertex, cell_center)
                    intersections += lambda_val
            
            # Sharp transition - geometric ratio
            void_fraction = 1.0 - (intersections / total_vertices)
            return np.clip(void_fraction, 0.0, 1.0)
        else:
            # Cell center inside particle - very low void fraction
            return 0.1  # alphaMin from IBVoidFraction


class StandardIBM:
    """
    Implementation of standard IBM with smooth interpolation using discrete delta functions.
    """
    
    def __init__(self, particle_center, particle_radius, support_radius_factor=1.5):
        self.center = np.array(particle_center)
        self.radius = particle_radius
        self.support_radius = particle_radius * support_radius_factor
    
    def discrete_delta_function(self, distance, smoothing_length):
        """
        Smooth discrete delta function for IBM interpolation.
        Using a Gaussian-based kernel function.
        """
        if distance > smoothing_length:
            return 0.0
        
        # Normalized distance
        r = distance / smoothing_length
        
        # Smooth kernel function (modified Gaussian)
        if r <= 1.0:
            return np.exp(-4.0 * r**2) * (1.0 - r**2)**2
        else:
            return 0.0
    
    def calculate_void_fraction(self, cell_center):
        """
        Calculate void fraction using smooth IBM interpolation.
        Gradual transitions with continuous kernel functions.
        """
        distance_to_surface = np.linalg.norm(cell_center - self.center) - self.radius
        
        if distance_to_surface <= -self.support_radius:
            # Deep inside particle
            return 0.0
        elif distance_to_surface >= self.support_radius:
            # Far from particle
            return 1.0
        else:
            # In the transition zone - smooth interpolation
            normalized_distance = (distance_to_surface + self.support_radius) / (2.0 * self.support_radius)
            
            # Smooth transition using tanh function
            return 0.5 * (1.0 + np.tanh(4.0 * (normalized_distance - 0.5)))


def create_2d_grid(nx=50, ny=50, domain_size=4.0):
    """Create 2D computational grid."""
    x = np.linspace(-domain_size/2, domain_size/2, nx)
    y = np.linspace(-domain_size/2, domain_size/2, ny)
    X, Y = np.meshgrid(x, y)
    return X, Y


def create_cell_vertices_2d(x, y, dx, dy):
    """Create vertices for a 2D cell."""
    return np.array([
        [x - dx/2, y - dy/2],
        [x + dx/2, y - dy/2],
        [x + dx/2, y + dy/2],
        [x - dx/2, y + dy/2]
    ])


def visualize_cfdem_ib_vs_ibm():
    """Generate comprehensive visualizations comparing cfdemIB and standard IBM methods."""
    
    # Set up particle and domain
    particle_center = [0.0, 0.0]
    particle_radius = 1.0
    domain_size = 4.0
    
    # Create grid
    nx, ny = 60, 60
    X, Y = create_2d_grid(nx, ny, domain_size)
    dx = domain_size / nx
    dy = domain_size / ny
    
    # Initialize methods
    cfdem_ib = CFDEMIBGeometric(particle_center, particle_radius)
    standard_ibm = StandardIBM(particle_center, particle_radius)
    
    # Calculate void fractions
    void_cfdem = np.zeros((ny, nx))
    void_ibm = np.zeros((ny, nx))
    
    for i in range(ny):
        for j in range(nx):
            cell_center = np.array([X[i, j], Y[i, j]])
            
            # cfdemIB method - geometric intersection
            cell_vertices = create_cell_vertices_2d(X[i, j], Y[i, j], dx, dy)
            void_cfdem[i, j] = cfdem_ib.calculate_void_fraction(cell_center, cell_vertices)
            
            # Standard IBM method - smooth interpolation
            void_ibm[i, j] = standard_ibm.calculate_void_fraction(cell_center)
    
    # Create visualizations
    fig = plt.figure(figsize=(20, 12))
    
    # 1. cfdemIB Geometric Method - 2D Contour
    ax1 = fig.add_subplot(2, 4, 1)
    im1 = ax1.contourf(X, Y, void_cfdem, levels=20, cmap='viridis')
    ax1.add_patch(plt.Circle(particle_center, particle_radius, fill=False, edgecolor='red', linewidth=2))
    ax1.set_title('cfdemIB Geometric Method\n(Sharp Transitions)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    plt.colorbar(im1, ax=ax1, label='Void Fraction')
    
    # 2. Standard IBM - 2D Contour
    ax2 = fig.add_subplot(2, 4, 2)
    im2 = ax2.contourf(X, Y, void_ibm, levels=20, cmap='viridis')
    ax2.add_patch(plt.Circle(particle_center, particle_radius, fill=False, edgecolor='red', linewidth=2))
    ax2.add_patch(plt.Circle(particle_center, standard_ibm.support_radius, fill=False, edgecolor='orange', 
                            linewidth=1, linestyle='--', alpha=0.7))
    ax2.set_title('Standard IBM Method\n(Smooth Transitions)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('x')
    ax2.set_ylabel('y')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    plt.colorbar(im2, ax=ax2, label='Void Fraction')
    
    # 3. cfdemIB - 3D Surface Plot
    ax3 = fig.add_subplot(2, 4, 3, projection='3d')
    surf1 = ax3.plot_surface(X, Y, void_cfdem, cmap='viridis', alpha=0.8)
    ax3.set_title('cfdemIB 3D Surface\n(Sharp Boundaries)', fontsize=10, fontweight='bold')
    ax3.set_xlabel('x')
    ax3.set_ylabel('y')
    ax3.set_zlabel('Void Fraction')
    
    # 4. Standard IBM - 3D Surface Plot
    ax4 = fig.add_subplot(2, 4, 4, projection='3d')
    surf2 = ax4.plot_surface(X, Y, void_ibm, cmap='viridis', alpha=0.8)
    ax4.set_title('Standard IBM 3D Surface\n(Smooth Boundaries)', fontsize=10, fontweight='bold')
    ax4.set_xlabel('x')
    ax4.set_ylabel('y')
    ax4.set_zlabel('Void Fraction')
    
    # 5. Cross-sectional comparison (y=0)
    ax5 = fig.add_subplot(2, 4, 5)
    center_idx = ny // 2
    x_line = X[center_idx, :]
    ax5.plot(x_line, void_cfdem[center_idx, :], 'b-', linewidth=2, label='cfdemIB Geometric', marker='o')
    ax5.plot(x_line, void_ibm[center_idx, :], 'r-', linewidth=2, label='Standard IBM', marker='s')
    ax5.axvline(-particle_radius, color='gray', linestyle='--', alpha=0.7, label='Particle boundary')
    ax5.axvline(particle_radius, color='gray', linestyle='--', alpha=0.7)
    ax5.set_title('Cross-section Comparison\n(y = 0)', fontsize=12, fontweight='bold')
    ax5.set_xlabel('x')
    ax5.set_ylabel('Void Fraction')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Difference plot
    ax6 = fig.add_subplot(2, 4, 6)
    difference = void_ibm - void_cfdem
    im6 = ax6.contourf(X, Y, difference, levels=20, cmap='RdBu')
    ax6.add_patch(plt.Circle(particle_center, particle_radius, fill=False, edgecolor='black', linewidth=2))
    ax6.set_title('Difference (IBM - cfdemIB)\nHighlighting Method Differences', fontsize=12, fontweight='bold')
    ax6.set_xlabel('x')
    ax6.set_ylabel('y')
    ax6.set_aspect('equal')
    plt.colorbar(im6, ax=ax6, label='Void Fraction Difference')
    
    # 7. Interpolation kernels comparison
    ax7 = fig.add_subplot(2, 4, 7)
    r_values = np.linspace(0, 3*particle_radius, 200)
    
    # cfdemIB kernel (sharp step function)
    cfdem_kernel = np.where(r_values <= particle_radius, 0.0, 1.0)
    
    # IBM kernel (smooth transition)
    ibm_kernel = []
    for r in r_values:
        distance_to_surface = r - particle_radius
        if distance_to_surface <= -standard_ibm.support_radius:
            ibm_kernel.append(0.0)
        elif distance_to_surface >= standard_ibm.support_radius:
            ibm_kernel.append(1.0)
        else:
            normalized_distance = (distance_to_surface + standard_ibm.support_radius) / (2.0 * standard_ibm.support_radius)
            ibm_kernel.append(0.5 * (1.0 + np.tanh(4.0 * (normalized_distance - 0.5))))
    
    ax7.plot(r_values/particle_radius, cfdem_kernel, 'b-', linewidth=3, label='cfdemIB (Sharp)', marker='o', markersize=4)
    ax7.plot(r_values/particle_radius, ibm_kernel, 'r-', linewidth=3, label='Standard IBM (Smooth)', marker='s', markersize=4)
    ax7.axvline(1.0, color='gray', linestyle='--', alpha=0.7, label='Particle surface')
    ax7.set_title('Interpolation Kernel Functions\nRadial Profiles', fontsize=12, fontweight='bold')
    ax7.set_xlabel('r/R (normalized radius)')
    ax7.set_ylabel('Void Fraction')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    ax7.set_xlim(0, 3)
    
    # 8. Grid cells illustration
    ax8 = fig.add_subplot(2, 4, 8)
    # Draw a zoomed-in view of grid cells around particle boundary
    zoom_size = 0.5
    zoom_nx = 15
    zoom_ny = 15
    x_zoom = np.linspace(-zoom_size, zoom_size, zoom_nx)
    y_zoom = np.linspace(-zoom_size, zoom_size, zoom_ny)
    X_zoom, Y_zoom = np.meshgrid(x_zoom, y_zoom)
    
    # Draw grid cells
    for i in range(zoom_ny):
        for j in range(zoom_nx):
            cell_center = np.array([X_zoom[i, j], Y_zoom[i, j]])
            distance = np.linalg.norm(cell_center - np.array(particle_center))
            
            if distance < particle_radius * 1.2:  # Only show cells near particle
                dx_zoom = zoom_size * 2 / zoom_nx
                dy_zoom = zoom_size * 2 / zoom_ny
                rect = patches.Rectangle((X_zoom[i, j] - dx_zoom/2, Y_zoom[i, j] - dy_zoom/2),
                                       dx_zoom, dy_zoom, linewidth=1, edgecolor='blue', facecolor='none')
                ax8.add_patch(rect)
                
                # Color code based on intersection with particle
                if distance < particle_radius:
                    ax8.plot(X_zoom[i, j], Y_zoom[i, j], 'ro', markersize=6)  # Inside
                else:
                    ax8.plot(X_zoom[i, j], Y_zoom[i, j], 'go', markersize=6)  # Outside
    
    # Draw particle
    circle = plt.Circle(particle_center, particle_radius, fill=False, edgecolor='red', linewidth=3)
    ax8.add_patch(circle)
    ax8.set_title('Grid Cell Intersection\nwith Particle Boundary', fontsize=12, fontweight='bold')
    ax8.set_xlabel('x')
    ax8.set_ylabel('y')
    ax8.set_aspect('equal')
    ax8.set_xlim(-zoom_size, zoom_size)
    ax8.set_ylim(-zoom_size, zoom_size)
    ax8.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Save the plot
    output_file = os.path.join(output_dir, 'cfdem_ib_vs_ibm_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Visualization saved to: {output_file}")
    
    # Show the plot
    plt.show()
    
    return fig


def create_detailed_kernel_comparison():
    """Create a detailed comparison of interpolation kernels."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    particle_radius = 1.0
    r_values = np.linspace(0, 3*particle_radius, 300)
    
    # 1. cfdemIB Sharp Kernel
    cfdem_kernel = np.where(r_values <= particle_radius, 0.0, 1.0)
    ax1.plot(r_values/particle_radius, cfdem_kernel, 'b-', linewidth=4, label='cfdemIB')
    ax1.axvline(1.0, color='red', linestyle='--', alpha=0.7, label='Particle surface')
    ax1.set_title('cfdemIB Geometric Method\n(Binary Step Function)', fontweight='bold')
    ax1.set_xlabel('r/R (normalized radius)')
    ax1.set_ylabel('Void Fraction')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(-0.1, 1.1)
    
    # 2. Standard IBM Smooth Kernels (different smoothing parameters)
    support_factors = [1.2, 1.5, 2.0]
    colors = ['red', 'green', 'orange']
    
    for i, (support_factor, color) in enumerate(zip(support_factors, colors)):
        ibm = StandardIBM([0, 0], particle_radius, support_factor)
        ibm_kernel = []
        for r in r_values:
            distance_to_surface = r - particle_radius
            if distance_to_surface <= -ibm.support_radius:
                ibm_kernel.append(0.0)
            elif distance_to_surface >= ibm.support_radius:
                ibm_kernel.append(1.0)
            else:
                normalized_distance = (distance_to_surface + ibm.support_radius) / (2.0 * ibm.support_radius)
                ibm_kernel.append(0.5 * (1.0 + np.tanh(4.0 * (normalized_distance - 0.5))))
        
        ax2.plot(r_values/particle_radius, ibm_kernel, color=color, linewidth=3, 
                label=f'IBM (support={support_factor:.1f}R)')
    
    ax2.axvline(1.0, color='gray', linestyle='--', alpha=0.7, label='Particle surface')
    ax2.set_title('Standard IBM Method\n(Smooth Transition Functions)', fontweight='bold')
    ax2.set_xlabel('r/R (normalized radius)')
    ax2.set_ylabel('Void Fraction')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_ylim(-0.1, 1.1)
    
    # 3. Gradient comparison
    dr = r_values[1] - r_values[0]
    cfdem_gradient = np.gradient(cfdem_kernel, dr)
    
    ax3.plot(r_values/particle_radius, cfdem_gradient/particle_radius, 'b-', linewidth=3, label='cfdemIB gradient')
    
    # IBM gradient for support_factor = 1.5
    ibm = StandardIBM([0, 0], particle_radius, 1.5)
    ibm_kernel = []
    for r in r_values:
        distance_to_surface = r - particle_radius
        if distance_to_surface <= -ibm.support_radius:
            ibm_kernel.append(0.0)
        elif distance_to_surface >= ibm.support_radius:
            ibm_kernel.append(1.0)
        else:
            normalized_distance = (distance_to_surface + ibm.support_radius) / (2.0 * ibm.support_radius)
            ibm_kernel.append(0.5 * (1.0 + np.tanh(4.0 * (normalized_distance - 0.5))))
    
    ibm_gradient = np.gradient(ibm_kernel, dr)
    ax3.plot(r_values/particle_radius, ibm_gradient/particle_radius, 'r-', linewidth=3, label='IBM gradient')
    
    ax3.axvline(1.0, color='gray', linestyle='--', alpha=0.7, label='Particle surface')
    ax3.set_title('Gradient Comparison\n(Sharpness of Transitions)', fontweight='bold')
    ax3.set_xlabel('r/R (normalized radius)')
    ax3.set_ylabel('d(VoidFraction)/dr')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Support radius illustration
    theta = np.linspace(0, 2*np.pi, 100)
    particle_x = particle_radius * np.cos(theta)
    particle_y = particle_radius * np.sin(theta)
    
    ax4.plot(particle_x, particle_y, 'b-', linewidth=3, label='Particle boundary')
    
    # Show support radius for IBM
    support_radius = 1.5 * particle_radius
    support_x = support_radius * np.cos(theta)
    support_y = support_radius * np.sin(theta)
    ax4.plot(support_x, support_y, 'r--', linewidth=2, label='IBM support radius')
    
    # Fill the support zone
    ax4.fill_between(support_x, support_y, alpha=0.2, color='red', label='IBM influence zone')
    ax4.fill_between(particle_x, particle_y, alpha=0.3, color='blue', label='Particle volume')
    
    ax4.set_title('Influence Zones Comparison\ncfdemIB (sharp) vs IBM (smooth)', fontweight='bold')
    ax4.set_xlabel('x/R')
    ax4.set_ylabel('y/R')
    ax4.set_aspect('equal')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.set_xlim(-2.5, 2.5)
    ax4.set_ylim(-2.5, 2.5)
    
    plt.tight_layout()
    
    # Save the detailed kernel comparison
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, 'cfdem_ib_kernel_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Kernel comparison saved to: {output_file}")
    
    plt.show()
    
    return fig


def main():
    """Main function to generate all visualizations."""
    print("CFDEMcoupling Visualization Script")
    print("==================================")
    print("Generating visualizations comparing cfdemIB geometric method and standard IBM...")
    print()
    
    # Generate main comparison visualization
    print("1. Creating comprehensive comparison visualization...")
    fig1 = visualize_cfdem_ib_vs_ibm()
    
    print()
    print("2. Creating detailed kernel function comparison...")
    fig2 = create_detailed_kernel_comparison()
    
    print()
    print("Visualization generation completed!")
    print("Generated files:")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"  - {os.path.join(output_dir, 'cfdem_ib_vs_ibm_comparison.png')}")
    print(f"  - {os.path.join(output_dir, 'cfdem_ib_kernel_comparison.png')}")
    print()
    print("Key differences highlighted:")
    print("  • cfdemIB: Binary inside/outside determination with geometric ratios")
    print("  • Standard IBM: Continuous interpolation with smooth kernels")
    print("  • cfdemIB: Sharp boundaries, no smoothing")
    print("  • Standard IBM: Smooth transitions, wider influence zone")


if __name__ == "__main__":
    main()