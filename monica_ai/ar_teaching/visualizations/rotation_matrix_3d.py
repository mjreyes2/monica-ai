"""
3D Rotation Matrix Visualization using PyVista
Interactive demonstration of 3D rotations
"""

import numpy as np
import pyvista as pv
from pyvista import examples

def create_rotation_matrix_x(angle):
    """Create rotation matrix around X-axis."""
    rad = np.radians(angle)
    return np.array([
        [1, 0, 0],
        [0, np.cos(rad), -np.sin(rad)],
        [0, np.sin(rad), np.cos(rad)]
    ])

def create_rotation_matrix_y(angle):
    """Create rotation matrix around Y-axis."""
    rad = np.radians(angle)
    return np.array([
        [np.cos(rad), 0, np.sin(rad)],
        [0, 1, 0],
        [-np.sin(rad), 0, np.cos(rad)]
    ])

def create_rotation_matrix_z(angle):
    """Create rotation matrix around Z-axis."""
    rad = np.radians(angle)
    return np.array([
        [np.cos(rad), -np.sin(rad), 0],
        [np.sin(rad), np.cos(rad), 0],
        [0, 0, 1]
    ])

def visualize_3d_rotation():
    """
    Interactive 3D rotation visualization.
    Shows how rotation matrices transform objects in 3D space.
    """
    
    # Create plotter
    plotter = pv.Plotter()
    plotter.set_background('black')
    
    # Create a cube
    cube = pv.Cube()
    
    # Add coordinate axes
    axes = pv.Axes(show_actor=True, actor_scale=2.0, line_width=5)
    plotter.add_actor(axes.actor)
    
    # Add cube
    cube_actor = plotter.add_mesh(
        cube,
        color='cyan',
        opacity=0.8,
        show_edges=True,
        edge_color='white',
        line_width=2
    )
    
    # Add title
    plotter.add_text(
        "3D Rotation Matrix Visualization\nUse mouse to rotate view",
        position='upper_left',
        font_size=12,
        color='yellow'
    )
    
    # Add instructions
    instructions = """
    X-axis: Red
    Y-axis: Green  
    Z-axis: Blue
    
    Rotation Matrix Example:
    Rotate 45° around Z-axis
    """
    
    plotter.add_text(
        instructions,
        position='lower_left',
        font_size=10,
        color='white'
    )
    
    # Show the plot
    plotter.show()

def visualize_rotation_sequence():
    """
    Show step-by-step rotation around different axes.
    """
    
    # Create cube
    cube = pv.Cube()
    
    # Rotation angles
    angles = [0, 30, 60, 90]
    
    # Create subplot for each rotation
    plotter = pv.Plotter(shape=(2, 2))
    plotter.set_background('black')
    
    for i, angle in enumerate(angles):
        row = i // 2
        col = i % 2
        plotter.subplot(row, col)
        
        # Apply rotation around Z-axis
        rotation_matrix = create_rotation_matrix_z(angle)
        
        # Transform cube vertices
        rotated_cube = cube.copy()
        rotated_cube.points = rotated_cube.points @ rotation_matrix.T
        
        # Add mesh
        plotter.add_mesh(
            rotated_cube,
            color='cyan',
            opacity=0.8,
            show_edges=True,
            edge_color='white'
        )
        
        # Add axes
        axes = pv.Axes(show_actor=True, actor_scale=1.5)
        plotter.add_actor(axes.actor)
        
        # Add title
        plotter.add_text(
            f"Rotation: {angle}° around Z-axis",
            font_size=10,
            color='yellow'
        )
    
    plotter.link_views()
    plotter.show()

def visualize_euler_angles():
    """
    Demonstrate Euler angles (rotation around X, Y, Z in sequence).
    """
    
    plotter = pv.Plotter()
    plotter.set_background('black')
    
    # Create cube
    cube = pv.Cube()
    
    # Apply Euler rotations: 30° around X, 45° around Y, 60° around Z
    rx = create_rotation_matrix_x(30)
    ry = create_rotation_matrix_y(45)
    rz = create_rotation_matrix_z(60)
    
    # Combined rotation (order matters!)
    combined_rotation = rz @ ry @ rx
    
    # Original cube (transparent)
    plotter.add_mesh(
        cube,
        color='gray',
        opacity=0.3,
        show_edges=True,
        edge_color='white'
    )
    
    # Rotated cube
    rotated_cube = cube.copy()
    rotated_cube.points = rotated_cube.points @ combined_rotation.T
    
    plotter.add_mesh(
        rotated_cube,
        color='cyan',
        opacity=0.8,
        show_edges=True,
        edge_color='white',
        line_width=2
    )
    
    # Add axes
    axes = pv.Axes(show_actor=True, actor_scale=2.0, line_width=5)
    plotter.add_actor(axes.actor)
    
    # Add title
    plotter.add_text(
        "Euler Angles: Rx(30°) * Ry(45°) * Rz(60°)",
        position='upper_left',
        font_size=12,
        color='yellow'
    )
    
    # Add matrix display
    matrix_text = f"""
    Combined Rotation Matrix:
    [{combined_rotation[0,0]:.2f}  {combined_rotation[0,1]:.2f}  {combined_rotation[0,2]:.2f}]
    [{combined_rotation[1,0]:.2f}  {combined_rotation[1,1]:.2f}  {combined_rotation[1,2]:.2f}]
    [{combined_rotation[2,0]:.2f}  {combined_rotation[2,1]:.2f}  {combined_rotation[2,2]:.2f}]
    """
    
    plotter.add_text(
        matrix_text,
        position='lower_left',
        font_size=8,
        color='white',
        font='courier'
    )
    
    plotter.show()

# Main function to run from AR teaching coordinator
def run_visualization(mode='basic'):
    """
    Run 3D rotation visualization.
    
    Args:
        mode: 'basic', 'sequence', or 'euler'
    """
    if mode == 'basic':
        visualize_3d_rotation()
    elif mode == 'sequence':
        visualize_rotation_sequence()
    elif mode == 'euler':
        visualize_euler_angles()
    else:
        visualize_3d_rotation()

if __name__ == "__main__":
    # Test the visualization
    print("Running 3D Rotation Matrix Visualization...")
    print("Close the window to continue...")
    run_visualization('basic')
