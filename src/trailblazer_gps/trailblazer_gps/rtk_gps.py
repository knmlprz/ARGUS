import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
import serial
import pynmea2


class GPSPublisher(Node):
    def __init__(self):
        super().__init__('gps_publisher')
        self.publisher = self.create_publisher(NavSatFix, '/gps/fix', 10)
        self.port = self.declare_parameter("port", "/dev/ttyUSB1").get_parameter_value().string_value
        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            timeout=1.0,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        self.timer = self.create_timer(1.0, self.publish_data)

    def publish_data(self):
        msg = NavSatFix()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.status.status = NavSatStatus.STATUS_NO_FIX  # Default to no fix

        try:
            if self.ser.in_waiting > 0:
                raw_data = self.ser.read(self.ser.in_waiting).decode("utf-8", errors='replace')
                lines = [line.strip() for line in raw_data.split('\n') if line.strip()]

                for line in lines:
                    self.get_logger().debug(f"Raw line: {line}")

                    try:
                        # Process GNGGA message (primary position source)
                        if line.startswith('$GNGGA'):
                            parsed = pynmea2.parse(line)
                            if parsed.is_valid:
                                msg.status.status = NavSatStatus.STATUS_FIX
                                msg.latitude = parsed.latitude
                                msg.longitude = parsed.longitude
                                msg.altitude = parsed.altitude if hasattr(parsed, 'altitude') else 0.0
                                self.get_logger().info(f"GGA Position: Lat: {parsed.latitude}, Lon: {parsed.longitude}, Alt: {msg.altitude}")

                        # Process GNRMC message (secondary position source and velocity)
                        elif line.startswith('$GNRMC'):
                            parsed = pynmea2.parse(line)
                            if parsed.is_valid and parsed.status == 'A':
                                # Only update if we don't have a fix yet from GGA
                                if msg.status.status != NavSatStatus.STATUS_FIX:
                                    msg.status.status = NavSatStatus.STATUS_FIX
                                    msg.latitude = parsed.latitude
                                    msg.longitude = parsed.longitude
                                    self.get_logger().info(f"RMC Position: Lat: {parsed.latitude}, Lon: {parsed.longitude}")

                                # You could also extract speed and course from RMC if needed
                                # msg.speed = parsed.spd_over_grnd
                                # msg.course = parsed.true_course

                    except pynmea2.ParseError as e:
                        self.get_logger().warn(f"Parse error for line '{line}': {str(e)}")
                        continue

                # Only publish if we have a valid fix
                if msg.status.status == NavSatStatus.STATUS_FIX:
                    self.publisher.publish(msg)
                else:
                    self.get_logger().warn("No valid GPS fix available")

        except UnicodeDecodeError as e:
            self.get_logger().warn(f"Unicode decode error: {str(e)}")
        except serial.SerialException as e:
            self.get_logger().error(f"Serial port error: {str(e)}")
        except Exception as e:
            self.get_logger().error(f"Unexpected error: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = GPSPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.ser.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()