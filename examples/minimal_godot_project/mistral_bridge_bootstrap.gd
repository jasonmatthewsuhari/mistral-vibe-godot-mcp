extends Node

const BridgeEntryScript := preload("res://addons/mistral_mcp_bridge/bridge_entry.gd")

var _bridge_entry: Node


func _ready() -> void:
	_bridge_entry = BridgeEntryScript.new()
	_bridge_entry.name = "MistralMCPBridgeRuntime"
	add_child(_bridge_entry)
	if _bridge_entry.has_method("start_server"):
		var token := str(ProjectSettings.get_setting("mistral_mcp/bridge_token", "integration-token"))
		var port := int(ProjectSettings.get_setting("mistral_mcp/bridge_port", 19110))
		_bridge_entry.call("start_server", "127.0.0.1", port, token)


func _exit_tree() -> void:
	if _bridge_entry and _bridge_entry.has_method("stop_server"):
		_bridge_entry.call("stop_server")
