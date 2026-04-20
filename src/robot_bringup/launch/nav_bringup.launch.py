#!/usr/bin/env python3
"""
Navigation Bringup - Gazebo + Nav2 + autonomous waypoint navigation.

Usage:
  ros2 launch robot_bringup nav_bringup.launch.py
  ros2 launch robot_bringup nav_bringup.launch.py map:=/home/user/maps/house_map.yaml
  ros2 launch robot_bringup nav_bringup.launch.py auto_navigate:=false  # manual goal via RViz
"""

import os

from ament_index_python.packages import get_package_share_directory # type: ignore
from launch import LaunchDescription # type: ignore     
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction # type: ignore
from launch.conditions import IfCondition # type: ignore
from launch.launch_description_sources import PythonLaunchDescriptionSource # type: ignore
from launch.substitutions import LaunchConfiguration # type: ignore
from launch_ros.actions import Node # type: ignore

def generate_launch_description():

    pkg_desc = get_package_share_directory("robot_description")
    pkg_nav  = get_package_share_directory("robot_navigation")

    default_map = os.path.join(pkg_nav, "maps", "house_map.yaml")

    declare_world         = DeclareLaunchArgument("world",         default_value="house")
    declare_map           = DeclareLaunchArgument("map",           default_value=default_map)
    declare_use_rviz      = DeclareLaunchArgument("use_rviz",      default_value="true")
    declare_params_file   = DeclareLaunchArgument("params_file",   default_value=os.path.join(pkg_nav, "config", "nav2_params.yaml"))
    declare_auto_navigate = DeclareLaunchArgument("auto_navigate", default_value="true",  description="Auto-run waypoint navigator")

    # Gazebo + robot
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_desc, "launch", "robot_gazebo.launch.py")
        ),
        launch_arguments={
            "world":       LaunchConfiguration("world"),
            "use_rviz":    LaunchConfiguration("use_rviz"),
            "rviz_config": os.path.join(pkg_desc, "config", "robot.rviz"),
            "x": "1.0", "y": "1.0", "z": "0.05",
        }.items(),
    )

    # Nav2 - delayed 25s for Gazebo to load AND robot to be spawned
    # robot_gazebo.launch.py delays spawn by 15s; Nav2 needs the odom frame
    # which only appears after DiffDrive activates post-spawn.
    nav2_launch = TimerAction(
        period=25.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_nav, "launch", "navigation_launch.py")
                ),
                launch_arguments={
                    "map":          LaunchConfiguration("map"),
                    "use_sim_time": "true",
                    "params_file":  LaunchConfiguration("params_file"),
                    "autostart":    "true",
                }.items(),
            )
        ],
    )

    # Waypoint navigator - delayed 60s to let Nav2 fully activate
    waypoint_navigator = TimerAction(
        period=60.0,
        actions=[
            Node(
                package="robot_bringup",
                executable="waypoint_navigator.py",
                name="waypoint_navigator",
                output="screen",
                parameters=[
                    {"use_sim_time": True},
                    {"initial_x": 1.0},
                    {"initial_y": 1.0},
                    {"initial_yaw": 0.0},
                ],
                condition=IfCondition(LaunchConfiguration("auto_navigate")),
            )
        ],
    )

    return LaunchDescription([
        declare_world,
        declare_map,
        declare_use_rviz,
        declare_params_file,
        declare_auto_navigate,
        sim_launch,
        nav2_launch,
        waypoint_navigator,
    ])
