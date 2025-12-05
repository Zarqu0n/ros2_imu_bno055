#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('ros2_imu_bno055')
    rviz_config_file = os.path.join(pkg_share, 'utils', 'view_imu_rviz.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='USB port where the IMU is connected'
        ),
        DeclareLaunchArgument(
            'frame_id',
            default_value='imu_link',
            description='Name of the link that the tf will use'
        ),
        DeclareLaunchArgument(
            'operation_mode',
            default_value='IMU',
            description='Type of sensory fusion used by the IMU'
        ),
        DeclareLaunchArgument(
            'reset_orientation',
            default_value='true',
            description='Resets the IMU to reset the orientation'
        ),
        DeclareLaunchArgument(
            'frequency',
            default_value='50',
            description='Frequency of reading the IMU and publication'
        ),
        DeclareLaunchArgument(
            'use_magnetometer',
            default_value='false',
            description='Enables topic imu/magnetometer'
        ),
        DeclareLaunchArgument(
            'use_temperature',
            default_value='false',
            description='Enables topic imu/temperature'
        ),
        # Static transform publisher
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='link1_broadcaster',
            arguments=['0', '0', '0', '0', '0', '0', '1', 'fixed_frame', LaunchConfiguration('frame_id')]
        ),
        # IMU node
        Node(
            package='ros2_imu_bno055',
            executable='imu_node',
            name='ros2_imu_bno055_node',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'frame_id': LaunchConfiguration('frame_id'),
                'operation_mode': LaunchConfiguration('operation_mode'),
                'reset_orientation': LaunchConfiguration('reset_orientation'),
                'frequency': LaunchConfiguration('frequency'),
                'use_magnetometer': LaunchConfiguration('use_magnetometer'),
                'use_temperature': LaunchConfiguration('use_temperature'),
            }]
        ),
        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file]
        ),
    ])
