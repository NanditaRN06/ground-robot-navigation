import os
import subprocess
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('robot_description')
    
    urdf_path = os.path.join(pkg_share, 'urdf', 'robot.urdf.xacro')
    robot_description = subprocess.check_output(['xacro', urdf_path]).decode('utf-8')

    world_path = os.path.join(pkg_share, 'worlds', 'mar_world.sdf')

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen',
    )

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-v', '4', '-r', world_path],
        output='screen',
    )

    spawn_robot = TimerAction(period=3.0, actions=[
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-name', 'mar_robot', '-topic', '/robot_description',
                       '-x', '0.0', '-y', '0.0', '-z', '0.15'],
            output='screen',
        )
    ])

    bridge = TimerAction(period=4.0, actions=[
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            ],
            output='screen',
        )
    ])

    return LaunchDescription([rsp_node, gazebo, spawn_robot, bridge])
