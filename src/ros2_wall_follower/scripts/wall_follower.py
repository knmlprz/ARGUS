#! /usr/bin/python3

# imports
# rclpy imports
import rclpy                                              # rclpy
from rclpy.node import Node                               # base node
from rclpy.qos import QoSProfile                          # qos profile
from rclpy.qos import (HistoryPolicy, ReliabilityPolicy,  # qos policies
                      DurabilityPolicy, LivelinessPolicy) # qos policies
from rclpy.executors import MultiThreadedExecutor         # multithreaded executor
from rclpy.callback_groups import ReentrantCallbackGroup  # reentrant callback group
# ros2 interfaces
from geometry_msgs.msg import Twist   # twist message
from nav_msgs.msg import Odometry     # odometry message
from sensor_msgs.msg import LaserScan # laser scan message
from std_srvs.srv import Trigger  # Dodajemy import dla usługi Trigger
# standard imports
import math

# common global variables
# side bias options for wall follow behavior: "none" or "left" or "right"
# this is the side on which the robot will have the wall
# left - sets the robot to follow the wall on its left side
# right - sets the robot to follow the wall on its right side
# none - sets the robot to automatically choose a side
side_choice = "none"
# algorithm choice options for wall follow behavior: "min" or "avg"
# this is the algorithm to decide closeness to the wall
# min - uses minimum scan ranges to detect the wall on its side
# avg - uses average scan ranges to detect the wall on its side
algo_choice = "min"

# define wall follower class as a subclass of node class
class WallFollower(Node):
    # class constructor
    def __init__(self):
        super().__init__("wall_follower")
        self.get_logger().info("Initializing Wall Follower ...")

        # wall detection algorithm choice
        if (algo_choice == "avg"):
            self.ang_vel_mult = 3.000
        else:
            self.ang_vel_mult = 1.250

        # declare and initialize cmd_vel publisher
        self.cmd_vel_pub = self.create_publisher(msg_type=Twist,
                                                 topic="/cmd_vel",
                                                 qos_profile=10)
        self.get_logger().info("Initialized /cmd_vel Publisher")

        # declare and initialize callback group
        self.callback_group = ReentrantCallbackGroup()

        # declare and initialize scan subscriber
        self.scan_sub_qos = QoSProfile(depth=10,
                                       history=HistoryPolicy.KEEP_LAST,
                                       reliability=ReliabilityPolicy.BEST_EFFORT,
                                       durability=DurabilityPolicy.VOLATILE,
                                       liveliness=LivelinessPolicy.AUTOMATIC)
        self.scan_sub = self.create_subscription(msg_type=LaserScan,
                                                 topic="/scan",
                                                 callback=self.scan_callback,
                                                 qos_profile=self.scan_sub_qos,
                                                 callback_group=self.callback_group)
        self.get_logger().info("Initialized /scan Subscriber")

        # declare and initialize odom subscriber
        self.odom_sub_qos = QoSProfile(depth=10,
                                       history=HistoryPolicy.KEEP_LAST,
                                       reliability=ReliabilityPolicy.BEST_EFFORT,
                                       durability=DurabilityPolicy.VOLATILE,
                                       liveliness=LivelinessPolicy.AUTOMATIC)
        self.odom_sub = self.create_subscription(msg_type=Odometry,
                                                 topic="/odom",
                                                 callback=self.odom_callback,
                                                 qos_profile=self.odom_sub_qos,
                                                 callback_group=self.callback_group)
        self.get_logger().info("Initialized /odom Subscriber")

        # declare and initialize control timer callback
        self.control_frequency = 30.0
        self.control_timer = self.create_timer(timer_period_sec=1.0 / self.control_frequency,
                                               callback=self.control_callback,
                                               callback_group=self.callback_group)
        self.get_logger().info("Initialized Control Timer")

        self.get_logger().info("Wall Follower Initialized !")

        # Inicjalizacja usługi do uruchamiania autonomii
        self.srv = self.create_service(Trigger, 'start_autonomy', self.start_autonomy_callback)
        self.get_logger().info("Initialized start_autonomy Service")

        # Inicjalizacja usługi do wylaczania autonomii
        self.srv = self.create_service(Trigger, 'stop_autonomy', self.stop_autonomy_callback)
        self.get_logger().info("Initialized stop_autonomy Service")

        # Flaga kontrolująca autonomię
        self.autonomy_enabled = False

        return None

    # class destructor
    def __del__(self):
        return None

    # define and initialize class variables
    twisting_multiplier = 10
    robot_radius = 1.0                      # 10 cm
    side_threshold_min = robot_radius + 0.05 #  5 cm gap
    side_threshold_max = robot_radius + 0.10 # 10 cm gap
    front_threshold = robot_radius + 0.40    # 40 cm gap
    pi = 3.141592654
    pi_inv = 0.318309886
    ignore_iterations = 5
    iterations_count = 0
    # process variables
    wall_found = False
    side_chosen = "none"
    lin_vel_zero = 0.000
    lin_vel_slow = 0.100
    lin_vel_fast = 0.250
    ang_vel_zero = 0.000
    ang_vel_slow = 0.050
    ang_vel_fast = 0.500
    ang_vel_mult = 0.0
    # velocity publisher variables
    twist_cmd = Twist()
    # scan subscriber variables
    scan_info_done = False
    scan_angle_min = 0.0
    scan_angle_max = 0.0
    scan_angle_inc = 0.0
    scan_range_min = 0.0
    scan_range_max = 0.0
    scan_right_range = 0.0
    scan_front_range = 0.0
    scan_left_range = 0.0
    scan_angle_range = 0
    scan_ranges_size = 0
    scan_right_index = 0
    scan_front_index = 0
    scan_left_index = 0
    scan_sides_angle_range = 15 # degs
    scan_front_angle_range = 15 # degs
    scan_right_range_from_index = 0
    scan_right_range_to_index = 0
    scan_front_range_from_index = 0
    scan_front_range_to_index = 0
    scan_left_range_from_index = 0
    scan_left_range_to_index = 0
    # odom subscriber variables
    odom_info_done = False
    odom_initial_x = 0.0
    odom_initial_y = 0.0
    odom_initial_yaw = 0.0
    odom_curr_x = 0.0
    odom_curr_y = 0.0
    odom_curr_yaw = 0.0
    odom_prev_x = 0.0
    odom_prev_y = 0.0
    odom_prev_yaw = 0.0
    odom_distance = 0.0
    odom_lin_vel = 0.0
    odom_ang_vel = 0.0
    angles = dict()

    def start_autonomy_callback(self, request, response):
        self.autonomy_enabled = True
        self.get_logger().info('Autonomy enabled by operator')
        response.success = True
        response.message = 'Autonomy started'
        return response
    
    def stop_autonomy_callback(self, request, response):
        self.autonomy_enabled = False
        self.get_logger().info('Autonomy disabled by operator')
        response.success = True
        response.message = 'Autonomy stoped'
        return response
    
    # private class methods and callbacks

    def scan_callback(self, scan_msg):
        if (self.scan_info_done):
            # do this step continuously
            if (algo_choice == "avg"):
                # use average ranges if algo_choice is set to "avg"
                # ~~~~~ AVERAGE OF RANGE VALUES METHOD ~~~~~ #
                # initialize local variables to hold sum and count
                # for right, front and left ranges
                scan_right_range_sum = 0.0
                scan_front_range_sum = 0.0
                scan_left_range_sum = 0.0
                scan_right_count = 0
                scan_front_count = 0
                scan_left_count = 0
                # loop through the scan ranges and accumulate the sum of segments
                for index in range(0, self.scan_ranges_size):
                    if (not math.isinf(scan_msg.ranges[index])):
                        if ((index >= self.scan_right_range_from_index) and
                            (index <= self.scan_right_range_to_index)):
                            scan_right_range_sum += scan_msg.ranges[index]
                            scan_right_count += 1
                        if ((index >= self.scan_front_range_from_index) and
                            (index <= self.scan_front_range_to_index)):
                            scan_front_range_sum += scan_msg.ranges[index]
                            scan_front_count += 1
                        if ((index >= self.scan_left_range_from_index) and
                            (index <= self.scan_left_range_to_index)):
                            scan_left_range_sum += scan_msg.ranges[index]
                            scan_left_count += 1
                    else:
                        # otherwise discard the scan range with infinity as value
                        pass
                # calculate the average of each segment
                if (scan_right_count > 0):
                    self.scan_right_range = (scan_right_range_sum / scan_right_count)
                else:
                    self.scan_right_range = self.scan_range_min
                if (scan_front_count > 0):
                    self.scan_front_range = (scan_front_range_sum / scan_front_count)
                else:
                    self.scan_front_range = self.scan_range_min
                if (scan_left_count > 0):
                    self.scan_left_range = (scan_left_range_sum / scan_left_count)
                else:
                    self.scan_left_range = self.scan_range_min
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
            else:
                # otherwise use minimum ranges
                # if algo_choice is set to "min" or anything else
                # ~~~~~ MINIMUM OF RANGE VALUES METHOD ~~~~~ #
                # initialize variables to hold minimum values
                scan_right_range_min = self.scan_range_max
                scan_front_range_min = self.scan_range_max
                scan_left_range_min = self.scan_range_max
                # loop through the scan ranges and get the minimum value
                for index in range(0, self.scan_ranges_size):
                    if (not math.isinf(scan_msg.ranges[index])):
                        if ((index >= self.scan_right_range_from_index) and
                            (index <= self.scan_right_range_to_index)):
                            if (scan_right_range_min > scan_msg.ranges[index]):
                                scan_right_range_min = scan_msg.ranges[index]
                            else:
                                pass
                        if ((index >= self.scan_front_range_from_index) and
                            (index <= self.scan_front_range_to_index)):
                            if (scan_front_range_min > scan_msg.ranges[index]):
                                scan_front_range_min = scan_msg.ranges[index]
                            else:
                                pass
                        if ((index >= self.scan_left_range_from_index) and
                            (index <= self.scan_left_range_to_index)):
                            if (scan_left_range_min > scan_msg.ranges[index]):
                                scan_left_range_min = scan_msg.ranges[index]
                            else:
                                pass
                    else:
                        # otherwise discard the scan range with infinity as value
                        pass
                # set the range values to their minimum values
                if (self.scan_right_range > 0.0):
                    self.scan_right_range = scan_right_range_min
                else:
                    self.scan_right_range = self.scan_range_min
                if (self.scan_front_range > 0.0):
                    self.scan_front_range = scan_front_range_min
                else:
                    self.scan_front_range = self.scan_range_min
                if (self.scan_left_range > 0.0):
                    self.scan_left_range = scan_left_range_min
                else:
                    self.scan_left_range = self.scan_range_min
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
        else:
            # do this step only once
            # get the min and max angles
            self.scan_angle_min = scan_msg.angle_min
            self.scan_angle_max = scan_msg.angle_max
            # get the min and max range values
            self.scan_range_min = scan_msg.range_min
            self.scan_range_max = scan_msg.range_max
            # get the size of the ranges array
            self.scan_ranges_size = len(scan_msg.ranges)
            # get the total scan angle range
            self.scan_angle_range = int((abs(self.scan_angle_min) +
                                         abs(self.scan_angle_max)) *
                                        (180.0 / self.pi))
            # get the angle increments per scan ray
            self.scan_angle_inc = (self.scan_angle_range / self.scan_ranges_size)
            # calculate the front, right and left scan ray indexes
            self.scan_front_index = (self.scan_ranges_size / 2)
            self.scan_right_index = (self.scan_front_index -
                                     int(90.0 / self.scan_angle_inc) - 1)
            self.scan_left_index = (self.scan_front_index +
                                    int(90.0 / self.scan_angle_inc) + 1)
            # calculate the front scan ray ranges
            self.scan_front_range_from_index = (self.scan_front_index -
                                                int(self.scan_front_angle_range /
                                                    self.scan_angle_inc))
            self.scan_front_range_to_index = (self.scan_front_index +
                                              int(self.scan_front_angle_range /
                                                  self.scan_angle_inc))
            # calculate right and left scan ray ranges
            if (self.scan_angle_range > 180):
                self.scan_right_range_from_index = (self.scan_right_index -
                                                    int(self.scan_sides_angle_range /
                                                        self.scan_angle_inc))
                self.scan_right_range_to_index = (self.scan_right_index +
                                                  int(self.scan_sides_angle_range /
                                                      self.scan_angle_inc))
                self.scan_left_range_from_index = (self.scan_left_index -
                                                   int(self.scan_sides_angle_range /
                                                       self.scan_angle_inc))
                self.scan_left_range_to_index = (self.scan_left_index +
                                                 int(self.scan_sides_angle_range /
                                                     self.scan_angle_inc))
            else:
                self.scan_right_range_from_index = self.scan_right_index
                self.scan_right_range_to_index = (self.scan_right_index +
                                                  int(self.scan_sides_angle_range /
                                                      self.scan_angle_inc))
                self.scan_left_range_from_index = (self.scan_left_index -
                                                   int(self.scan_sides_angle_range /
                                                       self.scan_angle_inc))
                self.scan_left_range_to_index = self.scan_left_index
            # set flag to true so this step will not be done again
            self.scan_info_done = True
            # print scan details
            self.get_logger().info("~~~~~ Start Scan Info ~~~~")
            self.get_logger().info("scan_angle_min: %+0.3f" % (self.scan_angle_min))
            self.get_logger().info("scan_angle_max: %+0.3f" % (self.scan_angle_max))
            self.get_logger().info("scan_range_min: %+0.3f" % (self.scan_range_min))
            self.get_logger().info("scan_range_max: %+0.3f" % (self.scan_range_max))
            self.get_logger().info("scan_angle_range: %d" % (self.scan_angle_range))
            self.get_logger().info("scan_ranges_size: %d" % (self.scan_ranges_size))
            self.get_logger().info("scan_angle_inc: %+0.3f" % (self.scan_angle_inc))
            self.get_logger().info("scan_right_index: %d" % (self.scan_right_index))
            self.get_logger().info("scan_front_index: %d" % (self.scan_front_index))
            self.get_logger().info("scan_left_index: %d" % (self.scan_left_index))
            self.get_logger().info("scan_right_range_index:")
            self.get_logger().info("from: %d ~~~> to: %d" %
                                   (self.scan_right_range_from_index,
                                    self.scan_right_range_to_index))
            self.get_logger().info("scan_front_range_index:")
            self.get_logger().info("from: %d ~~~> to: %d" %
                                   (self.scan_front_range_from_index,
                                    self.scan_front_range_to_index))
            self.get_logger().info("scan_left_range_index:")
            self.get_logger().info("from: %d ~~~> to: %d" %
                                   (self.scan_left_range_from_index,
                                    self.scan_left_range_to_index))
            self.get_logger().info("~~~~~ End Scan Info ~~~~")
        return None

    def odom_callback(self, odom_msg):
        if (self.odom_info_done):
            # do this step continuously
            # get current odometry values
            self.odom_curr_x = odom_msg.pose.pose.position.x
            self.odom_curr_y = odom_msg.pose.pose.position.y
            angles = self.euler_from_quaternion(odom_msg.pose.pose.orientation.x,
                                                odom_msg.pose.pose.orientation.y,
                                                odom_msg.pose.pose.orientation.z,
                                                odom_msg.pose.pose.orientation.w)
            self.odom_curr_yaw = angles["yaw_deg"]
            # calculate distance based on current and previous odometry values
            self.odom_distance += self.calculate_distance(self.odom_prev_x,
                                                          self.odom_prev_y,
                                                          self.odom_curr_x,
                                                          self.odom_curr_y)
            # set previous odometry values to current odometry values
            self.odom_prev_x = self.odom_curr_x
            self.odom_prev_y = self.odom_curr_y
            self.odom_prev_yaw = self.odom_curr_yaw
        else:
            # do this step only once
            # get initial odometry values
            self.odom_initial_x = odom_msg.pose.pose.position.x
            self.odom_initial_y = odom_msg.pose.pose.position.y
            angles = self.euler_from_quaternion(odom_msg.pose.pose.orientation.x,
                                                odom_msg.pose.pose.orientation.y,
                                                odom_msg.pose.pose.orientation.z,
                                                odom_msg.pose.pose.orientation.w)
            self.odom_initial_yaw = angles["yaw_deg"]
            # set previous odometry values to initial odometry values
            self.odom_prev_x = self.odom_initial_x
            self.odom_prev_y = self.odom_initial_y
            self.odom_prev_yaw = self.odom_initial_yaw
            # set flag to true so this step will not be done again
            self.odom_info_done = True
            # print odom details
            self.get_logger().info("~~~~~ Start Odom Info ~~~~")
            self.get_logger().info("odom_initial_x: %+0.3f" % (self.odom_initial_x))
            self.get_logger().info("odom_initial_y: %+0.3f" % (self.odom_initial_y))
            self.get_logger().info("odom_initial_yaw: %+0.3f" % (self.odom_initial_yaw))
            self.get_logger().info("~~~~~ End Odom Info ~~~~")
        return None

    # def control_callback(self):
    #     if (self.iterations_count >= self.ignore_iterations):
    #         # Ustawienie prędkości liniowej na stałą wartość
    #         self.twist_cmd.linear.x = self.lin_vel_fast
            
    #         # Obliczenie prędkości kątowej na podstawie odległości do przeszkód
    #         if (self.scan_left_range > self.side_threshold_max and
    #             self.scan_right_range > self.side_threshold_max):
    #             # Jeśli obie strony są daleko, nie skręcaj
    #             self.twist_cmd.angular.z = self.ang_vel_zero
    #         else:
    #             # Obliczenie błędu
    #             error = 1 / self.scan_left_range - 1 / self.scan_right_range
    #             # Normalizacja błędu do zakresu od -1 do 1
    #             max_error = 1 / self.scan_range_min - 1 / self.scan_range_max
    #             normalized_error = error / max_error if max_error != 0 else 0
    #             # Skalowanie do zakresu od 0 do 1
    #             scaled_error = (normalized_error + 1) / 2
    #             # Obliczenie prędkości kątowej z zachowaniem znaku
    #             self.twist_cmd.angular.z = -self.ang_vel_fast * scaled_error * (1 if error > 0 else -1)
    #     else:
    #         self.iterations_count += 1
    #         self.twist_cmd.linear.x = self.lin_vel_zero
    #         self.twist_cmd.angular.z = self.ang_vel_zero
    #     # Opublikuj komendę twist
    #     self.publish_twist_cmd()
    #     # Wydrukuj informacje o bieżącej iteracji
    #     self.print_info()
    #     return None

    def control_callback(self):
        if self.autonomy_enabled == True and self.iterations_count >= self.ignore_iterations:
            # Ustaw stałą prędkość jazdy do przodu
            self.twist_cmd.linear.x = self.lin_vel_fast

            if (self.scan_left_range > self.side_threshold_max and
                self.scan_right_range > self.side_threshold_max):
                # Jeśli obie strony są daleko, nie skręcaj
                self.twist_cmd.angular.z = self.ang_vel_zero
            else:
                # Oblicz różnicę średnich odległości
                error = self.scan_right_range - self.scan_left_range

                # Normalizacja względem maksymalnego możliwego zakresu
                max_error = self.scan_range_max - self.scan_range_min
                normalized_error = error / max_error if max_error != 0 else 0.0
                
                print("error",error,"max_error",max_error,"self.scan_range_max",self.scan_range_max,"self.scan_range_min",self.scan_range_min,"normalized_error",normalized_error)

                # Skalowanie prędkości kątowej (ujemna = skręt w lewo, dodatnia = skręt w prawo)
                self.twist_cmd.angular.z = -self.ang_vel_fast * normalized_error * self.twisting_multiplier
                self.twist_cmd.angular.z = max(min(self.twist_cmd.angular.z, 0.3), -0.3)

        else:
            self.iterations_count += 1
            self.twist_cmd.linear.x = self.lin_vel_zero
            self.twist_cmd.angular.z = self.ang_vel_zero

        # Publikuj komendę twist
        self.publish_twist_cmd()

        # Debug/info
        self.print_info()

        return None
    
    def publish_twist_cmd(self):
        # linear speed control
        if (self.twist_cmd.linear.x >= 0.450):
          self.twist_cmd.linear.x = 0.450
        else:
          # do nothing
          pass
        # angular speed control
        if (self.twist_cmd.angular.z >= 0.450):
          self.twist_cmd.angular.z = 0.450
        else:
          # do nothing
          pass
        # publish command
        self.cmd_vel_pub.publish(self.twist_cmd)
        return None

    def print_info(self):
        self.get_logger().info("Scan: L: %0.3f F: %0.3f R: %0.3f" %
                               (self.scan_left_range, self.scan_front_range,
                                self.scan_right_range))
        self.get_logger().info("Odom: X: %+0.3f Y: %+0.3f" %
                               (self.odom_curr_x, self.odom_curr_y))
        self.get_logger().info("Odom: Yaw: %+0.3f Dist: %0.3f" %
                               (self.odom_curr_yaw, self.odom_distance))
        self.get_logger().info("Vel: Lin: %+0.3f Ang: %+0.3f" %
                               (self.twist_cmd.linear.x, self.twist_cmd.angular.z))
        self.get_logger().info("~~~~~~~~~~")
        return None

    def calculate_distance(self, prev_x, prev_y, curr_x, curr_y):
        # function to calculate euclidean distance in 2d plane

        #calculate distance
        distance = ((((curr_x - prev_x) ** 2.0) +
                     ((curr_y - prev_y) ** 2.0)) ** 0.50)

        #return the distance value
        return distance

    def euler_from_quaternion(self, quat_x, quat_y, quat_z, quat_w):
        # function to convert quaternions to euler angles

        # calculate roll
        sinr_cosp = 2 * (quat_w * quat_x + quat_y * quat_z)
        cosr_cosp = 1 - 2 * (quat_x * quat_x + quat_y * quat_y)
        roll_rad = math.atan2(sinr_cosp, cosr_cosp)
        roll_deg = (roll_rad * 180 * self.pi_inv)

        # calculate pitch
        sinp = 2 * (quat_w * quat_y - quat_z * quat_x)
        pitch_rad = math.asin(sinp)
        pitch_deg = (pitch_rad * 180 * self.pi_inv)

        # calculate yaw
        siny_cosp = 2 * (quat_w * quat_z + quat_x * quat_y)
        cosy_cosp = 1 - 2 * (quat_y * quat_y + quat_z * quat_z)
        yaw_rad = math.atan2(siny_cosp, cosy_cosp)
        yaw_deg = (yaw_rad * 180 * self.pi_inv)

        # store the angle values in a dict
        angles = dict()
        angles["roll_rad"] = roll_rad
        angles["roll_deg"] = roll_deg
        angles["pitch_rad"] = pitch_rad
        angles["pitch_deg"] = pitch_deg
        angles["yaw_rad"] = yaw_rad
        angles["yaw_deg"] = yaw_deg

        # return the angle values
        return angles


def main(args=None):

    # initialize ROS2 node
    rclpy.init(args=args)

    # create an instance of the wall follower class
    wall_follower = WallFollower()
    
    # create a multithreaded executor
    executor = MultiThreadedExecutor(num_threads=4)
    
    # add the wall follower node to the executor
    executor.add_node(wall_follower)

    try:
        # spin the executor to handle callbacks
        executor.spin()
    except:
        pass
    finally:
        # indicate wall follower node termination
        wall_follower.get_logger().info("Terminating Wall Follower ...")
        # stop the robot
        wall_follower.twist_cmd.linear.x = wall_follower.lin_vel_zero
        wall_follower.twist_cmd.angular.z = wall_follower.ang_vel_zero
        # publish the twist command
        wall_follower.publish_twist_cmd()
        wall_follower.get_logger().info("Wall Follower Terminated !")
    
    # shutdown the executor when spin completes
    executor.shutdown()
    
    # destroy the wall follower node
    wall_follower.destroy_node()

    # shutdown ROS2 node when spin completes
    rclpy.shutdown()

    return None


if __name__ == "__main__":
    main()

# End of Code
