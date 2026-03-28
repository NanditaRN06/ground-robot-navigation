import os
import subprocess
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    # Read directly from source — avoids install path xacro issues
    urdf_path = os.path.expanduser(
        '~/ros2_ws/src/ground-robot-navigation/src/robot_description/urdf/robot.urdf.xacro'
    )

    # Run xacro as a subprocess to get the processed URDF string
    robot_description = subprocess.check_output(
        ['xacro', urdf_path]
    ).decode('utf-8')

    # robot_state_publisher
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': False,
        }]
    )

    # joint_state_publisher_gui
    jsp_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
    )

    # RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
    )

    return LaunchDescription([
        rsp_node,
        jsp_gui_node,
        rviz_node,
    ])
