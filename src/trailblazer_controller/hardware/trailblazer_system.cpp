#include "trailblazer_controller/trailblazer_system.hpp"

#include <chrono>
#include <cmath>
#include <limits>
#include <memory>
#include <vector>
#include <sstream>
#include <iomanip>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace trailblazer_controller
{

hardware_interface::CallbackReturn trailblazerSystem::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  logger_ = std::make_shared<rclcpp::Logger>(
    rclcpp::get_logger("trailblazerSystem"));
  clock_ = std::make_shared<rclcpp::Clock>(rclcpp::Clock());

  hw_positions_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
  hw_velocities_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
  hw_commands_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());

  // Verify joint configuration matches your robot
  for (const hardware_interface::ComponentInfo & joint : info_.joints)
  {
    // trailblazer has velocity command and position+velocity state interfaces
    if (joint.command_interfaces.size() != 1)
    {
      RCLCPP_FATAL(
        *logger_, "Joint '%s' has %zu command interfaces. 1 expected.",
        joint.name.c_str(), joint.command_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.command_interfaces[0].name != hardware_interface::HW_IF_VELOCITY)
    {
      RCLCPP_FATAL(
        *logger_, "Joint '%s' has '%s' command interface. '%s' expected.",
        joint.name.c_str(), joint.command_interfaces[0].name.c_str(),
        hardware_interface::HW_IF_VELOCITY);
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces.size() != 2)
    {
      RCLCPP_FATAL(
        *logger_, "Joint '%s' has %zu state interfaces. 2 expected.",
        joint.name.c_str(), joint.state_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION)
    {
      RCLCPP_FATAL(
        *logger_, "Joint '%s' has '%s' first state interface. '%s' expected.",
        joint.name.c_str(), joint.state_interfaces[0].name.c_str(),
        hardware_interface::HW_IF_POSITION);
      return hardware_interface::CallbackReturn::ERROR;
    }

    if (joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY)
    {
      RCLCPP_FATAL(
        *logger_, "Joint '%s' has '%s' second state interface. '%s' expected.",
        joint.name.c_str(), joint.state_interfaces[1].name.c_str(),
        hardware_interface::HW_IF_VELOCITY);
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> trailblazerSystem::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (auto i = 0u; i < info_.joints.size(); i++)
  {
    state_interfaces.emplace_back(
      hardware_interface::StateInterface(
        info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_positions_[i]));
    state_interfaces.emplace_back(
      hardware_interface::StateInterface(
        info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_velocities_[i]));
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> trailblazerSystem::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (auto i = 0u; i < info_.joints.size(); i++)
  {
    command_interfaces.emplace_back(
      hardware_interface::CommandInterface(
        info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_commands_[i]));
  }

  return command_interfaces;
}

hardware_interface::CallbackReturn trailblazerSystem::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(*logger_, "Activating trailblazer hardware interface...");

  // Initialize default values
  for (auto i = 0u; i < hw_positions_.size(); i++)
  {
    if (std::isnan(hw_positions_[i]))
    {
      hw_positions_[i] = 0.0;
      hw_velocities_[i] = 0.0;
      hw_commands_[i] = 0.0;
    }
  }

  RCLCPP_INFO(*logger_, "Successfully activated!");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn trailblazerSystem::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(*logger_, "Deactivating trailblazer hardware interface...");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type trailblazerSystem::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
  // Simulate wheel movement (replace with actual hardware read)
  for (std::size_t i = 0; i < hw_velocities_.size(); i++)
  {
    hw_positions_[i] += period.seconds() * hw_velocities_[i];
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type trailblazerSystem::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Simulate sending commands to hardware (replace with actual hardware write)
  for (auto i = 0u; i < hw_commands_.size(); i++)
  {
    hw_velocities_[i] = hw_commands_[i];
  }

  return hardware_interface::return_type::OK;
}

}  // namespace trailblazer_controller

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  trailblazer_controller::trailblazerSystem, hardware_interface::SystemInterface)