#!/usr/bin/env python3
"""
send_goal.py – Simple Nav2 goal sender for the Ground Robot.

Sends a navigation goal to the Nav2 action server (NavigateToPose).
Can be run as a ROS 2 node or used as a library.

Usage (as a ROS 2 node):
  ros2 run robot_bringup send_goal --ros-args -p x:=5.0 -p y:=3.0 -p yaw:=0.0

Or with ros2 launch:
  ros2 run robot_bringup send_goal

The node will wait for the Nav2 action server to be available, send the goal,
and print the result.
"""

import sys
import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.duration import Duration
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from tf_transformations import quaternion_from_euler


class GoalSender(Node):
    """Sends a single navigation goal to the Nav2 NavigateToPose action server."""

    def __init__(self):
        super().__init__("goal_sender")

        # ── Parameters ────────────────────────────────────────────────────
        self.declare_parameter("x",   5.0)
        self.declare_parameter("y",   3.0)
        self.declare_parameter("yaw", 0.0)  # radians

        self._x   = self.get_parameter("x").value
        self._y   = self.get_parameter("y").value
        self._yaw = self.get_parameter("yaw").value

        # ── Action client ─────────────────────────────────────────────────
        self._action_client = ActionClient(
            self, NavigateToPose, "navigate_to_pose"
        )
        self.get_logger().info(
            f"GoalSender ready. Target: x={self._x:.2f}  y={self._y:.2f}  yaw={self._yaw:.2f} rad"
        )

        # Send after a short delay
        self.create_timer(2.0, self._send_goal_once)
        self._goal_sent = False

    def _send_goal_once(self):
        if self._goal_sent:
            return
        self._goal_sent = True

        self.get_logger().info("Waiting for NavigateToPose action server…")
        if not self._action_client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error("Action server not available! Is Nav2 running?")
            rclpy.shutdown()
            return

        # Build goal message
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp    = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = float(self._x)
        goal_msg.pose.pose.position.y = float(self._y)
        goal_msg.pose.pose.position.z = 0.0

        q = quaternion_from_euler(0, 0, float(self._yaw))
        goal_msg.pose.pose.orientation.x = q[0]
        goal_msg.pose.pose.orientation.y = q[1]
        goal_msg.pose.pose.orientation.z = q[2]
        goal_msg.pose.pose.orientation.w = q[3]

        self.get_logger().info(
            f"Sending goal → x={self._x:.2f}  y={self._y:.2f}  yaw={self._yaw:.2f}"
        )
        send_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback
        )
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal REJECTED by Nav2.")
            rclpy.shutdown()
            return
        self.get_logger().info("Goal ACCEPTED. Robot is navigating…")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        remaining = feedback.distance_remaining
        self.get_logger().info(
            f"  Distance remaining: {remaining:.2f} m", throttle_duration_sec=2.0
        )

    def _result_callback(self, future):
        result = future.result()
        if result.status == 4:   # SUCCEEDED
            self.get_logger().info("✅ Goal REACHED successfully!")
        else:
            self.get_logger().warn(f"❌ Goal ended with status: {result.status}")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = GoalSender()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
