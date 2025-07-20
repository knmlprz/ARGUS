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
        msg.header.frame_id = "gps"

        try:
            if self.ser.in_waiting > 0:
                # Odczytaj ca?y bufor danych
                raw_data = self.ser.read(self.ser.in_waiting)
                self.get_logger().info(f"Surowy odczyt: {raw_data}")

                # Podziel dane na linie
                lines = raw_data.decode("utf-8").strip().split("\r\n")

                for line in lines:
                    self.get_logger().info(f"Odebrane dane: {line}")

                    # Przetwarzaj tylko komunikaty z pozycj?
                    if line.startswith("$GPGGA") or line.startswith("$GPRMC"):
                        try:
                            parsed = pynmea2.parse(line)
                            if parsed.is_valid:
                                msg.status.status = NavSatStatus.STATUS_FIX
                                msg.latitude = parsed.latitude
                                msg.longitude = parsed.longitude
                                if hasattr(parsed, 'altitude'):  # Dodaj wysoko??, je?li jest dost?pna
                                    msg.altitude = parsed.altitude
                                else:
                                    msg.altitude = 0.0
                                self.get_logger().info(f"Pozycja: {parsed.latitude}, {parsed.longitude}")
                            else:
                                msg.status.status = NavSatStatus.STATUS_NO_FIX
                                self.get_logger().warn("Brak fixa GPS")
                        except pynmea2.ParseError as e:
                            self.get_logger().error(f"B??d parsowania NMEA: {str(e)}")
                            msg.status.status = NavSatStatus.STATUS_NO_FIX
                    else:
                        # Pomijaj komunikaty bez pozycji
                        continue

                # Opublikuj wiadomo??
                self.publisher.publish(msg)

        except UnicodeDecodeError:
            self.get_logger().warn("Nie mo?na zdekodowa? danych")
            msg.status.status = NavSatStatus.STATUS_NO_FIX
        except serial.SerialException as e:
            self.get_logger().error(f"B??d portu szeregowego: {str(e)}")
            msg.status.status = NavSatStatus.STATUS_NO_FIX

def main(args=None):
    rclpy.init(args=args)
    node = GPSPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()