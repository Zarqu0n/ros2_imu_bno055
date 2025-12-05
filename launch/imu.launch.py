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
            'oscillator',
            default_value='INTERNAL',
            description='Use internal or external oscillator'
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
        Node(
            package='ros2_imu_bno055',
            executable='imu_node',
            name='ros2_imu_bno055_node',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'frame_id': LaunchConfiguration('frame_id'),
                'operation_mode': LaunchConfiguration('operation_mode'),
                'oscillator': LaunchConfiguration('oscillator'),
                'reset_orientation': LaunchConfiguration('reset_orientation'),
                'frequency': LaunchConfiguration('frequency'),
                'use_magnetometer': LaunchConfiguration('use_magnetometer'),
                'use_temperature': LaunchConfiguration('use_temperature'),
            }]
        ),
    ])
