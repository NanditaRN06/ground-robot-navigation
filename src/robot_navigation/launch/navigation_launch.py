#!/usr/bin/env python3
"""
Nav2 navigation launch — AMCL localization + full Nav2 stack on a saved map.
Run AFTER saving a map from the SLAM phase.

Usage:
  ros2 launch robot_navigation navigation_launch.py map:=/path/to/map.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    pkg_nav          = get_package_share_directory("robot_navigation")
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

    # nav2_bringup's bringup_launch.py starts the full Nav2 stack:
    # map_server, amcl, controller_server, planner_server, bt_navigator,
    # behavior_server, smoother_server, waypoint_follower, velocity_smoother,
    # and both lifecycle managers.
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

    return LaunchDescription([
        declare_map,
        declare_params_file,
        declare_use_sim_time,
        declare_autostart,
        nav2_launch,
    ])
