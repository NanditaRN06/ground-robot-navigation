from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.actions import DeclareLaunchArgument
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    map_file = LaunchConfiguration("map")

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("robot_navigation"), "launch", "localization.launch.py"]
            )
        ),
        launch_arguments={"map": map_file}.items(),
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("robot_navigation"), "launch", "navigation.launch.py"]
            )
        )
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "map",
                description="Absolute path to saved map yaml",
            ),
            localization_launch,
            navigation_launch,
        ]
    )
