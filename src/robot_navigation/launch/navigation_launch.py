#!/usr/bin/env python3
"""
Nav2 navigation launch — AMCL localization + full Nav2 stack on a saved map.
Run AFTER saving a map from the SLAM phase.

Usage:
  ros2 launch robot_navigation navigation_launch.py map:=/path/to/map.yaml
"""

import os
from launch_ros.actions import Node # type: ignore
from ament_index_python.packages import get_package_share_directory # type: ignore
from launch import LaunchDescription # type: ignore
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo # type: ignore
from launch.launch_description_sources import PythonLaunchDescriptionSource # type: ignore
from launch.substitutions import LaunchConfiguration # type: ignore

def generate_launch_description():
    pkg_nav = get_package_share_directory("robot_navigation")
    pkg_nav2_bringup = get_package_share_directory("nav2_bringup")

    declare_map = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(pkg_nav, "maps", "house_map.yaml"),
        description="Full path to map yaml file",
    )
    declare_params_file = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(pkg_nav, "config", "nav2_params.yaml"),
        description="Full path to Nav2 params file",
    )
    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time", default_value="true",
    )
    declare_autostart = DeclareLaunchArgument(
        "autostart", default_value="true",
    )

    # Nav2 Bringup (AMCL + Navigation stack)
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "map":          LaunchConfiguration("map"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "params_file":  LaunchConfiguration("params_file"),
            "autostart":    LaunchConfiguration("autostart"),
        }.items(),
    )

    # Collision Monitor - needs to be launched explicitly as it's not in bringup_launch.py
    collision_monitor_node = Node(
        package='nav2_collision_monitor',
        executable='collision_monitor',
        name='collision_monitor',
        output='screen',
        parameters=[LaunchConfiguration("params_file")],
    )

    return LaunchDescription([
        declare_map,
        declare_params_file,
        declare_use_sim_time,
        declare_autostart,
        LogInfo(msg=["\033[94m[Navigation Bringup] Starting Nav2 stack on map: \033[0m", LaunchConfiguration("map")]),
        nav2_launch,
        collision_monitor_node,
    ])
