from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{'yaml_filename': '/home/walkowiczf/PycharmProjects/TrailblazeML/src/trailblazer_nav2/config/map_server.yaml'}]
        ),
        # Dodaj inne komponenty, takie jak AMCL, planner itp.
    ])
