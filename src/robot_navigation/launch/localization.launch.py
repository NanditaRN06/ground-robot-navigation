from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory('robot_navigation')
    default_map_yaml = os.path.join(
        package_share,
        'maps',
        'replace_with_saved_map.yaml',
    )
    default_amcl_params = os.path.join(
        package_share,
        'config',
        'localization',
        'amcl.yaml',
    )
    default_map_server_params = os.path.join(
        package_share,
        'config',
        'localization',
        'map_server.yaml',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map_yaml_file')
    amcl_params_file = LaunchConfiguration('amcl_params_file')
    map_server_params_file = LaunchConfiguration('map_server_params_file')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time when true.',
        ),
        DeclareLaunchArgument(
            'map_yaml_file',
            default_value=default_map_yaml,
            description='Path to the saved map YAML file.',
        ),
        DeclareLaunchArgument(
            'amcl_params_file',
            default_value=default_amcl_params,
            description='Path to the AMCL parameter file.',
        ),
        DeclareLaunchArgument(
            'map_server_params_file',
            default_value=default_map_server_params,
            description='Path to the map_server parameter file.',
        ),
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[
                map_server_params_file,
                {'use_sim_time': use_sim_time, 'yaml_filename': map_yaml_file},
            ],
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[amcl_params_file, {'use_sim_time': use_sim_time}],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': ['map_server', 'amcl'],
            }],
        ),
    ])
