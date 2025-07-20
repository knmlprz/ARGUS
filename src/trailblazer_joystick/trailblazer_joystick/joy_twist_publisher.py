import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped, Twist


class JoyTwistPublisher(Node):
    def __init__(self):
        super().__init__('joy_twist_publisher')

        # Parameters
        self.declare_parameter('linear_axis', 1)
        self.declare_parameter('angular_axis', 0)
        self.declare_parameter('scale_linear', 1.0)
        self.declare_parameter('scale_angular', 1.0)
        self.declare_parameter('deadzone', 0.1)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value

        # Determine message type
        self.use_stamped = 'diff_drive_controller' in self.cmd_vel_topic
        self.get_logger().info(f"Using {'TwistStamped' if self.use_stamped else 'Twist'} for topic: {self.cmd_vel_topic}")

        # Create appropriate publisher
        if self.use_stamped:
            self.publisher_ = self.create_publisher(TwistStamped, self.cmd_vel_topic, 10)
        else:
            self.publisher_ = self.create_publisher(Twist, self.cmd_vel_topic, 10)

        # Subscriber
        self.subscription = self.create_subscription(
            Joy,
            'joy',
            self.joy_callback,
            10)

        self.get_logger().info('Joy Twist Publisher has been started')

    def joy_callback(self, msg):
        # Get parameters
        linear_axis = self.get_parameter('linear_axis').get_parameter_value().integer_value
        angular_axis = self.get_parameter('angular_axis').get_parameter_value().integer_value
        scale_linear = self.get_parameter('scale_linear').get_parameter_value().double_value
        scale_angular = self.get_parameter('scale_angular').get_parameter_value().double_value
        deadzone = self.get_parameter('deadzone').get_parameter_value().double_value

        # Process axes
        linear = msg.axes[linear_axis]
        if abs(linear) < deadzone:
            linear = 0.0

        angular = msg.axes[angular_axis]
        if abs(angular) < deadzone:
            angular = 0.0

        # Apply scaling
        linear_cmd = linear * scale_linear
        angular_cmd = angular * scale_angular

        # Create and publish appropriate message
        if self.use_stamped:
            twist = TwistStamped()
            twist.header.stamp = self.get_clock().now().to_msg()
            twist.header.frame_id = 'base_link'
            twist.twist.linear.x = linear_cmd
            twist.twist.angular.z = angular_cmd
        else:
            twist = Twist()
            twist.linear.x = linear_cmd
            twist.angular.z = angular_cmd

        self.publisher_.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    joy_twist_publisher = JoyTwistPublisher()
    rclpy.spin(joy_twist_publisher)
    joy_twist_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()