cmake_minimum_required(VERSION 3.8)
project(ros2_wall_follower)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

# include cpp "include" directory
include_directories(include)

# create cpp executables
add_executable(wall_follower src/wall_follower.cpp)
ament_target_dependencies(wall_follower rclcpp std_msgs geometry_msgs sensor_msgs nav_msgs)

# install cpp executables
install(TARGETS
  wall_follower
  DESTINATION lib/${PROJECT_NAME}
)

# install python modules
ament_python_install_package(${PROJECT_NAME})

# install python executables
install(PROGRAMS
  scripts/wall_follower.py
  DESTINATION lib/${PROJECT_NAME}
)

# test python executables
install(PROGRAMS
  scripts/service_example.py
  scripts/service_planner_example.py
  DESTINATION lib/${PROJECT_NAME}
)

# install package directories
install(DIRECTORY 
  launch
  rviz
  params
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

# End of Code
