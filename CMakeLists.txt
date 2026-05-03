cmake_minimum_required(VERSION 3.8)
project(control)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Announcement.msg"
  DEPENDENCIES builtin_interfaces
)

install(DIRECTORY control
  DESTINATION ${PYTHON_INSTALL_DIR}
  FILES_MATCHING PATTERN "*.py"
)

install(PROGRAMS
  scripts/behavior_manager
  scripts/describe_scene_stub
  scripts/run
  scripts/speech_output
  scripts/voice_input
  DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
