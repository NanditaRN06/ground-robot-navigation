#!/usr/bin/env python3
"""
Gazebo Harmonic simulation launch for the ground robot.

Usage:
  ros2 launch robot_description robot_gazebo.launch.py
  ros2 launch robot_description robot_gazebo.launch.py world:=office use_rviz:=false

Key fixes vs naive implementation:
  1. World SDF path with spaces: uses ExecuteProcess cmd=[] list so
     subprocess receives the path as a single argument (no shell splitting).
  2. static_transform_publisher nodes fire at startup with timestamp=0
     (valid for ALL time) so SLAM's tf2 MessageFilter resolves lidar_link
     before Gazebo's /clock even arrives.
  3. joint_state_publisher provides wheel positions for RViz model display.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_desc   = get_package_share_directory("robot_description")

    # worlds/ lives at workspace_root/worlds — resolved from the install path.
    # os.path.realpath follows symlinks so colcon --symlink-install works.
    ws_root    = os.path.realpath(os.path.join(pkg_desc, "..", "..", "..", ".."))
    worlds_dir = os.path.join(ws_root, "worlds")

    # ── Launch arguments ──────────────────────────────────────────────────────
    declare_world    = DeclareLaunchArgument("world",    default_value="house",
                                             description="World name (house|office)")
    declare_use_rviz = DeclareLaunchArgument("use_rviz", default_value="true",
                                             description="Launch RViz2")
    declare_rviz_cfg = DeclareLaunchArgument(
        "rviz_config",
        default_value=os.path.join(pkg_desc, "config", "robot.rviz"),
        description="RViz2 config path")
    declare_x   = DeclareLaunchArgument("x",   default_value="1.0")
    declare_y   = DeclareLaunchArgument("y",   default_value="1.0")
    declare_z   = DeclareLaunchArgument("z",   default_value="0.05")
    declare_yaw = DeclareLaunchArgument("yaw", default_value="0.0")

    world    = LaunchConfiguration("world")
    use_rviz = LaunchConfiguration("use_rviz")
    rviz_cfg = LaunchConfiguration("rviz_config")
    spawn_x  = LaunchConfiguration("x")
    spawn_y  = LaunchConfiguration("y")
    spawn_z  = LaunchConfiguration("z")
    spawn_yaw= LaunchConfiguration("yaw")

    # ── Robot description from xacro ──────────────────────────────────────────
    xacro_file = os.path.join(pkg_desc, "urdf", "robot.xacro")
    robot_desc = Command([FindExecutable(name="xacro"), " ", xacro_file])

    # ── Immediate static TF publishers (timestamp=0, valid for ALL time) ──────
    # These fire before Gazebo's /clock so SLAM's tf2 MessageFilter can resolve
    # lidar_link on the very first scan. Values match robot.xacro joint origins:
    #   base_footprint→base_link : z = wheel_radius = 0.05
    #   base_link→lidar_link     : z = base_height/2 + lidar_height/2 = 0.04+0.02 = 0.06
    #   base_link→imu_link       : z = base_height/4 = 0.02
    #   base_link→caster_link    : x = base_radius*0.6 = 0.114, z = -(wheel_radius-caster_radius) = -0.025
    static_tf_base = Node(
        package="tf2_ros", executable="static_transform_publisher",
        name="static_tf_base_footprint_to_base_link",
        arguments=["--x", "0", "--y", "0", "--z", "0.05",
                   "--roll", "0", "--pitch", "0", "--yaw", "0",
                   "--frame-id", "base_footprint", "--child-frame-id", "base_link"],
    )
    static_tf_lidar = Node(
        package="tf2_ros", executable="static_transform_publisher",
        name="static_tf_base_link_to_lidar_link",
        arguments=["--x", "0", "--y", "0", "--z", "0.06",
                   "--roll", "0", "--pitch", "0", "--yaw", "0",
                   "--frame-id", "base_link", "--child-frame-id", "lidar_link"],
    )
    static_tf_imu = Node(
        package="tf2_ros", executable="static_transform_publisher",
        name="static_tf_base_link_to_imu_link",
        arguments=["--x", "0", "--y", "0", "--z", "0.02",
                   "--roll", "0", "--pitch", "0", "--yaw", "0",
                   "--frame-id", "base_link", "--child-frame-id", "imu_link"],
    )
    static_tf_caster = Node(
        package="tf2_ros", executable="static_transform_publisher",
        name="static_tf_base_link_to_caster_link",
        arguments=["--x", "0.114", "--y", "0", "--z", "-0.025",
                   "--roll", "0", "--pitch", "0", "--yaw", "0",
                   "--frame-id", "base_link", "--child-frame-id", "caster_link"],
    )

    # ── robot_state_publisher ─────────────────────────────────────────────────
    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"robot_description": robot_desc},
            {"use_sim_time": True},
        ],
    )

    # ── joint_state_publisher (wheel positions for RViz model) ────────────────
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # ── Gazebo Harmonic ───────────────────────────────────────────────────────
    # CRITICAL: use ExecuteProcess with cmd as a LIST — each element is passed
    # as a separate subprocess argument, so spaces inside world_sdf are safe.
    # IncludeLaunchDescription/gz_args passes the path as a string that gets
    # split on spaces, breaking paths like /mnt/c/Users/Nandita R Nadig/...
    def launch_gazebo(context, *args, **kwargs):
        world_name = context.perform_substitution(world)
        world_sdf  = os.path.join(worlds_dir, f"{world_name}.sdf")
        if not os.path.isfile(world_sdf):
            raise FileNotFoundError(
                f"World SDF not found: {world_sdf}\n"
                f"  worlds_dir resolved to: {worlds_dir}\n"
                f"  Ensure the 'worlds/' directory exists at workspace root."
            )
        return [
            ExecuteProcess(
                cmd=["gz", "sim", world_sdf, "-r", "--force-version", "8"],
                output="screen",
                additional_env={"GZ_SIM_RESOURCE_PATH": os.path.dirname(world_sdf)},
            )
        ]

    # ── Spawn robot ───────────────────────────────────────────────────────────
    spawn_node = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_robot",
        arguments=[
            "-topic", "robot_description",
            "-name",  "ground_robot",
            "-x", spawn_x, "-y", spawn_y, "-z", spawn_z, "-Y", spawn_yaw,
        ],
        output="screen",
    )

    # ── ros_gz_bridge ─────────────────────────────────────────────────────────
    bridge_cfg  = os.path.join(pkg_desc, "config", "gz_bridge.yaml")
    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_cfg}"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # ── RViz2 ─────────────────────────────────────────────────────────────────
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_cfg],
        parameters=[{"use_sim_time": True}],
        output="screen",
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        declare_world,
        declare_use_rviz,
        declare_rviz_cfg,
        declare_x, declare_y, declare_z, declare_yaw,
        static_tf_base,
        static_tf_lidar,
        static_tf_imu,
        static_tf_caster,
        rsp_node,
        joint_state_publisher_node,
        OpaqueFunction(function=launch_gazebo),
        spawn_node,
        bridge_node,
        rviz_node,
    ])
