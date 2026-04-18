#!/usr/bin/env python3
"""
Autonomous waypoint navigator for the Ground Robot.

AMCL initial pose is set via nav2_params.yaml (set_initial_pose: true).
This node just waits for Nav2 to be ready then drives through waypoints.

Usage:
  ros2 run robot_bringup waypoint_navigator
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from action_msgs.msg import GoalStatus
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy


# (x, y, yaw_degrees) — relative to map origin, matching spawn at (1.0, 1.0)
DEFAULT_WAYPOINTS = [
    (3.0,  1.0,   0.0),
    (3.0,  3.0,  90.0),
    (1.0,  3.0, 180.0),
    (1.0,  1.0, -90.0),
]


class WaypointNavigator(Node):

    def __init__(self):
        super().__init__("waypoint_navigator")

        self.declare_parameter("initial_x",   1.0)
        self.declare_parameter("initial_y",   1.0)
        self.declare_parameter("initial_yaw", 0.0)

        self._init_x   = self.get_parameter("initial_x").value
        self._init_y   = self.get_parameter("initial_y").value
        self._init_yaw = self.get_parameter("initial_yaw").value

        self._waypoints  = DEFAULT_WAYPOINTS
        self._current_wp = 0
        self._started    = False
        self._pose_published = False

        # Publish initial pose with transient-local so AMCL gets it even if
        # it subscribes slightly after we publish
        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._init_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, "/initialpose", qos
        )

        self._action_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        # Publish initial pose immediately, then retry every 2s until AMCL confirms
        self._pose_timer = self.create_timer(2.0, self._publish_initial_pose)
        # Start navigation sequence after 5s
        self.create_timer(5.0, self._start)

        self.get_logger().info(
            f"WaypointNavigator init. Spawn pose: ({self._init_x}, {self._init_y})"
        )

    def _publish_initial_pose(self):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = "map"
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = float(self._init_x)
        msg.pose.pose.position.y = float(self._init_y)
        yaw = float(self._init_yaw)
        msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        # Covariance: moderate uncertainty
        msg.pose.covariance[0]  = 0.25
        msg.pose.covariance[7]  = 0.25
        msg.pose.covariance[35] = 0.07
        self._init_pose_pub.publish(msg)
        self.get_logger().info(
            f"Published /initialpose ({self._init_x:.2f}, {self._init_y:.2f})",
            throttle_duration_sec=4.0,
        )

    def _start(self):
        if self._started:
            return
        self._started = True

        self.get_logger().info("Waiting for navigate_to_pose action server...")
        if not self._action_client.wait_for_server(timeout_sec=120.0):
            self.get_logger().error("Nav2 not available after 120s.")
            rclpy.shutdown()
            return

        self.get_logger().info("Nav2 ready — starting waypoint tour in 3s.")
        self.create_timer(3.0, self._begin_tour)

    def _begin_tour(self):
        self.destroy_timer(self._timers[-1])
        # Stop retrying initial pose
        self._pose_timer.cancel()
        self._send_next_goal()

    def _send_next_goal(self):
        if self._current_wp >= len(self._waypoints):
            self.get_logger().info("All waypoints completed!")
            rclpy.shutdown()
            return

        x, y, yaw_deg = self._waypoints[self._current_wp]
        yaw = math.radians(yaw_deg)

        self.get_logger().info(
            f"-> Waypoint {self._current_wp + 1}/{len(self._waypoints)}: "
            f"({x:.1f}, {y:.1f}, {yaw_deg:.0f}deg)"
        )

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(x)
        goal.pose.pose.position.y = float(y)
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self._action_client.send_goal_async(
            goal, feedback_callback=self._feedback_cb
        ).add_done_callback(self._goal_response_cb)

    def _goal_response_cb(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn(f"Waypoint {self._current_wp + 1} rejected, skipping.")
            self._current_wp += 1
            self._send_next_goal()
            return
        handle.get_result_async().add_done_callback(self._result_cb)

    def _feedback_cb(self, feedback_msg):
        self.get_logger().info(
            f"  Remaining: {feedback_msg.feedback.distance_remaining:.2f}m",
            throttle_duration_sec=3.0,
        )

    def _result_cb(self, future):
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"Waypoint {self._current_wp + 1} reached!")
        else:
            self.get_logger().warn(f"Waypoint {self._current_wp + 1} status={status}, continuing.")
        self._current_wp += 1
        self._send_next_goal()


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(WaypointNavigator())


if __name__ == "__main__":
    main()
