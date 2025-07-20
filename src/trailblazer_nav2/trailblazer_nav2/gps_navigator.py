from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Header

class GpsNavigator(BasicNavigator):
    """
    Extension of BasicNavigator that allows following GPS waypoints (lat/lon/yaw).
    """

    def __init__(self, name="basic_navigator"):
        super().__init__(name)

    def followGpsWaypoints(self, geoposes):
        """
        Accepts a list of geographic_msgs/GeoPose and follows them as waypoints.
        Converts GeoPose into PoseStamped with frame_id 'wgs84'.
        """
        gps_goal_poses = []
        for geopose in geoposes:
            pose_stamped = PoseStamped()
            pose_stamped.header = Header()
            pose_stamped.header.frame_id = "wgs84"
            pose_stamped.pose.position.x = geopose.position.longitude
            pose_stamped.pose.position.y = geopose.position.latitude
            pose_stamped.pose.position.z = geopose.position.altitude
            pose_stamped.pose.orientation = geopose.orientation
            gps_goal_poses.append(pose_stamped)

        # Now call the existing followWaypoints() method
        self.followWaypoints(gps_goal_poses)
