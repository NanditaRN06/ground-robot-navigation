#!/usr/bin/env python3
"""
SLAM Launch — mirrors the official slam_toolbox online_async_launch.py.

Root cause of 'Subscription count: 0': async_slam_toolbox_node is a
LifecycleNode. Using plain Node() leaves it in Unconfigured state so it
never subscribes to /scan. This file uses LifecycleNode + configure/activate
events, exactly as slam_toolbox's own online_async_launch.py does.
"""

import os
from ament_index_python.packages import get_package_share_directory  # type: ignore
from launch import LaunchDescription  # type: ignore
from launch.actions import DeclareLaunchArgument, EmitEvent, LogInfo, RegisterEventHandler  # type: ignore
from launch.conditions import IfCondition  # type: ignore
from launch.events import matches_action  # type: ignore
from launch.substitutions import AndSubstitution, LaunchConfiguration, NotSubstitution  # type: ignore
from launch_ros.actions import LifecycleNode  # type: ignore
from launch_ros.event_handlers import OnStateTransition  # type: ignore
from launch_ros.events.lifecycle import ChangeState  # type: ignore
from lifecycle_msgs.msg import Transition  # type: ignore


def generate_launch_description():
    pkg_nav = get_package_share_directory("robot_navigation")

    autostart             = LaunchConfiguration("autostart")
    use_lifecycle_manager = LaunchConfiguration("use_lifecycle_manager")
    use_sim_time          = LaunchConfiguration("use_sim_time")
    slam_params_file      = LaunchConfiguration("slam_params_file")

    declare_autostart = DeclareLaunchArgument(
        "autostart", default_value="true",
        description="Auto configure+activate slam_toolbox lifecycle node")
    declare_use_lifecycle_manager = DeclareLaunchArgument(
        "use_lifecycle_manager", default_value="false",
        description="Use external lifecycle manager (nav2_lifecycle_manager)")
    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time", default_value="true",
        description="Use Gazebo sim clock")
    declare_slam_params = DeclareLaunchArgument(
        "slam_params_file",
        default_value=os.path.join(pkg_nav, "config", "slam_toolbox_params.yaml"),
        description="Path to slam_toolbox params YAML")

    # LifecycleNode
    slam_node = LifecycleNode(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        namespace="",
        output="screen",
        parameters=[
            slam_params_file,
            {
                "use_lifecycle_manager": use_lifecycle_manager,
                "use_sim_time": use_sim_time,
            },
        ],
    )

    # Lifecycle: fire CONFIGURE immediately on autostart
    configure_event = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=matches_action(slam_node),
            transition_id=Transition.TRANSITION_CONFIGURE,
        ),
        condition=IfCondition(
            AndSubstitution(autostart, NotSubstitution(use_lifecycle_manager))
        ),
    )

    # Lifecycle: ACTIVATE once CONFIGURE completes
    activate_event = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=slam_node,
            start_state="configuring",
            goal_state="inactive",
            entities=[
                LogInfo(msg="\033[92m[LifecycleLaunch] slam_toolbox configured → activating\033[0m"),
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(slam_node),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                ),
            ],
        ),
        condition=IfCondition(
            AndSubstitution(autostart, NotSubstitution(use_lifecycle_manager))
        ),
    )

    return LaunchDescription([
        declare_autostart,
        declare_use_lifecycle_manager,
        declare_use_sim_time,
        declare_slam_params,
        slam_node,
        configure_event,
        activate_event,
    ])
