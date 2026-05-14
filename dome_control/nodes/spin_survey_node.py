#!/usr/bin/env python3
# spin_survey_node — ROS2 node: 360° spin survey, triggered via /survey/start service
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

from dome_control.spin_survey import SpinSurvey, SpinSurveyConfig

TICK_HZ = 5


class SpinSurveyNode(Node):
    """Spin robot 360° in place on /survey/start service call.

    Idle until /survey/start is called. Publishes /spin_survey/done on completion.
    Params (all optional — defaults from SpinSurveyConfig):
        angular_velocity, total_angle, step_angle_rad, pause_s, pass_count, pass_offset_rad
    """

    def __init__(self) -> None:
        super().__init__("spin_survey")
        cfg = SpinSurveyConfig()
        for name in SpinSurveyConfig.model_fields:
            self.declare_parameter(name, getattr(cfg, name))

        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.done_pub = self.create_publisher(Bool, "/spin_survey/done", 10)
        self.paused_pub = self.create_publisher(Bool, "/spin_survey/paused", 10)
        self.srv = self.create_service(Trigger, "/survey/start", self.on_start)

        self.survey: SpinSurvey | None = None
        self.timer = None
        self.get_logger().info("SpinSurveyNode ready — call /survey/start to begin")

    def on_start(self, request, response):
        if self.timer is not None:
            response.success = False
            response.message = "Survey already in progress"
            return response

        params = {name: self.get_parameter(name).value for name in SpinSurveyConfig.model_fields}
        params["pass_offset_rad"] = params["pass_offset_rad"] or None
        self.survey = SpinSurvey(
            params["angular_velocity"], params["total_angle"], params["step_angle_rad"], params["pause_s"],
            pass_count=params["pass_count"], pass_offset_rad=params["pass_offset_rad"],
        )
        self.survey.start()
        self.timer = self.create_timer(1.0 / TICK_HZ, self.tick)
        self.get_logger().info("Spin survey started")
        response.success = True
        response.message = "Survey started"
        return response

    def tick(self) -> None:
        vel, done = self.survey.tick(1.0 / TICK_HZ)
        self._publish_twist(vel)
        self.paused_pub.publish(Bool(data=self.survey.is_paused))
        if done:
            self._complete()

    def _publish_twist(self, angular_z: float) -> None:
        msg = Twist()
        msg.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)

    def _complete(self) -> None:
        self.destroy_timer(self.timer)
        self.timer = None
        self.survey = None
        self._publish_twist(0.0)
        self.done_pub.publish(Bool(data=True))
        self.get_logger().info("Spin survey complete")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SpinSurveyNode()
    rclpy.spin(node)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
