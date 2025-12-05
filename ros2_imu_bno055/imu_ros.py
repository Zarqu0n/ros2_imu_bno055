#!/usr/bin/env python3

"""
Copyright (c) 2020 Robotic Arts Industries

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

   * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

   * Neither the name of the copyright holder nor the names of its
     contributors may be used to endorse or promote products derived from
     this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

"""

"""

Author:  Robert Vasquez Zavaleta

"""

import rclpy
from rclpy.node import Node
import os
import time
from ros2_imu_bno055.imu_bno055_api import *
from sensor_msgs.msg import Imu
from sensor_msgs.msg import Temperature
from sensor_msgs.msg import MagneticField
from std_srvs.srv import Empty
from std_srvs.srv import Trigger


class SensorIMU(Node):

    def __init__(self):
        super().__init__('ros2_imu_bno055_node')

        # Get ros params
        self.get_ros_params()

        # Create an IMU instance
        self.bno055 = BoschIMU(port=self.serial_port)

        # Internal variables
        self.stop_request = False

        # Create topics
        self.pub_imu_data = self.create_publisher(Imu, 'imu/data', 10)

        if self.use_magnetometer:
            self.pub_imu_magnetometer = self.create_publisher(MagneticField, 'imu/magnetometer', 10)

        if self.use_temperature:
            self.pub_imu_temperature = self.create_publisher(Temperature, 'imu/temperature', 10)

        # Create services
        self.reset_imu_device = self.create_service(Empty, 'imu/reset_device', self.callback_reset_imu_device)
        self.calibration_imu_status = self.create_service(Trigger, 'imu/calibration_status', self.callback_calibration_imu_status)

        # Print node status
        self.get_logger().info("ros2_imu_bno055_node ready!")

    def get_ros_params(self):
        # Declare and get parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('frame_id', 'imu_link')
        self.declare_parameter('operation_mode', 'IMU')
        self.declare_parameter('oscillator', 'INTERNAL')
        self.declare_parameter('reset_orientation', True)
        self.declare_parameter('frequency', 20)
        self.declare_parameter('use_magnetometer', False)
        self.declare_parameter('use_temperature', False)

        self.serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self.operation_mode_str = self.get_parameter('operation_mode').get_parameter_value().string_value
        self.oscillator_str = self.get_parameter('oscillator').get_parameter_value().string_value
        self.reset_orientation = self.get_parameter('reset_orientation').get_parameter_value().bool_value
        self.frequency = self.get_parameter('frequency').get_parameter_value().integer_value
        self.use_magnetometer = self.get_parameter('use_magnetometer').get_parameter_value().bool_value
        self.use_temperature = self.get_parameter('use_temperature').get_parameter_value().bool_value

        switcher = {
            'IMU': IMU,
            'COMPASS': COMPASS,
            'M4G': M4G,
            'NDOF_FMC_OFF': NDOF_FMC_OFF,
            'NDOF': NDOF,
        }

        self.operation_mode = switcher.get(self.operation_mode_str, IMU)

        switcher = {
            'EXTERNAL': EXTERNAL_OSCILLATOR,
            'INTERNAL': INTERNAL_OSCILLATOR
        }

        self.oscillator = switcher.get(self.oscillator_str, INTERNAL_OSCILLATOR)

    def set_imu_configuration(self):
        # IMU configuration: required every time the IMU is turned on or reset

        # Enable IMU configuration
        status_1 = self.bno055.enable_imu_configuration()

        if status_1 == RESPONSE_OK:
            self.get_logger().info("Configuration mode activated")
        else:
            self.get_logger().error("Unable to activate configuration mode")

        # Set IMU units
        status_2 = self.bno055.set_imu_units(
            acceleration_units=METERS_PER_SECOND,
            angular_velocity_units=RAD_PER_SECOND,
            euler_orientation_units=RAD,
            temperature_units=CELSIUS,
            orientation_mode=WINDOWS_ORIENTATION
        )

        if status_2 == RESPONSE_OK:
            self.get_logger().info("Units configured successfully")
        else:
            self.get_logger().warn("Unable to configure units")

        # Set imu axis
        status_3 = self.bno055.set_imu_axis(axis_placement=P1)

        if status_3 == RESPONSE_OK:
            self.get_logger().info("Axis configured successfully")
        else:
            self.get_logger().warn("Unable to configure axis")

        status_calibration = self.load_calibration_from_file()

        if status_calibration == RESPONSE_OK:
            self.get_logger().info("Calibration loaded successfully")
        else:
            self.get_logger().info("Calibration not detected. IMU will use default calibration")

        status_oscillator = self.bno055.set_oscillator(oscillator_type=self.oscillator)

        if status_oscillator == RESPONSE_OK:
            self.get_logger().info(f"{self.oscillator_str} oscillator configured successfully")
        else:
            self.get_logger().info("Unable to configure oscillator")

        # Set operation mode. Exit configuration mode and activate IMU to work
        status_4 = self.bno055.set_imu_operation_mode(operation_mode=self.operation_mode)

        if status_4 == RESPONSE_OK:
            self.get_logger().info("Operation mode configured successfully")
        else:
            self.get_logger().error("Unable to configure operation mode")

        # Check all status
        if (status_1 == RESPONSE_OK and status_2 == RESPONSE_OK
                and status_3 == RESPONSE_OK and status_4 == RESPONSE_OK):
            self.get_logger().info(f"IMU is working now in {self.operation_mode_str} mode!")
        else:
            self.get_logger().warn("The IMU was not configured correctly. It may not work")

    def reset_imu(self):
        status = self.bno055.reset_imu()

        if status == RESPONSE_OK:
            self.get_logger().info("IMU successfully reset")
        else:
            self.get_logger().warn("Reset IMU failed")

    def load_calibration_from_file(self):
        status = -1
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # Read calibration from file
        try:
            binary_file = open(str(dir_path) + "/" + self.operation_mode_str + "_calibration", "rb")
            calibration_data = binary_file.read()
            binary_file.close()
            calibration_exists = True
        except Exception:
            calibration_data = 0
            calibration_exists = False

        # Load calibration into the IMU
        if calibration_exists:
            status = self.bno055.set_calibration(calibration_data)
        else:
            status = RESPONSE_ERROR

        return status

    def callback_reset_imu_device(self, request, response):
        self.get_logger().info("====================")
        self.get_logger().info("Service: Reseting IMU...")
        self.stop_request = True
        time.sleep(1)
        self.reset_imu()
        self.set_imu_configuration()
        self.stop_request = False
        self.get_logger().info("Service: IMU reset completed!")
        return response

    def callback_calibration_imu_status(self, request, response):
        self.stop_request = True
        # Delay proportional to the frequency of the node
        time.sleep(1 / self.frequency)
        calibration_status, status = self.bno055.get_calibration_status()
        self.stop_request = False

        if status == RESPONSE_OK:
            sys_str = " [System: " + str(calibration_status[0]) + "]"
            gyr = " [Gyroscope: " + str(calibration_status[1]) + "]"
            acc = " [Accelerometer: " + str(calibration_status[2]) + "]"
            mag = " [Magnetometer: " + str(calibration_status[3]) + "]"

            response.message = sys_str + gyr + acc + mag
            response.success = True
        else:
            self.get_logger().warn("Unable to read IMU calibration")
            response.message = "Unable to read IMU calibration"
            response.success = False

        return response

    def publish_imu_data(self):
        imu_data = Imu()

        quaternion = self.bno055.get_quaternion_orientation()
        linear_acceleration = self.bno055.get_linear_acceleration()
        gyroscope = self.bno055.get_gyroscope()

        imu_data.header.stamp = self.get_clock().now().to_msg()
        imu_data.header.frame_id = self.frame_id

        imu_data.orientation.w = float(quaternion[0])
        imu_data.orientation.x = float(quaternion[1])
        imu_data.orientation.y = float(quaternion[2])
        imu_data.orientation.z = float(quaternion[3])

        imu_data.linear_acceleration.x = float(linear_acceleration[0])
        imu_data.linear_acceleration.y = float(linear_acceleration[1])
        imu_data.linear_acceleration.z = float(linear_acceleration[2])

        imu_data.angular_velocity.x = float(gyroscope[0])
        imu_data.angular_velocity.y = float(gyroscope[1])
        imu_data.angular_velocity.z = float(gyroscope[2])

        imu_data.orientation_covariance[0] = -1.0
        imu_data.linear_acceleration_covariance[0] = -1.0
        imu_data.angular_velocity_covariance[0] = -1.0

        self.pub_imu_data.publish(imu_data)

    def publish_imu_magnetometer(self):
        imu_magnetometer = MagneticField()

        magnetometer = self.bno055.get_magnetometer()

        imu_magnetometer.header.stamp = self.get_clock().now().to_msg()
        imu_magnetometer.header.frame_id = self.frame_id

        imu_magnetometer.magnetic_field.x = float(magnetometer[0])
        imu_magnetometer.magnetic_field.y = float(magnetometer[1])
        imu_magnetometer.magnetic_field.z = float(magnetometer[2])

        self.pub_imu_magnetometer.publish(imu_magnetometer)

    def publish_imu_temperature(self):
        imu_temperature = Temperature()

        temperature = self.bno055.get_temperature()

        imu_temperature.header.stamp = self.get_clock().now().to_msg()
        imu_temperature.header.frame_id = self.frame_id

        imu_temperature.temperature = float(temperature)

        self.pub_imu_temperature.publish(imu_temperature)

    def run(self):
        # Reset IMU to reset axis orientation.
        if self.reset_orientation:
            self.reset_imu()

        # Configuration is necessary every time the IMU is turned on or reset
        self.set_imu_configuration()

        # Create timer for periodic publishing
        timer_period = 1.0 / self.frequency
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        if not self.stop_request:
            self.bno055.update_imu_data()

            # Publish imu data
            self.publish_imu_data()

            # Publish magnetometer data
            if self.use_magnetometer:
                self.publish_imu_magnetometer()

            # Publish temperature data
            if self.use_temperature:
                self.publish_imu_temperature()


def main(args=None):
    rclpy.init(args=args)

    imu = SensorIMU()

    try:
        imu.run()
        rclpy.spin(imu)
    except KeyboardInterrupt:
        pass
    finally:
        imu.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

