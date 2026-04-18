#!/usr/bin/env python3
"""
PHASE 1: SLAM Bringup Launch
────────────────────────────
Starts the full Gazebo simulation + robot + SLAM mapping stack.
Drive the robot around using teleop to build the map, then save it.

Usage:
  ros2 launch robot_bringup slam_bringup.launch.py
  ros2 launch robot_bringup slam_bringup.launch.py world:=office

After mapping:
  ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map --ros-args -p use_sim_time:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    pkg_robot_description = get_package_share_directory("robot_description")
    pkg_robot_navigation  = get_package_share_directory("robot_navigation")

    # ── Launch Arguments ──────────────────────────────────────────────────
    declare_world = DeclareLaunchArgument(
        "world",
        default_value="house",
        description="World name (house | office)",
    )
    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz",
        default_value="false",
        description="Start RViz2 (default off — launch separately for lower load)",
    )

    # SLAM-specific RViz config: Fixed Frame=odom, no Nav2 panel
    slam_rviz_config = os.path.join(pkg_robot_description, "config", "slam.rviz")

    # ── Gazebo + Robot Simulation ─────────────────────────────────────────
    robot_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_robot_description, "launch", "robot_gazebo.launch.py")
        ),
        launch_arguments={
            "world":       LaunchConfiguration("world"),
            "use_rviz":    LaunchConfiguration("use_rviz"),
            "rviz_config": slam_rviz_config,
            "x": "1.0",
            "y": "1.0",
            "z": "0.05",
        }.items(),
    )

    # ── SLAM (slam_toolbox) - delayed 5s to let Gazebo fully start ─────────
    slam_launch = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_robot_navigation, "launch", "slam_launch.py")
                ),
                launch_arguments={
                    "use_sim_time": "true",
                }.items(),
            )
        ]
    )

    return LaunchDescription([
        declare_world,
        declare_use_rviz,
        robot_sim_launch,
        slam_launch,
    ])
