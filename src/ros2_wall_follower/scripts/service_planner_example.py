#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from std_msgs.msg import Float32

class ManualServiceNode(Node):
    def __init__(self):
        super().__init__('manual_trigger_services')

        # Clienty do uruchamiania usług
        self.task1_client = self.create_client(Trigger, 'task1')
        self.task2_client = self.create_client(Trigger, 'task2')

        # Flaga, żeby nie wywołać /task2 wielokrotnie
        self.task2_called = False

        # Subskrypcja
        self.subscriber = self.create_subscription(
            Float32,
            '/aruco_average',
            self.aruco_callback,
            10
        )

        # Timer do odczekania aż serwis task1 będzie dostępny
        self.timer = self.create_timer(1.0, self.call_task1_once)

        self.task1_called = False

    def call_task1_once(self):
        if not self.task1_called and self.task1_client.service_is_ready():
            self.task1_called = True
            self.get_logger().info("Calling /task1 service...")
            req = Trigger.Request()
            future = self.task1_client.call_async(req)

            def task1_done(fut):
                if fut.result().success:
                    self.get_logger().info("Successfully called /task1.")
                else:
                    self.get_logger().warn("Failed to call /task1.")

            future.add_done_callback(task1_done)

            self.destroy_timer(self.timer)

    def aruco_callback(self, msg):
        self.get_logger().info(f"Received /aruco_average: {msg.data}")
        if msg.data > 15.0 and not self.task2_called and self.task2_client.service_is_ready():
            self.task2_called = True
            self.get_logger().info("Calling /task2 service because /aruco_average > 15.0")
            req = Trigger.Request()
            future = self.task2_client.call_async(req)

            def task2_done(fut):
                if fut.result().success:
                    self.get_logger().info("Successfully called /task2.")
                else:
                    self.get_logger().warn("Failed to call /task2.")

            future.add_done_callback(task2_done)

    # Serwisowe callbacki
    def task1_callback(self, request, response):
        self.get_logger().info("Service /task1 was called")
        response.success = True
        response.message = "Hello from task1!"
        return response

    def task2_callback(self, request, response):
        self.get_logger().info("Service /task2 was called")
        response.success = True
        response.message = "Hello from task2!"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ManualServiceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
