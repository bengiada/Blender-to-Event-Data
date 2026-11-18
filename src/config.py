import argparse
import sys

DEFAULT_CONFIG = {
    "output_dir": "../dataset/",
    "num_frames": 10000,
    "fps": 1000,
    
    #object
    "object_type": "SPHERE",
    "object_size": 1.0,
    "object_location": [0.0, 0.0, 0.0],
    "object_rotation": [0.0, 0.0, 0.0], #in radians
    
    #object material
    "object_color": [0.5, 0.5, 0.5, 1.0], #RGBA
    "object_roughness": 0.5,
    "object_metallic": 0.0,
    
    #ligth - not changable right now? - TODO: make a list of lights?
    "light_orbit_radius": 2.5,
    "light_orbit_height": 0.5,
    "light_rotations": 5.0,
    "light_energy": 1000.0,
    "light_size": 0.05,
    "light_color": [1.0, 1.0, 1.0],
    
    "camera_distance": 4.0,
    "camera_height": 0.5,
    "focal_length_mm": 50.0,
    
    "resolution_x": 640,
    "resolution_y": 480,
    
    "render_engine": "BLENDER_EEVEE",
    "image_format": "PNG",
    "look": "AgX - Medium High Contrast",
    
    "seed": 42,
    "video_fps": 30,
}


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--frames", type=int, default=None)
    parser.add_argument("--fps", type=int, default=None)
    parser.add_argument("--rotations", type=float, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--resolution", type=int, nargs=2, default=None)
    
    parser.add_argument(
        "--object",
        type=str,
        choices=["SPHERE", "CUBE","CONE","MONKEY"],
        default=None
    )
    
    parser.add_argument(
        "--object-location",
        type=float,
        nargs=3,
        default=[0.0,0.0,0.0]
    )
    
    parser.add_argument(
        "--object-rotation",
        type=float,
        nargs=3,
        default=[0.0,0.0,0.0]
    )
    
    parser.add_argument(
        "--object-color",
        type=float,
        nargs=4,
        default=None
    )
    parser.add_argument(
        "--object-roughness",
        type=float,
        default=None
    )
    parser.add_argument(
        "--object-metallic",
        type=float,
        default=None
    )
    
    
    parser.add_argument("--seed", type=int, default=None)

    parser.add_argument( #fps of mp4
        "--video-fps",
        type=int,
        default=None,
    )
    
    #TODO: Light arguments - can be customizable

    # To remove Blender's arguments - crashes otherwise
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    return parser.parse_args(argv)

def build_config():
    config = DEFAULT_CONFIG.copy()
    args = parse_args()

    if args.frames is not None:
        config["num_frames"] = args.frames
    if args.fps is not None:
        config["fps"] = args.fps
    if args.rotations is not None:
        config["light_rotations"] = args.rotations
    if args.output is not None:
        config["output_dir"] = args.output
        
    if args.object is not None:
        config["object_type"] = args.object
    if args.object_rotation is not None:
        config["object_rotation"] = args.object_rotation
    if args.object_location is not None:
        config["object_location"] = args.object_location
                
    if args.object_color is not None:
        config["object_color"] = args.object_color
    if args.object_roughness is not None:
        config["object_roughness"] = args.object_roughness
    if args.object_metallic is not None:
        config["object_metallic"] = args.object_metallic    
    
    if args.resolution is not None:
        config["resolution_x"], config["resolution_y"] = args.resolution
    if args.seed is not None:
        config["seed"] = args.seed

    if args.video_fps is not None:
        config["video_fps"] = args.video_fps

    return config
