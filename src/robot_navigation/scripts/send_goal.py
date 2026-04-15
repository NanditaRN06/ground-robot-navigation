#!/usr/bin/env python3
import math
import sys

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


class GoalSender(Node):
    def __init__(self):
        super().__init__("goal_sender")
        self._client = ActionClient(self, NavigateToPose, "navigate_to_pose")

    def send_goal(self, x: float, y: float, yaw: float) -> None:
        if not self._client.wait_for_server(timeout_sec=15.0):
            self.get_logger().error("navigate_to_pose action server not available.")
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        half_yaw = yaw * 0.5
        goal_msg.pose.pose.orientation.z = math.sin(half_yaw)
        goal_msg.pose.pose.orientation.w = math.cos(half_yaw)

        self.get_logger().info(f"Sending goal x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}")
        future = self._client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future)
        goal_handle = future.result()

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error("Goal was rejected.")
            return

        self.get_logger().info("Goal accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result()

        if result is None:
            self.get_logger().error("No result received from Nav2.")
            return

        if result.status == 4:
            self.get_logger().info("Goal reached successfully.")
        else:
            self.get_logger().warn(f"Goal finished with status code: {result.status}")


def main():
    rclpy.init()
    node = GoalSender()

    if len(sys.argv) < 3:
        node.get_logger().error("Usage: send_goal.py <x> <y> [yaw_in_radians]")
        node.destroy_node()
        rclpy.shutdown()
        return

    x = float(sys.argv[1])
    y = float(sys.argv[2])
    yaw = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

    node.send_goal(x, y, yaw)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
