import os
import trimesh
import argparse
from pathlib import Path

def convert_fbx_to_format(input_fbx, output_file, output_format="obj"):
    """
    Convert an FBX file to another 3D format using trimesh.
    - input_fbx: Path to input FBX file.
    - output_file: Path to output file (e.g., 'output.obj').
    - output_format: Target format ('obj', 'stl', 'glb', etc.).
    """
    try:
        # Verify supported formats
        supported_formats = ['obj', 'stl', 'glb', 'ply', 'dae']
        if output_format not in supported_formats:
            print(f"Error: Output format '{output_format}' not supported. Use one of: {supported_formats}")
            return False

        # Load FBX with trimesh
        print(f"Loading FBX: {input_fbx}")
        mesh = trimesh.load(input_fbx, force='mesh')
        if isinstance(mesh, trimesh.Scene):
            print("FBX contains multiple meshes; combining...")
            mesh = mesh.dump(concatenate=True)
            if isinstance(mesh, list) and len(mesh) > 0:
                mesh = mesh[0]
        mesh.fix_normals()
        print(f"Exporting to {output_file} (format: {output_format})")
        mesh.export(output_file, file_type=output_format)
        print(f"Converted to {output_file}")
        return True
    except Exception as e:
        print(f"Error during trimesh conversion: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert FBX to 3D format (e.g., OBJ)")
    parser.add_argument("input", help="Path to input FBX file")
    parser.add_argument("output", help="Path to output file (e.g., output.obj)")
    parser.add_argument("--format", default="obj", help="Output format (obj, stl, glb, ply, dae)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} does not exist")
        exit(1)
    
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting conversion: {args.input} to {args.output}")
    success = convert_fbx_to_format(args.input, args.output, args.format)
    if success:
        print("Conversion completed successfully")
    else:
        print("Conversion failed")
        exit(1)