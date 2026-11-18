import sys
sys.path.append('')

import os
import shutil
import json
import math
import subprocess
import random
import logging

#for blender
import bpy
from mathutils import Vector

from config import build_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def create_material(config):
    material = bpy.data.materials.new(name="ObjectMaterial")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")

    if bsdf:
        bsdf.inputs["Base Color"].default_value = config["object_color"]
        bsdf.inputs["Roughness"].default_value = config["object_roughness"]
        bsdf.inputs["Metallic"].default_value = config["object_metallic"]

    return material


def create_object(config):
    location = config["object_location"]
    rotation = config["object_rotation"]

    if config["object_type"] == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=64,
            ring_count=32,
            radius=config["object_size"],
            location=location,
            rotation=rotation
        )
    elif config["object_type"] == "CUBE":
        bpy.ops.mesh.primitive_cube_add(
            size=config["object_size"],
            location=location,
            rotation=rotation
        )
    elif config["object_type"] == "CONE":
        bpy.ops.mesh.primitive_cone_add(
            size=config["object_size"],
            location=location,
            rotation=rotation
    )
    elif config["object_type"] == "MONKEY":
        bpy.ops.mesh.primitive_monkey_add(
        size=config["object_size"],
        location=location,
        rotation=rotation
    )
    else:
        raise ValueError(f"Unknown object type: {config['object_type']}")
    
    #TODO: Add custom object types

    obj = bpy.context.object
    obj.name = "Object"
    obj.data.materials.append(create_material(config))
    return obj


def create_light(config):
    data = bpy.data.lights.new(name="MovingLight", type="POINT")
    data.energy = config["light_energy"]
    data.color = config["light_color"]
    data.shadow_soft_size = config["light_size"]

    light = bpy.data.objects.new(name="MovingLight", object_data=data)
    bpy.context.collection.objects.link(light)
    
    #TODO: Multiple lights???
    return light

    

def create_camera(config, target):
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)

    camera.data.lens = config["focal_length_mm"]
    camera.location = (
        0.0,
        config["camera_distance"],
        config["camera_height"],
    )
    
    #points the camera at the objct
    direction = target.location - camera.location 
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        
    bpy.context.scene.camera = camera


def configure_world(config):
    world = bpy.context.scene.world
    
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")

    if background: #background is black for now
        background.inputs["Color"].default_value = [0.0, 0.0, 0.0, 1.0]
        background.inputs["Strength"].default_value = 0.0


def configure_render(config):
    scene = bpy.context.scene
    
    scene.render.engine = config["render_engine"]
    scene.render.resolution_x = config["resolution_x"]
    scene.render.resolution_y = config["resolution_y"]
    scene.render.resolution_percentage = 100
    scene.render.fps = config["fps"]
    scene.render.image_settings.file_format = config["image_format"]
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False

    scene.view_settings.look = config["look"]


def light_position(frame, config, target): #TODO: rotation from different angles & anticlockwise???
    n = config["num_frames"]
    t = 0.0 if n <= 1 else (frame - 1) / (n - 1)
    angle = 2.0 * math.pi * config["light_rotations"] * t
    
    radius = config["light_orbit_radius"]
    height = config["light_orbit_height"]
    center = Vector(target.location)

    return (
        center.x + radius * math.cos(angle),
        center.y + radius * math.sin(angle),
        center.z + height,
    )


def create_frame_handler(config, light, target):
    def handler(scene):
        light.location = light_position(scene.frame_current, config, target)

    return handler


def save_config(config, output_dir):
    path = os.path.join(output_dir, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    return path


def encode_video(frames_dir, output_path, video_fps):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("No FFMPEG")

    pattern = os.path.join(frames_dir, "frame_%04d.png")
    cmd = [ffmpeg, "-y", "-framerate", str(video_fps), "-start_number", "1", "-i", pattern, "-c:v", "libx264", 
           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", output_path]

    logger.info("Encoding MP4 with ffmpeg")
    logger.info(" ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    
    config = build_config()
    random.seed(config["seed"])

    output_dir = bpy.path.abspath(config["output_dir"])
    os.makedirs(output_dir, exist_ok=True)

    #frame directory    
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    clear_scene()
    
    scene = bpy.context.scene
    configure_world(config)
    configure_render(config)

    target = create_object(config)
    light = create_light(config)
    create_camera(config, target)

    handler = create_frame_handler(config, light, target)
    bpy.app.handlers.frame_change_pre.append(handler)

    scene.frame_start = 1
    scene.frame_end = config["num_frames"]
    scene.render.filepath = os.path.join(frames_dir, "frame_")

    config_path = save_config(config, output_dir)

    blend_path = os.path.join(output_dir, "scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    duration = config["num_frames"] / config["fps"]
    rotation_frequency = config["light_rotations"] / duration

    logger.info("BLENDER ANIMATION") 
    logger.info(f"Frames: {config['num_frames']}")
    logger.info(f"Simulation FPS: {config['fps']}")
    logger.info(f"Duration: {duration:.4f} s")
    logger.info(f"Resolution: {config['resolution_x']} x {config['resolution_y']}")
    logger.info(f"Video FPS: {config['video_fps']}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Frames: {frames_dir}")
    logger.info(f"Config: {config_path}")
    logger.info(f"Blend File: {blend_path}")
    
    logger.info("Starting rendering")
    bpy.ops.render.render(animation=True)
    logger.info("Render complete")

    video_path = os.path.join(output_dir, "video.mp4")
    encode_video(frames_dir, video_path, config["video_fps"])
    logger.info(f"MP4 saved to: {video_path}")


    bpy.app.handlers.frame_change_pre.remove(handler)


    logger.info(f"Frames: {os.path.join(output_dir, 'frames')}")
    logger.info(f"Video: {os.path.join(output_dir, 'video.mp4')}")
    logger.info(f"Scene: {blend_path}")

