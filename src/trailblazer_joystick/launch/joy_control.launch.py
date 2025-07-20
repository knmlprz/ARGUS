from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Argument dla wyboru topicu cmd_vel
    cmd_vel_topic_arg = DeclareLaunchArgument(
        'cmd_vel_topic',
        default_value='/cmd_vel',
        description='Topic for velocity commands'
    )

    return LaunchDescription([
        cmd_vel_topic_arg,

        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[{
                'dev': '/dev/input/js0',
                'deadzone': 0.1,
                'autorepeat_rate': 20.0,
            }]
        ),

        Node(
            package='trailblazer_joystick',
            executable='joy_twist_publisher',
            name='joy_twist_publisher',
            parameters=[{
                'linear_axis': 1,
                'angular_axis': 0,
                'scale_linear': 1.0,
                'scale_angular': 1.0,
                'deadzone': 0.1,
                'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic')
            }],
            output='screen'
        )
    ])