from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable

# ROS2 Launch System will look for this function definition #
def generate_launch_description():
    
    # ROS2 Wall Follower Python Program Node #
    wall_follower = Node(
        package="ros2_wall_follower",
        executable="wall_follower.py", # py version
        name="wall_follower",
        output="screen",
        emulate_tty=True,
        remappings=[
            ('/scan', '/ldlidar_node/scan')
        ]
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable('RCUTILS_CONSOLE_OUTPUT_FORMAT', '[{severity}]: {message}'),
            wall_follower,
        ]
    )