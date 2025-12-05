#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='USB port where the IMU is connected'
        ),
        DeclareLaunchArgument(
            'operation_mode',
            default_value='IMU',
            description='Type of sensory fusion used by the IMU'
        ),
        Node(
            package='ros2_imu_bno055',
            executable='imu_calibration',
            name='ros2_imu_bno055_calibration_node',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'operation_mode': LaunchConfiguration('operation_mode'),
            }]
        ),
    ])
