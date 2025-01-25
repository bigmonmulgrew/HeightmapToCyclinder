import numpy as np
from PIL import Image
import math
import os
import sys

# Constants
PIXEL_SIZE = 0.019  # 19μm resolution
DEPTH_FACTOR = 0.1  # Max depth is 10% of the cylinder radius  TODO make it an explicit mm value

def load_heightmap(image_path):
    """Load the heightmap and return a normalized grayscale array."""
    image = Image.open(image_path).convert('L')  # Convert to grayscale
    heightmap = np.array(image, dtype=np.float32)
    heightmap = 1.0 - (heightmap / 255.0)  # Invert heightmap (White = low, Black = high)
    return heightmap

def process_vertices(heightmap, radius, max_depth):
    """Generate vertices, uvs, and normals for the cylindrical mesh."""
    height, width = heightmap.shape
    vertices = []
    uvs = []
    normals = []
    
    for y in range(height):
        sys.stdout.write(f"\rProcessing row {y+1}/{height}   ")  # Overwrite same line
        sys.stdout.flush()
        for x in range(width):
            theta = (x * (2 * math.pi)) / (width - 1)
            world_z = (y / (height - 1)) * (height * PIXEL_SIZE)
            base_x = radius * math.cos(theta)
            base_y = radius * math.sin(theta)
            
            center_x, center_y = 0, 0
            vector_x = base_x - center_x
            vector_y = base_y - center_y
            length = math.sqrt(vector_x ** 2 + vector_y ** 2)
            depth_offset = heightmap[y, x] * max_depth
            if length > 0:
                scale = (radius - depth_offset) / length
                adjusted_x = center_x + vector_x * scale
                adjusted_y = center_y + vector_y * scale
            else:
                adjusted_x, adjusted_y = base_x, base_y
            
            vertices.append((adjusted_x, adjusted_y, world_z))
            uvs.append((x / (width - 1), y / (height - 1)))
            normals.append((math.cos(theta), math.sin(theta), 0))
    
    print("\nProcessing complete.")
    return vertices, uvs, normals

def process_faces(height, width):
    """Generate face indices for the cylindrical mesh."""
    faces = []
    for y in range(height - 1):
        for x in range(width - 1):
            v0 = y * width + x
            v1 = v0 + 1
            v2 = v0 + width
            v3 = v2 + 1
            
            faces.append((v0, v1, v3))
            faces.append((v0, v3, v2))
    
    for y in range(height - 1):
        v0 = y * width + (width - 1)
        v1 = y * width
        v2 = (y + 1) * width + (width - 1)
        v3 = (y + 1) * width
        
        faces.append((v0, v1, v3))
        faces.append((v0, v3, v2))
    
    return faces

def save_obj(filename, vertices, faces, uvs, normals):
    """Save the generated mesh to an OBJ file."""
    with open(filename, 'w') as f:
        for v in vertices:
            f.write(f'v {v[0]} {v[1]} {v[2]}\n')
        for vt in uvs:
            f.write(f'vt {vt[0]} {vt[1]}\n')
        for vn in normals:
            f.write(f'vn {vn[0]} {vn[1]} {vn[2]}\n')
        for face in faces:
            f.write(f'f {face[0]+1}/{face[0]+1}/{face[0]+1} {face[1]+1}/{face[1]+1}/{face[1]+1} {face[2]+1}/{face[2]+1}/{face[2]+1}\n')

def save_metadata(filename, height, width, radius, vertex_count, face_count, obj_filename):
    """Save metadata about the processed heightmap conversion."""
    with open(filename, 'w') as f:
        f.write(f'Image size: {width}x{height}\n')
        f.write(f'Cylinder height: {height * PIXEL_SIZE}\n')
        f.write(f'Cylinder radius: {radius}\n')
        f.write(f'Total number of vertices: {vertex_count}\n')
        f.write(f'Total number of triangles: {face_count}\n')
        f.write(f'Total file size: {os.path.getsize(obj_filename)} bytes\n')

def process_images():
    """List images and allow batch processing or selection."""
    images = [f for f in os.listdir() if f.endswith(('.png', '.jpg', '.jpeg'))]
    if len(images) == 1:
        selected_images = images
    else:
        print("Select an image to process:")
        for i, img in enumerate(images[:9]):
            print(f"{i+1}. {img}")
        print("0. Process all")
        choice = int(input("Enter your choice: "))
        batch_process = False
        
        if choice == 0:
            selected_images = images
            batch_process = bool(input("Process all, y or n: ") == "y")
        else:
            selected_images = [images[choice - 1]]
    
    for image in selected_images:
        heightmap = load_heightmap(image)
        height, width = heightmap.shape
        radius = (width * PIXEL_SIZE) / (2 * math.pi)
        max_depth = radius * DEPTH_FACTOR
        
        vertices, uvs, normals = process_vertices(heightmap, radius, max_depth)
        faces = process_faces(height, width)
        
        obj_filename = image.replace('.png', '.obj')
        txt_filename = image.replace('.png', '.txt')
        save_obj(obj_filename, vertices, faces, uvs, normals)
        save_metadata(txt_filename, height, width, radius, len(vertices), len(faces),obj_filename)
        
        if len(selected_images) > 1 and not batch_process:
            input("Press Enter to continue to the next image...")

# Run image processing
process_images()
