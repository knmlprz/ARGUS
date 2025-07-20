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
        self.control_timer = self.create_timer(timer_period_sec=0.500,
                                               callback=self.control_callback,
                                               callback_group=self.callback_group)
        self.get_logger().info("Initialized Control Timer")

        self.get_logger().info("Wall Follower Initialized !")

        return None

    # class destructor
    def __del__(self):
        return None

    # define and initialize class variables
    robot_radius = 0.10                      # 10 cm
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

    def control_callback(self):
        if (self.iterations_count >= self.ignore_iterations):
            # fix for delayed laser scanner startup
            if (self.wall_found):
                # now the robot is either facing the wall after finding the wall
                # or running the wall follower process and facing a wall or obstacle
                if (self.scan_front_range < self.front_threshold):
                    # turn towards the side opposite to the wall while moving forward
                    self.twist_cmd.linear.x = self.lin_vel_slow
                    if (self.side_chosen == "right"):
                        # turn the robot to the left
                        self.twist_cmd.angular.z = (self.ang_vel_fast * self.ang_vel_mult)
                    elif (self.side_chosen == "left"):
                        # turn the robot to the right
                        self.twist_cmd.angular.z = (-self.ang_vel_fast * self.ang_vel_mult)
                    else:
                        # otherwise do nothing
                        # this choice will never happen
                        pass
                else:
                    # otherwise keep going straight
                    # until either onstacle or wall is detected
                    self.twist_cmd.linear.x = self.lin_vel_fast
                    # check the closeness to the wall
                    if (self.side_chosen == "right"):
                        # wall is on the right
                        if (self.scan_right_range < self.side_threshold_min):
                            # turn left to move away from the wall
                            self.twist_cmd.angular.z = self.ang_vel_slow
                        elif (self.scan_right_range > self.side_threshold_max):
                            # turn right to move close to the wall
                            self.twist_cmd.angular.z = -self.ang_vel_slow
                        else:
                            # do not turn and keep going straight
                            self.twist_cmd.angular.z = self.ang_vel_zero
                    elif (self.side_chosen == "left"):
                        # wall is on the left
                        if (self.scan_left_range < self.side_threshold_min):
                            # turn right to move away from the wall
                            self.twist_cmd.angular.z = -self.ang_vel_slow
                        elif (self.scan_left_range > self.side_threshold_max):
                            # turn left to move close to the wall
                            self.twist_cmd.angular.z = self.ang_vel_slow
                        else:
                            # do not turn and keep going straight
                            self.twist_cmd.angular.z = self.ang_vel_zero
                    else:
                        # otherwise do nothing
                        # this choice will never happen
                        pass
            else:
                # find the wall closest to the robot
                # keep moving forward until the robot detects
                # an obstacle or wall in its front
                if (self.scan_front_range < self.front_threshold):
                    # immediately set the wall_found flag to true
                    # to break out of this subprocess
                    self.wall_found = True
                    self.get_logger().info("Wall Found!")
                    # stop the robot
                    self.twist_cmd.linear.x = self.lin_vel_zero
                    self.twist_cmd.angular.z = self.ang_vel_zero
                    self.get_logger().info("Robot Stopped!")
                    # choose a side to turn if side_choice is set to none
                    if ((side_choice != "right") and
                        (side_choice != "left")):
                        # choose the side that has closer range value
                        # closer range value indicates that the wall is on that side
                        if (self.scan_right_range < self.scan_left_range):
                            # wall is on the right
                            self.side_chosen = "right"
                        elif (self.scan_right_range > self.scan_left_range):
                            # wall is on the left
                            self.side_chosen = "left"
                        else:
                            # otherwise do nothing
                            # this choice will never happen
                            pass
                        self.get_logger().info("Side Chosen: %s" % (self.side_chosen))
                    else:
                        # otherwise do nothing
                        # side is already set by the user
                        pass
                else:
                    # otherwise keep going straight slowly
                    # until either onstacle or wall is detected
                    self.twist_cmd.linear.x = self.lin_vel_slow
                    self.twist_cmd.angular.z = self.ang_vel_zero
        else:
            # just increment the iterations count
            self.iterations_count += 1
            # keep the robot stopped
            self.twist_cmd.linear.x = self.lin_vel_zero
            self.twist_cmd.angular.z = self.ang_vel_zero
        # publish the twist command
        self.publish_twist_cmd()
        # print the current iteration information
        self.print_info()
        return None

    def publish_twist_cmd(self):
        # linear speed control
        if (self.twist_cmd.linear.x >= 0.150):
          self.twist_cmd.linear.x = 0.150
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
