import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("robot_navigation")
    default_nav2_params = os.path.join(pkg_share, "config", "nav2", "nav2_params.yaml")
    default_global_costmap = os.path.join(pkg_share, "config", "costmaps", "global_costmap.yaml")
    default_local_costmap = os.path.join(pkg_share, "config", "costmaps", "local_costmap.yaml")

    nav2_params_file = LaunchConfiguration("nav2_params_file")
    global_costmap_file = LaunchConfiguration("global_costmap_file")
    local_costmap_file = LaunchConfiguration("local_costmap_file")

    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        parameters=[nav2_params_file, global_costmap_file, {"use_sim_time": True}],
    )

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        output="screen",
        parameters=[nav2_params_file, local_costmap_file, {"use_sim_time": True}],
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        output="screen",
        parameters=[nav2_params_file, {"use_sim_time": True}],
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        output="screen",
        parameters=[nav2_params_file, {"use_sim_time": True}],
    )

    smoother_server = Node(
        package="nav2_smoother",
        executable="smoother_server",
        name="smoother_server",
        output="screen",
        parameters=[nav2_params_file, {"use_sim_time": True}],
    )

    waypoint_follower = Node(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        output="screen",
        parameters=[nav2_params_file, {"use_sim_time": True}],
    )

    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        name="velocity_smoother",
        output="screen",
        parameters=[nav2_params_file, {"use_sim_time": True}],
        remappings=[("cmd_vel", "cmd_vel_nav"), ("cmd_vel_smoothed", "cmd_vel")],
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"autostart": True},
            {
                "node_names": [
                    "planner_server",
                    "controller_server",
                    "smoother_server",
                    "behavior_server",
                    "bt_navigator",
                    "waypoint_follower",
                    "velocity_smoother",
                ]
            },
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "nav2_params_file",
                default_value=default_nav2_params,
                description="Path to Nav2 parameters YAML",
            ),
            DeclareLaunchArgument(
                "global_costmap_file",
                default_value=default_global_costmap,
                description="Path to global costmap YAML",
            ),
            DeclareLaunchArgument(
                "local_costmap_file",
                default_value=default_local_costmap,
                description="Path to local costmap YAML",
            ),
            planner_server,
            controller_server,
            smoother_server,
            behavior_server,
            bt_navigator,
            waypoint_follower,
            velocity_smoother,
            lifecycle_manager,
        ]
    )
