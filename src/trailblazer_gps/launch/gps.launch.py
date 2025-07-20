from docutils.nodes import description
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    gps_type_launch_arg = DeclareLaunchArgument(
        'gps_type',
        default_value='rtk_gps',
        description='Typ GPS: rtk_gps lub basic_gps'
    )
    port_launch_arg = DeclareLaunchArgument(
        'port',
        default_value='/dev/ttyUSB0',
        description='Port szeregowy, do którego podłączony jest GPS'
    )
    gps_node = Node(
        package='trailblazer_gps',
        executable=LaunchConfiguration('gps_type'),
        name='gps_node',
        parameters=[{
            'port': LaunchConfiguration('port'),
        }]
    )

    return LaunchDescription([
        gps_type_launch_arg,
        port_launch_arg,
        gps_node,
    ])
