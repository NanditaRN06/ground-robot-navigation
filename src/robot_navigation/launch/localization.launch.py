import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("robot_navigation")

    default_map = os.path.join(pkg_share, "maps", "map.yaml")
    default_amcl_params = os.path.join(pkg_share, "config", "localization", "amcl.yaml")

    map_file = LaunchConfiguration("map")
    amcl_params = LaunchConfiguration("amcl_params_file")

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"yaml_filename": map_file},
        ],
    )

    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[amcl_params, {"use_sim_time": True}],
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"autostart": True},
            {"node_names": ["map_server", "amcl"]},
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "map",
                default_value=default_map,
                description="Absolute path to saved map YAML file",
            ),
            DeclareLaunchArgument(
                "amcl_params_file",
                default_value=default_amcl_params,
                description="Path to AMCL parameters YAML file",
            ),
            map_server,
            amcl,
            lifecycle_manager,
        ]
    )
