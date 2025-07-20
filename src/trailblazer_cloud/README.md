```bash
#old now not work
ros2 launch trailblazer_bringup oakd_robot.launch.py 
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=false params_file:=/home/rafal/TrailblazerML/src/trailblazer_cloud/params/rgbd_nav2_params.yaml

ros2 launch nav2_bringup rviz_launch.py 

## new
ros2 launch trailblazer_bringup camera_robot.launch.py 

## navsat test
ros2 launch trailblazer_nav2 dual_ekf_navsat.launch.py 
ros2 service call /fromLL robot_localization/srv/FromLL "{ll_point: {latitude: 50.0411, longitude: 22.0001, altitude: 0.0}}"


```