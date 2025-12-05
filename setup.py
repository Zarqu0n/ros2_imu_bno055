from setuptools import setup
import os
from glob import glob

package_name = 'ros2_imu_bno055'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'utils'), glob('utils/*.rviz')),
        (os.path.join('share', package_name, 'utils'), glob('utils/*.rules')),
    ],
    install_requires=['setuptools', 'pyserial'],
    zip_safe=True,
    maintainer='Robert Vasquez Zavaleta',
    maintainer_email='roboticarts1@gmail.com',
    description='ROS2 driver for the BNO055 IMU using serial communication',
    license='BSD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imu_node = ros2_imu_bno055.imu_ros:main',
            'imu_calibration = ros2_imu_bno055.imu_calibration:main',
        ],
    },
)
