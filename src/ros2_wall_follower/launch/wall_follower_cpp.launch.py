from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable

# ROS2 Launch System will look for this function definition #
def generate_launch_description():
    
    # ROS2 Wall Follower C++ Program Node #
    wall_follower = Node(
        package="ros2_wall_follower",
        executable="wall_follower", # cpp version
        name="wall_follower",
        output="screen",
        emulate_tty=True)

    return LaunchDescription(
        [
            SetEnvironmentVariable('RCUTILS_CONSOLE_OUTPUT_FORMAT', '[{severity}]: {message}'),
            wall_follower,
        ]
    )

# End of Code
