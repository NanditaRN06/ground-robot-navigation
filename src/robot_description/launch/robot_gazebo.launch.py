#!/usr/bin/env python3
"""
Gazebo Harmonic simulation launch for the ground robot.

Usage:
  ros2 launch robot_description robot_gazebo.launch.py
  ros2 launch robot_description robot_gazebo.launch.py world:=office use_rviz:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_desc      = get_package_share_directory("robot_description")
    pkg_ros_gz    = get_package_share_directory("ros_gz_sim")

    # worlds/ is at workspace_root/worlds — resolve from install path
    ws_root    = os.path.realpath(os.path.join(pkg_desc, "..", "..", "..", ".."))
    worlds_dir = os.path.join(ws_root, "worlds")

    # ── Launch arguments ──────────────────────────────────────────────────
    declare_world      = DeclareLaunchArgument("world",       default_value="house",  description="World name (house|office)")
    declare_use_rviz   = DeclareLaunchArgument("use_rviz",    default_value="true",   description="Launch RViz2")
    declare_rviz_cfg   = DeclareLaunchArgument("rviz_config", default_value=os.path.join(pkg_desc, "config", "robot.rviz"), description="RViz2 config path")
    declare_x          = DeclareLaunchArgument("x",   default_value="1.0")
    declare_y          = DeclareLaunchArgument("y",   default_value="1.0")
    declare_z          = DeclareLaunchArgument("z",   default_value="0.05")
    declare_yaw        = DeclareLaunchArgument("yaw", default_value="0.0")

    world      = LaunchConfiguration("world")
    use_rviz   = LaunchConfiguration("use_rviz")
    rviz_cfg   = LaunchConfiguration("rviz_config")
    spawn_x    = LaunchConfiguration("x")
    spawn_y    = LaunchConfiguration("y")
    spawn_z    = LaunchConfiguration("z")
    spawn_yaw  = LaunchConfiguration("yaw")

    # ── Robot description from xacro ─────────────────────────────────────
    xacro_file = os.path.join(pkg_desc, "urdf", "robot.xacro")
    robot_desc = Command([FindExecutable(name="xacro"), " ", xacro_file])

    # ── robot_state_publisher ─────────────────────────────────────────────
    # use_sim_time=True so TF timestamps align with /clock from Gazebo.
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

    # ── Gazebo Harmonic ───────────────────────────────────────────────────
    def launch_gazebo(context, *args, **kwargs):
        world_name = context.perform_substitution(world)
        world_sdf  = os.path.join(worlds_dir, f"{world_name}.sdf")
        if not os.path.isfile(world_sdf):
            raise FileNotFoundError(f"World SDF not found: {world_sdf}")
        return [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_ros_gz, "launch", "gz_sim.launch.py")
                ),
                launch_arguments={
                    "gz_args": f"{world_sdf} -r",
                    "on_exit_shutdown": "true",
                }.items(),
            )
        ]

    # ── Spawn robot ───────────────────────────────────────────────────────
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

    # ── ros_gz_bridge ─────────────────────────────────────────────────────
    bridge_cfg = os.path.join(pkg_desc, "config", "gz_bridge.yaml")
    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_cfg}"],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # ── RViz2 ─────────────────────────────────────────────────────────────
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
        rsp_node,
        OpaqueFunction(function=launch_gazebo),
        spawn_node,
        bridge_node,
        rviz_node,
    ])
