#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

class ManualServiceNode(Node):
    def __init__(self):
        super().__init__('manual_trigger_services')

        # Tworzymy 10 usług ręcznie
        self.task1_srv = self.create_service(Trigger, 'task1', self.task1_callback)
        self.get_logger().info("Service '/task1' is ready!")

        self.task2_srv = self.create_service(Trigger, 'task2', self.task2_callback)
        self.get_logger().info("Service '/task2' is ready!")

        self.task3_srv = self.create_service(Trigger, 'task3', self.task3_callback)
        self.get_logger().info("Service '/task3' is ready!")

        self.task4_srv = self.create_service(Trigger, 'task4', self.task4_callback)
        self.get_logger().info("Service '/task4' is ready!")

        self.task5_srv = self.create_service(Trigger, 'task5', self.task5_callback)
        self.get_logger().info("Service '/task5' is ready!")

        self.task6_srv = self.create_service(Trigger, 'task6', self.task6_callback)
        self.get_logger().info("Service '/task6' is ready!")

        self.task7_srv = self.create_service(Trigger, 'task7', self.task7_callback)
        self.get_logger().info("Service '/task7' is ready!")

        self.task8_srv = self.create_service(Trigger, 'task8', self.task8_callback)
        self.get_logger().info("Service '/task8' is ready!")

        self.task9_srv = self.create_service(Trigger, 'task9', self.task9_callback)
        self.get_logger().info("Service '/task9' is ready!")

        self.task10_srv = self.create_service(Trigger, 'task10', self.task10_callback)
        self.get_logger().info("Service '/task10' is ready!")

    # Callbacks dla każdej usługi

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

    def task3_callback(self, request, response):
        self.get_logger().info("Service /task3 was called")
        response.success = True
        response.message = "Hello from task3!"
        return response

    def task4_callback(self, request, response):
        self.get_logger().info("Service /task4 was called")
        response.success = True
        response.message = "Hello from task4!"
        return response

    def task5_callback(self, request, response):
        self.get_logger().info("Service /task5 was called")
        response.success = True
        response.message = "Hello from task5!"
        return response

    def task6_callback(self, request, response):
        self.get_logger().info("Service /task6 was called")
        response.success = True
        response.message = "Hello from task6!"
        return response

    def task7_callback(self, request, response):
        self.get_logger().info("Service /task7 was called")
        response.success = True
        response.message = "Hello from task7!"
        return response

    def task8_callback(self, request, response):
        self.get_logger().info("Service /task8 was called")
        response.success = True
        response.message = "Hello from task8!"
        return response

    def task9_callback(self, request, response):
        self.get_logger().info("Service /task9 was called")
        response.success = True
        response.message = "Hello from task9!"
        return response

    def task10_callback(self, request, response):
        self.get_logger().info("Service /task10 was called")
        response.success = True
        response.message = "Hello from task10!"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ManualServiceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
