// includes
// rclcpp includes
#include "rclcpp/callback_group.hpp"                    // callback groups
#include "rclcpp/executors.hpp"                         // executors
#include "rclcpp/executors/multi_threaded_executor.hpp" // multithreaded executor
#include "rclcpp/logger.hpp"                            // logger
#include "rclcpp/node.hpp"                              // base node
#include "rclcpp/publisher.hpp"                         // publisher
#include "rclcpp/qos.hpp"                               // qos
#include "rclcpp/rclcpp.hpp"                            // rclcpp
#include "rclcpp/subscription.hpp"                      // subscriber
#include "rclcpp/subscription_options.hpp"              // subscriber options
#include "rclcpp/timer.hpp"                             // wall timer
#include "rclcpp/utilities.hpp"                         // utilities
#include "rmw/qos_profiles.h"                           // qos profiles
// ros2 interfaces
#include "geometry_msgs/msg/detail/twist__struct.hpp" // twist message structure
#include "geometry_msgs/msg/twist.hpp"                // twist message
#include "nav_msgs/msg/detail/odometry__struct.hpp" // odometry message structure
#include "nav_msgs/msg/odometry.hpp"                // odometry message
#include "sensor_msgs/msg/detail/laser_scan__struct.hpp" // laser scan message structure
#include "sensor_msgs/msg/laser_scan.hpp"                // laser scan message
// standard cpp includes
#include <bits/types/sigevent_t.h>
#include <chrono>
#include <cmath>
#include <map>
#include <memory>
#include <string>

// common global variables
// side bias options for wall follow behavior: "none" or "left" or "right"
// this is the side on which the robot will have the wall
// left - sets the robot to follow the wall on its left side
// right - sets the robot to follow the wall on its right side
// none - sets the robot to automatically choose a side
static const std::string side_choice = "none";
// algorithm choice options for wall follow behavior: "min" or "avg"
// this is the algorithm to decide closeness to the wall
// min - uses minimum scan ranges to detect the wall on its side
// avg - uses average scan ranges to detect the wall on its side
static const std::string algo_choice = "min";

// define wall follower class as a subclass of node class
class WallFollower : public rclcpp::Node {
public:
  // class constructor
  WallFollower() : Node("wall_follower") {
    RCLCPP_INFO(this->get_logger(), "Initializing Wall Follower ...");

    // wall detection algorithm choice
    if (algo_choice == "avg") {
      ang_vel_mult = 3.000;
    } else {
      ang_vel_mult = 1.250;
    }

    // declare and initialize cmd_vel publisher
    cmd_vel_pub = this->create_publisher<Twist>("/cmd_vel", 10);
    RCLCPP_INFO(this->get_logger(), "Initialized /cmd_vel Publisher");

    // declare and initialize callback group
    callback_group =
        this->create_callback_group(rclcpp::CallbackGroupType::Reentrant);

    // declare and initialize scan subscriber
    rclcpp::QoS scan_sub_qos =
        rclcpp::QoS(rclcpp::KeepLast(10), rmw_qos_profile_sensor_data);
    rclcpp::SubscriptionOptions scan_sub_options;
    scan_sub_options.callback_group = callback_group;
    scan_sub = this->create_subscription<LaserScan>(
        "/scan", scan_sub_qos,
        std::bind(&WallFollower::scan_callback, this, std::placeholders::_1),
        scan_sub_options);
    RCLCPP_INFO(this->get_logger(), "Initialized /scan Subscriber");

    // declare and initialize odom subscriber
    rclcpp::QoS odom_sub_qos =
        rclcpp::QoS(rclcpp::KeepLast(10), rmw_qos_profile_sensor_data);
    rclcpp::SubscriptionOptions odom_sub_options;
    odom_sub_options.callback_group = callback_group;
    odom_sub = this->create_subscription<Odometry>(
        "/odom", odom_sub_qos,
        std::bind(&WallFollower::odom_callback, this, std::placeholders::_1),
        odom_sub_options);
    RCLCPP_INFO(this->get_logger(), "Initialized /odom Subscriber");

    // declare and initialize control timer callback
    control_timer = this->create_wall_timer(
        std::chrono::milliseconds(500),
        std::bind(&WallFollower::control_callback, this), callback_group);
    RCLCPP_INFO(this->get_logger(), "Initialized Control Timer");

    RCLCPP_INFO(this->get_logger(), "Wall Follower Initialized !");
  }

  // class destructor
  ~WallFollower() {
    // indicate wall follower node termination
    RCLCPP_INFO(this->get_logger(), "Terminating Wall Follower ...");
    // stop the robot
    twist_cmd.linear.x = lin_vel_zero;
    twist_cmd.angular.z = ang_vel_zero;
    // publish the twist command
    publish_twist_cmd();
    RCLCPP_INFO(this->get_logger(), "Wall Follower Terminated !");
  }

private:
  // shorten lengthy class references
  using Twist = geometry_msgs::msg::Twist;
  using LaserScan = sensor_msgs::msg::LaserScan;
  using Odometry = nav_msgs::msg::Odometry;

  // define callbacks and callback group
  rclcpp::Publisher<Twist>::SharedPtr cmd_vel_pub;
  rclcpp::Subscription<LaserScan>::SharedPtr scan_sub;
  rclcpp::Subscription<Odometry>::SharedPtr odom_sub;
  rclcpp::TimerBase::SharedPtr control_timer;
  rclcpp::CallbackGroup::SharedPtr callback_group;

  // define and initialize class variables
  const float robot_radius = 0.10;                      // 10 cm
  const float side_threshold_min = robot_radius + 0.05; //  5 cm gap
  const float side_threshold_max = robot_radius + 0.10; // 10 cm gap
  const float front_threshold = robot_radius + 0.40;    // 40 cm gap
  const float pi = 3.141592654;
  const float pi_inv = 0.318309886;
  const int ignore_iterations = 5;
  int iterations_count = 0;
  // process variables
  bool wall_found = false;
  std::string side_chosen = "none";
  const float lin_vel_zero = 0.000;
  const float lin_vel_slow = 0.100;
  const float lin_vel_fast = 0.250;
  const float ang_vel_zero = 0.000;
  const float ang_vel_slow = 0.050;
  const float ang_vel_fast = 0.500;
  float ang_vel_mult = 0.0;
  // velocity publisher variables
  Twist twist_cmd;
  // scan subscriber variables
  bool scan_info_done = false;
  float scan_angle_min = 0.0;
  float scan_angle_max = 0.0;
  float scan_angle_inc = 0.0;
  float scan_range_min = 0.0;
  float scan_range_max = 0.0;
  float scan_right_range = 0.0;
  float scan_front_range = 0.0;
  float scan_left_range = 0.0;
  int scan_angle_range = 0;
  int scan_ranges_size = 0;
  int scan_right_index = 0;
  int scan_front_index = 0;
  int scan_left_index = 0;
  int scan_sides_angle_range = 15; // degs
  int scan_front_angle_range = 15; // degs
  int scan_right_range_from_index = 0;
  int scan_right_range_to_index = 0;
  int scan_front_range_from_index = 0;
  int scan_front_range_to_index = 0;
  int scan_left_range_from_index = 0;
  int scan_left_range_to_index = 0;
  // odom subscriber variables
  bool odom_info_done = false;
  double odom_initial_x = 0.0;
  double odom_initial_y = 0.0;
  double odom_initial_yaw = 0.0;
  double odom_curr_x = 0.0;
  double odom_curr_y = 0.0;
  double odom_curr_yaw = 0.0;
  double odom_prev_x = 0.0;
  double odom_prev_y = 0.0;
  double odom_prev_yaw = 0.0;
  float odom_distance = 0.0;
  float odom_lin_vel = 0.0;
  float odom_ang_vel = 0.0;
  std::map<std::string, double> angles;

  // class methods and callbacks

  void scan_callback(const LaserScan::SharedPtr scan_msg) {
    if (scan_info_done) {
      // do this step continuously
      if (algo_choice == "avg") {
        // use average ranges if algo_choice is set to "avg"
        // ~~~~~ AVERAGE OF RANGE VALUES METHOD ~~~~~ //
        // initialize local variables to hold sum and count
        // for right, front and left ranges
        float scan_right_range_sum = 0.0;
        float scan_front_range_sum = 0.0;
        float scan_left_range_sum = 0.0;
        int scan_right_count = 0;
        int scan_front_count = 0;
        int scan_left_count = 0;
        // loop through the scan ranges and accumulate the sum of segments
        for (int index = 0; index < scan_ranges_size; index++) {
          if (!std::isinf(scan_msg->ranges[index])) {
            if ((index >= scan_right_range_from_index) &&
                (index <= scan_right_range_to_index)) {
              scan_right_range_sum += scan_msg->ranges[index];
              scan_right_count += 1;
            }
            if ((index >= scan_front_range_from_index) &&
                (index <= scan_front_range_to_index)) {
              scan_front_range_sum += scan_msg->ranges[index];
              scan_front_count += 1;
            }
            if ((index >= scan_left_range_from_index) &&
                (index <= scan_left_range_to_index)) {
              scan_left_range_sum += scan_msg->ranges[index];
              scan_left_count += 1;
            }
          } else {
            // otherwise discard the scan range with infinity as value
          }
        }
        // calculate the average of each segment
        if (scan_right_count > 0) {
          scan_right_range = (scan_right_range_sum / scan_right_count);
        } else {
          scan_right_range = scan_range_min;
        }
        if (scan_front_count > 0) {
          scan_front_range = (scan_front_range_sum / scan_front_count);
        } else {
          scan_front_range = scan_range_min;
        }
        if (scan_left_count > 0) {
          scan_left_range = (scan_left_range_sum / scan_left_count);
        } else {
          scan_left_range = scan_range_min;
        }
        // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ //
      } else {
        // otherwise use minimum ranges
        // if algo_choice is set to "min" or anything else
        // ~~~~~ MINIMUM OF RANGE VALUES METHOD ~~~~~ //
        // initialize variables to hold minimum values
        float scan_right_range_min = scan_range_max;
        float scan_front_range_min = scan_range_max;
        float scan_left_range_min = scan_range_max;
        // loop through the scan ranges and get the minimum value
        for (int index = 0; index < scan_ranges_size; index++) {
          if (!std::isinf(scan_msg->ranges[index])) {
            if ((index >= scan_right_range_from_index) &&
                (index <= scan_right_range_to_index)) {
              if (scan_right_range_min > scan_msg->ranges[index]) {
                scan_right_range_min = scan_msg->ranges[index];
              } else {
                // otherwise do nothing
              }
            }
            if ((index >= scan_front_range_from_index) &&
                (index <= scan_front_range_to_index)) {
              if (scan_front_range_min > scan_msg->ranges[index]) {
                scan_front_range_min = scan_msg->ranges[index];
              } else {
                // otherwise do nothing
              }
            }
            if ((index >= scan_left_range_from_index) &&
                (index <= scan_left_range_to_index)) {
              if (scan_left_range_min > scan_msg->ranges[index]) {
                scan_left_range_min = scan_msg->ranges[index];
              } else {
                // otherwise do nothing
              }
            }
          } else {
            // otherwise discard the scan range with infinity as value
          }
        }
        // set the range values to their minimum values
        if (scan_right_range > 0.0) {
          scan_right_range = scan_right_range_min;
        } else {
          scan_right_range = scan_range_min;
        }
        if (scan_front_range > 0.0) {
          scan_front_range = scan_front_range_min;
        } else {
          scan_front_range = scan_range_min;
        }
        if (scan_left_range > 0.0) {
          scan_left_range = scan_left_range_min;
        } else {
          scan_left_range = scan_range_min;
        }
        // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ //
      }
    } else {
      // do this step only once
      // get the min and max angles
      scan_angle_min = scan_msg->angle_min;
      scan_angle_max = scan_msg->angle_max;
      // get the min and max range values
      scan_range_min = scan_msg->range_min;
      scan_range_max = scan_msg->range_max;
      // get the size of the ranges array
      scan_ranges_size = scan_msg->ranges.size();
      // get the total scan angle range
      scan_angle_range =
          (int)((fabs(scan_angle_min) + fabs(scan_angle_max)) * (180.0 / pi));
      // get the angle increments per scan ray
      scan_angle_inc = ((float)(scan_angle_range) / (float)(scan_ranges_size));
      // calculate the front, right and left scan ray indexes
      scan_front_index = (scan_ranges_size / 2);
      scan_right_index = scan_front_index - (int)(90.0 / scan_angle_inc) - 1;
      scan_left_index = scan_front_index + (int)(90.0 / scan_angle_inc) + 1;
      // calculate the front scan ray ranges
      scan_front_range_from_index =
          scan_front_index - (int)(scan_front_angle_range / scan_angle_inc);
      scan_front_range_to_index =
          scan_front_index + (int)(scan_front_angle_range / scan_angle_inc);
      // calculate right and left scan ray ranges
      if (scan_angle_range > 180) {
        scan_right_range_from_index =
            scan_right_index - (int)(scan_sides_angle_range / scan_angle_inc);
        scan_right_range_to_index =
            scan_right_index + (int)(scan_sides_angle_range / scan_angle_inc);
        scan_left_range_from_index =
            scan_left_index - (int)(scan_sides_angle_range / scan_angle_inc);
        scan_left_range_to_index =
            scan_left_index + (int)(scan_sides_angle_range / scan_angle_inc);
      } else {
        scan_right_range_from_index = scan_right_index;
        scan_right_range_to_index =
            scan_right_index + (int)(scan_sides_angle_range / scan_angle_inc);
        scan_left_range_from_index =
            scan_left_index - (int)(scan_sides_angle_range / scan_angle_inc);
        scan_left_range_to_index = scan_left_index;
      }
      // set flag to true so this step will not be done again
      scan_info_done = true;
      // print scan details
      RCLCPP_INFO(this->get_logger(), "~~~~~ Start Scan Info ~~~~");
      RCLCPP_INFO(this->get_logger(), "scan_angle_min: %+0.3f", scan_angle_min);
      RCLCPP_INFO(this->get_logger(), "scan_angle_max: %+0.3f", scan_angle_max);
      RCLCPP_INFO(this->get_logger(), "scan_range_min: %+0.3f", scan_range_min);
      RCLCPP_INFO(this->get_logger(), "scan_range_max: %+0.3f", scan_range_max);
      RCLCPP_INFO(this->get_logger(), "scan_angle_range: %d", scan_angle_range);
      RCLCPP_INFO(this->get_logger(), "scan_ranges_size: %d", scan_ranges_size);
      RCLCPP_INFO(this->get_logger(), "scan_angle_inc: %+0.3f", scan_angle_inc);
      RCLCPP_INFO(this->get_logger(), "scan_right_index: %d", scan_right_index);
      RCLCPP_INFO(this->get_logger(), "scan_front_index: %d", scan_front_index);
      RCLCPP_INFO(this->get_logger(), "scan_left_index: %d", scan_left_index);
      RCLCPP_INFO(this->get_logger(), "scan_right_range_index:");
      RCLCPP_INFO(this->get_logger(), "from: %d ~~~> to: %d",
                  scan_right_range_from_index, scan_right_range_to_index);
      RCLCPP_INFO(this->get_logger(), "scan_front_range_index:");
      RCLCPP_INFO(this->get_logger(), "from: %d ~~~> to: %d",
                  scan_front_range_from_index, scan_front_range_to_index);
      RCLCPP_INFO(this->get_logger(), "scan_left_range_index:");
      RCLCPP_INFO(this->get_logger(), "from: %d ~~~> to: %d",
                  scan_left_range_from_index, scan_left_range_to_index);
      RCLCPP_INFO(this->get_logger(), "~~~~~ End Scan Info ~~~~");
    }
  }

  void odom_callback(const Odometry::SharedPtr odom_msg) {
    if (odom_info_done) {
      // do this step continuously
      // get current odometry values
      odom_curr_x = odom_msg->pose.pose.position.x;
      odom_curr_y = odom_msg->pose.pose.position.y;
      angles = euler_from_quaternion(
          odom_msg->pose.pose.orientation.x, odom_msg->pose.pose.orientation.y,
          odom_msg->pose.pose.orientation.z, odom_msg->pose.pose.orientation.w);
      odom_curr_yaw = angles["yaw_deg"];
      // calculate distance based on current and previous odometry values
      odom_distance += calculate_distance(odom_prev_x, odom_prev_y, odom_curr_x,
                                          odom_curr_y);
      // set previous odometry values to current odometry values
      odom_prev_x = odom_curr_x;
      odom_prev_y = odom_curr_y;
      odom_prev_yaw = odom_curr_yaw;
    } else {
      // do this step only once
      // get initial odometry values
      odom_initial_x = odom_msg->pose.pose.position.x;
      odom_initial_y = odom_msg->pose.pose.position.y;
      angles = euler_from_quaternion(
          odom_msg->pose.pose.orientation.x, odom_msg->pose.pose.orientation.y,
          odom_msg->pose.pose.orientation.z, odom_msg->pose.pose.orientation.w);
      odom_initial_yaw = angles["yaw_deg"];
      // set previous odometry values to initial odometry values
      odom_prev_x = odom_initial_x;
      odom_prev_y = odom_initial_y;
      odom_prev_yaw = odom_initial_yaw;
      // set flag to true so this step will not be done again
      odom_info_done = true;
      // print odom details
      RCLCPP_INFO(this->get_logger(), "~~~~~ Start Odom Info ~~~~");
      RCLCPP_INFO(this->get_logger(), "odom_initial_x: %+0.3f", odom_initial_x);
      RCLCPP_INFO(this->get_logger(), "odom_initial_y: %+0.3f", odom_initial_y);
      RCLCPP_INFO(this->get_logger(), "odom_initial_yaw: %+0.3f",
                  odom_initial_yaw);
      RCLCPP_INFO(this->get_logger(), "~~~~~ End Odom Info ~~~~");
    }
  }

  void control_callback() {
    if (iterations_count >= ignore_iterations) {
      // fix for delayed laser scanner startup
      if (wall_found) {
        // now the robot is either facing the wall after finding the wall
        // or running the wall follower process and facing a wall or obstacle
        if (scan_front_range < front_threshold) {
          // turn towards the side opposite to the wall while moving forward
          twist_cmd.linear.x = lin_vel_slow;
          if (side_chosen == "right") {
            // turn the robot to the left
            twist_cmd.angular.z = (ang_vel_fast * ang_vel_mult);
          } else if (side_chosen == "left") {
            // turn the robot to the right
            twist_cmd.angular.z = (-ang_vel_fast * ang_vel_mult);
          } else {
            // otherwise do nothing
            // this choice will never happen
          }
        } else {
          // otherwise keep going straight
          // until either obstacle or wall is detected
          twist_cmd.linear.x = lin_vel_fast;
          // check the closeness to the wall
          if (side_chosen == "right") {
            // wall is on the right
            if (scan_right_range < side_threshold_min) {
              // turn left to move away from the wall
              twist_cmd.angular.z = ang_vel_slow;
            } else if (scan_right_range > side_threshold_max) {
              // turn right to move close to the wall
              twist_cmd.angular.z = -ang_vel_slow;
            } else {
              // do not turn and keep going straight
              twist_cmd.angular.z = ang_vel_zero;
            }
          } else if (side_chosen == "left") {
            // wall is on the left
            if (scan_left_range < side_threshold_min) {
              // turn right to move away from the wall
              twist_cmd.angular.z = -ang_vel_slow;
            } else if (scan_left_range > side_threshold_max) {
              // turn left to move close to the wall
              twist_cmd.angular.z = ang_vel_slow;
            } else {
              // do not turn and keep going straight
              twist_cmd.angular.z = ang_vel_zero;
            }
          } else {
            // otherwise do nothing
            // this choice will never happen
          }
        }
      } else {
        // find the wall closest to the robot
        // keep moving forward until the robot detects
        // an obstacle or wall in its front
        if (scan_front_range < front_threshold) {
          // immediately set the wall_found flag to true
          // to break out of this subprocess
          wall_found = true;
          RCLCPP_INFO(this->get_logger(), "Wall Found!");
          // stop the robot
          twist_cmd.linear.x = lin_vel_zero;
          twist_cmd.angular.z = ang_vel_zero;
          RCLCPP_INFO(this->get_logger(), "Robot Stopped!");
          // choose a side to turn if side_choice is set to none
          if ((side_choice != "right") && (side_choice != "left")) {
            // choose the side that has closer range value
            // closer range value indicates that the wall is on that side
            if (scan_right_range < scan_left_range) {
              // wall is on the right
              side_chosen = "right";
            } else if (scan_right_range > scan_left_range) {
              // wall is on the left
              side_chosen = "left";
            } else {
              // otherwise do nothing
              // this choice will never happen
            }
            RCLCPP_INFO(this->get_logger(), "Side Chosen: %s",
                        side_chosen.c_str());
          } else {
            // otherwise do nothing
            // side is already set by the user
          }
        } else {
          // otherwise keep going straight slowly
          // until either obstacle or wall is detected
          twist_cmd.linear.x = lin_vel_slow;
          twist_cmd.angular.z = ang_vel_zero;
        }
      }
    } else {
      // just increment the iterations count
      iterations_count += 1;
      // keep the robot stopped
      twist_cmd.linear.x = lin_vel_zero;
      twist_cmd.angular.z = ang_vel_zero;
    }
    // publish the twist command
    publish_twist_cmd();
    // print the current iteration information
    print_info();
  }

  void publish_twist_cmd() {
    // linear speed control
    if (twist_cmd.linear.x >= 0.150) {
      twist_cmd.linear.x = 0.150;
    } else {
      // do nothing
    }
    // angular speed control
    if (twist_cmd.angular.z >= 0.450) {
      twist_cmd.angular.z = 0.450;
    } else {
      // do nothing
    }
    // publish command
    cmd_vel_pub->publish(twist_cmd);
  }

  void print_info() {
    RCLCPP_INFO(this->get_logger(), "Scan: L: %0.3f F: %0.3f R: %0.3f",
                scan_left_range, scan_front_range, scan_right_range);
    RCLCPP_INFO(this->get_logger(), "Odom: X: %+0.3f Y: %+0.3f", odom_curr_x,
                odom_curr_y);
    RCLCPP_INFO(this->get_logger(), "Odom: Yaw: %+0.3f Dist: %0.3f",
                odom_curr_yaw, odom_distance);
    RCLCPP_INFO(this->get_logger(), "Vel: Lin: %+0.3f Ang: %+0.3f",
                twist_cmd.linear.x, twist_cmd.angular.z);
    RCLCPP_INFO(this->get_logger(), "~~~~~~~~~~");
  }

  float calculate_distance(double prev_x, double prev_y, double curr_x,
                           double curr_y) {
    // function to calculate euclidean distance in 2d plane

    // calculate distance
    float distance = powf(
        (powf((curr_x - prev_x), 2.0) + powf((curr_y - prev_y), 2.0)), 0.50);

    // return the distance value
    return distance;
  }

  std::map<std::string, double> euler_from_quaternion(double quat_x,
                                                      double quat_y,
                                                      double quat_z,
                                                      double quat_w) {
    // function to convert quaternions to euler angles

    // calculate roll
    double sinr_cosp = 2 * (quat_w * quat_x + quat_y * quat_z);
    double cosr_cosp = 1 - 2 * (quat_x * quat_x + quat_y * quat_y);
    double roll_rad = atan2(sinr_cosp, cosr_cosp);
    double roll_deg = (double)(roll_rad * 180 * pi_inv);

    // calculate pitch
    double sinp = 2 * (quat_w * quat_y - quat_z * quat_x);
    double pitch_rad = asin(sinp);
    double pitch_deg = (double)(pitch_rad * 180 * pi_inv);

    // calculate yaw
    double siny_cosp = 2 * (quat_w * quat_z + quat_x * quat_y);
    double cosy_cosp = 1 - 2 * (quat_y * quat_y + quat_z * quat_z);
    double yaw_rad = atan2(siny_cosp, cosy_cosp);
    double yaw_deg = (double)(yaw_rad * 180 * pi_inv);

    // store the angle values in a map
    std::map<std::string, double> angles;
    angles["roll_rad"] = roll_rad;
    angles["roll_deg"] = roll_deg;
    angles["pitch_rad"] = pitch_rad;
    angles["pitch_deg"] = pitch_deg;
    angles["yaw_rad"] = yaw_rad;
    angles["yaw_deg"] = yaw_deg;

    // return the angle values
    return angles;
  }

}; // class WallFollower

int main(int argc, char **argv) {

  // initialize ROS2 node
  rclcpp::init(argc, argv);

  // create an instance of the wall follower class
  std::shared_ptr<WallFollower> wall_follower =
      std::make_shared<WallFollower>();

  // create a multithreaded executor
  rclcpp::executors::MultiThreadedExecutor executor;

  // add the wall follower node to the executor
  executor.add_node(wall_follower);

  // spin the executor to handle callbacks
  executor.spin();

  // shutdown ROS2 node when spin completes
  rclcpp::shutdown();

  return 0;
}

// End of Code
