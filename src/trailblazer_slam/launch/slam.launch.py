from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config_dir = os.path.join(
        get_package_share_directory('trailblazer_slam'),
        'config',
        # 'mapper_params_online_async_gazebo.yaml'
        'mapper_params_online_async.yaml'
    )

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[config_dir],
        remappings=[
            ('/scan', '/scan')
        ]
    )

    return LaunchDescription([
        slam_node
    ])
