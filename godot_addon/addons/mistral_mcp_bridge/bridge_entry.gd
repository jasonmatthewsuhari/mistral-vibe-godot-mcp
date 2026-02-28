@tool
extends Node

const CONTENT_TYPE_JSON := "application/json"
const STATUS_TEXT := {
	200: "OK",
	400: "Bad Request",
	401: "Unauthorized",
	404: "Not Found",
	405: "Method Not Allowed",
	500: "Internal Server Error"
}
const ROUTES := {
	"/health": "GET",
	"/scene/create": "POST",
	"/scene/add_node": "POST",
	"/scene/load_sprite": "POST",
	"/scene/export_mesh_library": "POST",
	"/scene/save": "POST",
	"/uid/get": "POST",
	"/uid/refresh": "POST",
	"/render/capture": "POST",
	"/render/interact": "POST"
}
const CLICK_BUTTON_LEFT := 1
const CAMERA_ORBIT_SENSITIVITY_DEFAULT := 0.01

var _token := ""
var _server := TCPServer.new()
var _running := false
var _bind_host := "127.0.0.1"
var _bind_port := 19110
const BIND_RETRY_COUNT := 30
const BIND_RETRY_DELAY_MS := 100


func start_server(bind_host: String = "127.0.0.1", bind_port: int = 19110, token: String = "") -> void:
	if bind_host != "127.0.0.1":
		push_error("Bridge must bind to 127.0.0.1 only.")
		return
	if token.strip_edges() == "":
		push_error("Bridge token cannot be empty.")
		return
	_bind_host = bind_host
	_bind_port = bind_port
	_token = token
	if _server.is_listening():
		_server.stop()
	var err := OK
	for _attempt in range(BIND_RETRY_COUNT):
		err = _server.listen(_bind_port, _bind_host)
		if err == OK:
			break
		OS.delay_msec(BIND_RETRY_DELAY_MS)
	if err != OK:
		push_error("Failed to start bridge server after retries: %s" % [error_string(err)])
		return
	_running = true
	set_process(true)


func stop_server() -> void:
	_running = false
	set_process(false)
	if _server.is_listening():
		_server.stop()


func _process(_delta: float) -> void:
	if not _running:
		return
	while _server.is_connection_available():
		var peer := _server.take_connection()
		if peer == null:
			return
		_handle_peer(peer)


func _handle_peer(peer: StreamPeerTCP) -> void:
	var raw := _read_http_request(peer, 1500)
	if raw.strip_edges() == "":
		_send_json_response(peer, 400, _error_payload("/unknown", "invalid_request", "Empty request"))
		return

	var request := _parse_http_request(raw)
	if request.is_empty():
		_send_json_response(peer, 400, _error_payload("/unknown", "invalid_request", "Malformed request"))
		return

	var method: String = request.get("method", "")
	var path: String = request.get("path", "")
	var headers: Dictionary = request.get("headers", {})
	var body: String = request.get("body", "")

	if not ROUTES.has(path):
		_send_json_response(peer, 404, _error_payload(path, "not_found", "Unknown endpoint"))
		return
	if method != ROUTES[path]:
		_send_json_response(peer, 405, _error_payload(path, "method_not_allowed", "Invalid method"))
		return
	if not _is_token_valid(headers):
		_send_json_response(peer, 401, _error_payload(path, "unauthorized", "Missing or invalid bearer token"))
		return

	var payload := {}
	if body.strip_edges() != "":
		var parser := JSON.new()
		var parse_status := parser.parse(body)
		if parse_status != OK:
			_send_json_response(peer, 400, _error_payload(path, "invalid_json", "Request body must be valid JSON"))
			return
		payload = parser.data
		if not (payload is Dictionary):
			_send_json_response(peer, 400, _error_payload(path, "invalid_json", "Request body must be an object"))
			return

	var result := _dispatch_endpoint(path, payload)
	var status := int(result.get("status", 200))
	var response_payload: Dictionary = result.get("payload", _error_payload(path, "bridge_error", "Unknown bridge error"))
	_send_json_response(peer, status, response_payload)


func _dispatch_endpoint(path: String, payload: Dictionary) -> Dictionary:
	match path:
		"/health":
			return {"status": 200, "payload": _handle_health()}
		"/scene/create":
			return _handle_scene_create(payload)
		"/scene/add_node":
			return _handle_scene_add_node(payload)
		"/scene/load_sprite":
			return _handle_scene_load_sprite(payload)
		"/scene/export_mesh_library":
			return _handle_scene_export_mesh_library(payload)
		"/scene/save":
			return _handle_scene_save(payload)
		"/uid/get":
			return _handle_uid_get(payload)
		"/uid/refresh":
			return _handle_uid_refresh(payload)
		"/render/capture":
			return _handle_render_capture(payload)
		"/render/interact":
			return _handle_render_interact(payload)
		_:
			return {"status": 404, "payload": _error_payload(path, "not_found", "Unknown endpoint")}


func _handle_health() -> Dictionary:
	return {
		"ok": true,
		"status": "healthy",
		"bridge_version": "0.2.0",
		"bind_host": _bind_host,
		"bind_port": _bind_port
	}


func _handle_scene_create(payload: Dictionary) -> Dictionary:
	var scene_path := _normalize_res_path(str(payload.get("scene_path", "")), ".tscn")
	if scene_path == "":
		return {"status": 400, "payload": _error_payload("/scene/create", "validation_error", "scene_path is required")}
	var root_node_type := str(payload.get("root_node_type", "Node2D"))
	var root_node := _instantiate_node(root_node_type)
	if root_node == null:
		return {"status": 400, "payload": _error_payload("/scene/create", "invalid_node_type", "Unknown root node type")}

	var dir_path := scene_path.get_base_dir()
	var err_mkdir := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_path))
	if err_mkdir != OK:
		return {"status": 500, "payload": _error_payload("/scene/create", "io_error", "Failed to create scene directory")}

	root_node.name = str(payload.get("root_node_name", "Root"))
	var packed := PackedScene.new()
	var err_pack := packed.pack(root_node)
	if err_pack != OK:
		return {"status": 500, "payload": _error_payload("/scene/create", "pack_error", "Failed to pack scene")}
	var err_save := ResourceSaver.save(packed, scene_path)
	root_node.queue_free()
	if err_save != OK:
		return {"status": 500, "payload": _error_payload("/scene/create", "io_error", "Failed to save scene")}
	return {"status": 200, "payload": {"ok": true, "scene_path": scene_path, "uid": str(ResourceLoader.get_resource_uid(scene_path))}}


func _handle_scene_add_node(payload: Dictionary) -> Dictionary:
	var scene_path := _normalize_res_path(str(payload.get("scene_path", "")), ".tscn")
	if scene_path == "":
		return {"status": 400, "payload": _error_payload("/scene/add_node", "validation_error", "scene_path is required")}
	var scene_result := _load_scene_root(scene_path)
	if int(scene_result.get("status", 500)) != 200:
		return scene_result
	var root: Node = scene_result.get("root")
	var parent_path := str(payload.get("parent_node_path", ""))
	var parent := _resolve_node(root, parent_path)
	if parent == null:
		root.queue_free()
		return {"status": 404, "payload": _error_payload("/scene/add_node", "node_not_found", "Parent node path not found")}
	var node_type := str(payload.get("node_type", ""))
	var node_name := str(payload.get("node_name", ""))
	if node_type == "" or node_name == "":
		root.queue_free()
		return {"status": 400, "payload": _error_payload("/scene/add_node", "validation_error", "node_type and node_name are required")}
	var child := _instantiate_node(node_type)
	if child == null:
		root.queue_free()
		return {"status": 400, "payload": _error_payload("/scene/add_node", "invalid_node_type", "Unknown node type")}
	child.name = node_name
	parent.add_child(child)
	_apply_node_properties(child, payload.get("properties", {}))
	var save_result := _save_scene_root(root, scene_path)
	if int(save_result.get("status", 500)) != 200:
		return save_result
	return {"status": 200, "payload": {"ok": true, "node_path": str(child.get_path())}}


func _handle_scene_load_sprite(payload: Dictionary) -> Dictionary:
	var scene_path := _normalize_res_path(str(payload.get("scene_path", "")), ".tscn")
	var sprite_node_path := str(payload.get("sprite_node_path", ""))
	var texture_path := _normalize_res_path(str(payload.get("texture_path", "")))
	if scene_path == "" or sprite_node_path == "" or texture_path == "":
		return {"status": 400, "payload": _error_payload("/scene/load_sprite", "validation_error", "scene_path, sprite_node_path, texture_path are required")}
	var texture := ResourceLoader.load(texture_path)
	if texture == null:
		return {"status": 404, "payload": _error_payload("/scene/load_sprite", "resource_not_found", "Texture resource not found")}
	var scene_result := _load_scene_root(scene_path)
	if int(scene_result.get("status", 500)) != 200:
		return scene_result
	var root: Node = scene_result.get("root")
	var node := _resolve_node(root, sprite_node_path)
	if node == null:
		root.queue_free()
		return {"status": 404, "payload": _error_payload("/scene/load_sprite", "node_not_found", "Sprite node not found")}
	if not _set_node_property(node, "texture", texture):
		root.queue_free()
		return {"status": 400, "payload": _error_payload("/scene/load_sprite", "invalid_node", "Node does not expose a texture property")}
	var save_result := _save_scene_root(root, scene_path)
	if int(save_result.get("status", 500)) != 200:
		return save_result
	return {"status": 200, "payload": {"ok": true, "sprite_node_path": sprite_node_path, "texture_uid": str(ResourceLoader.get_resource_uid(texture_path))}}


func _handle_scene_export_mesh_library(payload: Dictionary) -> Dictionary:
	var source_scene_path := _normalize_res_path(str(payload.get("source_scene_path", "")), ".tscn")
	var mesh_library_path := _normalize_res_path(str(payload.get("mesh_library_path", "")), ".tres")
	if source_scene_path == "" or mesh_library_path == "":
		return {"status": 400, "payload": _error_payload("/scene/export_mesh_library", "validation_error", "source_scene_path and mesh_library_path are required")}
	var scene_result := _load_scene_root(source_scene_path)
	if int(scene_result.get("status", 500)) != 200:
		return scene_result
	var root: Node = scene_result.get("root")
	var mesh_library := MeshLibrary.new()
	var mesh_nodes := _collect_mesh_nodes(root)
	for idx in range(mesh_nodes.size()):
		var mesh_node: MeshInstance3D = mesh_nodes[idx]
		mesh_library.create_item(idx)
		mesh_library.set_item_name(idx, mesh_node.name)
		mesh_library.set_item_mesh(idx, mesh_node.mesh)
	var save_path_dir := mesh_library_path.get_base_dir()
	var err_mkdir := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(save_path_dir))
	if err_mkdir != OK:
		root.queue_free()
		return {"status": 500, "payload": _error_payload("/scene/export_mesh_library", "io_error", "Failed to create mesh library directory")}
	var err_save := ResourceSaver.save(mesh_library, mesh_library_path)
	root.queue_free()
	if err_save != OK:
		return {"status": 500, "payload": _error_payload("/scene/export_mesh_library", "io_error", "Failed to save mesh library")}
	return {"status": 200, "payload": {"ok": true, "mesh_library_path": mesh_library_path, "item_count": mesh_nodes.size()}}


func _handle_scene_save(payload: Dictionary) -> Dictionary:
	var scene_path := _normalize_res_path(str(payload.get("scene_path", "")), ".tscn")
	if scene_path == "":
		return {"status": 400, "payload": _error_payload("/scene/save", "validation_error", "scene_path is required")}
	if bool(payload.get("make_inherited", false)):
		return {"status": 400, "payload": _error_payload("/scene/save", "not_supported", "make_inherited is not supported in wave 2")}
	var scene_result := _load_scene_root(scene_path)
	if int(scene_result.get("status", 500)) != 200:
		return scene_result
	var root: Node = scene_result.get("root")
	var output_path := scene_path
	var variant_name := str(payload.get("variant_name", ""))
	if variant_name != "":
		var base_name := scene_path.get_basename()
		output_path = "%s_%s.tscn" % [base_name, variant_name]
	var save_result := _save_scene_root(root, output_path)
	if int(save_result.get("status", 500)) != 200:
		return save_result
	return {"status": 200, "payload": {"ok": true, "saved_path": output_path, "uid": str(ResourceLoader.get_resource_uid(output_path))}}


func _handle_uid_get(payload: Dictionary) -> Dictionary:
	var resource_path := _normalize_res_path(str(payload.get("resource_path", "")))
	if resource_path == "":
		return {"status": 400, "payload": _error_payload("/uid/get", "validation_error", "resource_path is required")}
	if not ResourceLoader.exists(resource_path):
		return {"status": 404, "payload": _error_payload("/uid/get", "resource_not_found", "Resource path does not exist")}
	var uid := ResourceLoader.get_resource_uid(resource_path)
	return {"status": 200, "payload": {"ok": true, "uid": str(uid), "resource_path": resource_path}}


func _handle_uid_refresh(payload: Dictionary) -> Dictionary:
	var raw_paths := payload.get("paths", [])
	var paths: Array = []
	if raw_paths is Array:
		paths = raw_paths
	var updated_paths: Array[String] = []
	for raw_path in paths:
		var resource_path := _normalize_res_path(str(raw_path))
		if resource_path == "" or not ResourceLoader.exists(resource_path):
			continue
		var uid := ResourceLoader.get_resource_uid(resource_path)
		if uid > 0:
			updated_paths.append(resource_path)
	return {"status": 200, "payload": {"ok": true, "updated_count": updated_paths.size(), "updated_paths": updated_paths}}


func _handle_render_capture(payload: Dictionary) -> Dictionary:
	var width := int(payload.get("width", 1280))
	var height := int(payload.get("height", 720))
	if width <= 0 or height <= 0:
		return {"status": 400, "payload": _error_payload("/render/capture", "validation_error", "width and height must be positive")}

	var viewport_texture := get_viewport().get_texture()
	if viewport_texture == null:
		return {"status": 500, "payload": _error_payload("/render/capture", "capture_failed", "No viewport texture available")}
	var image := viewport_texture.get_image()
	if image == null:
		return {"status": 500, "payload": _error_payload("/render/capture", "capture_failed", "Unable to read viewport image")}
	if image.get_width() != width or image.get_height() != height:
		image.resize(width, height, Image.INTERPOLATE_BILINEAR)

	var capture_dir := "user://mistral_mcp/renders"
	var mkdir_err := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(capture_dir))
	if mkdir_err != OK:
		return {"status": 500, "payload": _error_payload("/render/capture", "io_error", "Failed to create capture directory")}
	var timestamp := Time.get_unix_time_from_system()
	var local_path := "%s/capture_%d.png" % [capture_dir, timestamp]
	var save_err := image.save_png(local_path)
	if save_err != OK:
		return {"status": 500, "payload": _error_payload("/render/capture", "io_error", "Failed to save PNG capture")}

	return {
		"status": 200,
		"payload": {
			"ok": true,
			"image_path": ProjectSettings.globalize_path(local_path),
			"width": width,
			"height": height,
			"timestamp": timestamp
		}
	}


func _handle_render_interact(payload: Dictionary) -> Dictionary:
	var mode := str(payload.get("mode", ""))
	var interaction_payload := payload.get("payload", {})
	if not (interaction_payload is Dictionary):
		return {"status": 400, "payload": _error_payload("/render/interact", "validation_error", "payload must be an object")}
	match mode:
		"mouse_click":
			return _render_mouse_click(interaction_payload)
		"key_press":
			return _render_key_press(interaction_payload)
		"camera_orbit":
			return _render_camera_orbit(interaction_payload)
		_:
			return {"status": 400, "payload": _error_payload("/render/interact", "validation_error", "Unsupported interaction mode")}


func _render_mouse_click(payload: Dictionary) -> Dictionary:
	if not payload.has("x") or not payload.has("y"):
		return {"status": 400, "payload": _error_payload("/render/interact", "validation_error", "x and y are required")}
	var x := float(payload.get("x", 0))
	var y := float(payload.get("y", 0))
	var button := int(payload.get("button", CLICK_BUTTON_LEFT))
	var pressed := InputEventMouseButton.new()
	pressed.position = Vector2(x, y)
	pressed.button_index = button
	pressed.pressed = true
	Input.parse_input_event(pressed)
	var released := InputEventMouseButton.new()
	released.position = Vector2(x, y)
	released.button_index = button
	released.pressed = false
	Input.parse_input_event(released)
	return {"status": 200, "payload": {"ok": true, "details": {"mode": "mouse_click", "x": x, "y": y, "button": button}}}


func _render_key_press(payload: Dictionary) -> Dictionary:
	if not payload.has("keycode"):
		return {"status": 400, "payload": _error_payload("/render/interact", "validation_error", "keycode is required")}
	var keycode := int(payload.get("keycode", 0))
	var press := InputEventKey.new()
	press.keycode = keycode
	press.pressed = true
	_apply_modifiers(press, payload.get("mods", {}))
	Input.parse_input_event(press)
	var release := InputEventKey.new()
	release.keycode = keycode
	release.pressed = false
	_apply_modifiers(release, payload.get("mods", {}))
	Input.parse_input_event(release)
	return {"status": 200, "payload": {"ok": true, "details": {"mode": "key_press", "keycode": keycode}}}


func _render_camera_orbit(payload: Dictionary) -> Dictionary:
	if not payload.has("dx") or not payload.has("dy"):
		return {"status": 400, "payload": _error_payload("/render/interact", "validation_error", "dx and dy are required")}
	var dx := float(payload.get("dx", 0.0))
	var dy := float(payload.get("dy", 0.0))
	var sensitivity := float(payload.get("sensitivity", CAMERA_ORBIT_SENSITIVITY_DEFAULT))
	var camera := _resolve_camera(payload)
	if camera == null:
		return {"status": 404, "payload": _error_payload("/render/interact", "node_not_found", "Camera not found")}
	camera.rotate_y(-dx * sensitivity)
	camera.rotate_object_local(Vector3.RIGHT, -dy * sensitivity)
	return {
		"status": 200,
		"payload": {
			"ok": true,
			"details": {"mode": "camera_orbit", "dx": dx, "dy": dy, "sensitivity": sensitivity, "camera_path": str(camera.get_path())}
		}
	}


func _resolve_camera(payload: Dictionary) -> Camera3D:
	var camera_path := str(payload.get("camera_path", ""))
	if camera_path != "":
		var node := get_tree().current_scene.get_node_or_null(camera_path) if get_tree().current_scene else null
		if node is Camera3D:
			return node
	var viewport_camera := get_viewport().get_camera_3d()
	if viewport_camera is Camera3D:
		return viewport_camera
	return null


func _apply_modifiers(event: InputEventKey, raw_mods: Variant) -> void:
	if not (raw_mods is Dictionary):
		return
	event.shift_pressed = bool(raw_mods.get("shift", false))
	event.ctrl_pressed = bool(raw_mods.get("ctrl", false))
	event.alt_pressed = bool(raw_mods.get("alt", false))
	event.meta_pressed = bool(raw_mods.get("meta", false))


func _normalize_res_path(raw_path: String, default_extension: String = "") -> String:
	var path := raw_path.strip_edges()
	if path == "":
		return ""
	if not path.begins_with("res://"):
		path = "res://%s" % [path.trim_prefix("/")]
	if default_extension != "" and path.get_extension() == "":
		path = "%s%s" % [path, default_extension]
	return path


func _instantiate_node(node_type: String) -> Node:
	if not ClassDB.class_exists(node_type):
		return null
	var value: Variant = ClassDB.instantiate(node_type)
	if value is Node:
		return value
	return null


func _load_scene_root(scene_path: String) -> Dictionary:
	if not ResourceLoader.exists(scene_path):
		return {"status": 404, "payload": _error_payload("/scene", "scene_not_found", "Scene file not found")}
	var packed := ResourceLoader.load(scene_path)
	if packed == null or not (packed is PackedScene):
		return {"status": 400, "payload": _error_payload("/scene", "invalid_scene", "Scene is not a PackedScene")}
	var root := packed.instantiate()
	if root == null:
		return {"status": 500, "payload": _error_payload("/scene", "scene_load_failed", "Failed to instantiate scene")}
	return {"status": 200, "root": root}


func _save_scene_root(root: Node, scene_path: String) -> Dictionary:
	var dir_err := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(scene_path.get_base_dir()))
	if dir_err != OK:
		root.queue_free()
		return {"status": 500, "payload": _error_payload("/scene", "io_error", "Failed to create scene directory")}
	var packed := PackedScene.new()
	var err_pack := packed.pack(root)
	root.queue_free()
	if err_pack != OK:
		return {"status": 500, "payload": _error_payload("/scene", "pack_error", "Failed to pack scene")}
	var err_save := ResourceSaver.save(packed, scene_path)
	if err_save != OK:
		return {"status": 500, "payload": _error_payload("/scene", "io_error", "Failed to save scene")}
	return {"status": 200}


func _resolve_node(root: Node, node_path: String) -> Node:
	if node_path.strip_edges() == "" or node_path == "." or node_path == root.name:
		return root
	return root.get_node_or_null(node_path)


func _apply_node_properties(node: Node, raw_properties: Variant) -> void:
	if not (raw_properties is Dictionary):
		return
	for key in raw_properties.keys():
		_set_node_property(node, str(key), raw_properties[key])


func _set_node_property(node: Node, property_name: String, property_value: Variant) -> bool:
	for property_info in node.get_property_list():
		if str(property_info.get("name", "")) == property_name:
			node.set(property_name, property_value)
			return true
	return false


func _collect_mesh_nodes(root: Node) -> Array[MeshInstance3D]:
	var results: Array[MeshInstance3D] = []
	var stack: Array[Node] = [root]
	while stack.size() > 0:
		var current := stack.pop_back()
		if current is MeshInstance3D and current.mesh != null:
			results.append(current)
		for child in current.get_children():
			if child is Node:
				stack.append(child)
	return results


func _is_token_valid(headers: Dictionary) -> bool:
	var auth_header: String = str(headers.get("authorization", ""))
	if not auth_header.begins_with("Bearer "):
		return false
	var provided_token := auth_header.substr(7).strip_edges()
	return provided_token != "" and provided_token == _token


func _parse_http_request(raw_request: String) -> Dictionary:
	var sections := raw_request.split("\r\n\r\n", true, 1)
	if sections.is_empty():
		return {}
	var header_block: String = sections[0]
	var body := sections[1] if sections.size() > 1 else ""
	var lines := header_block.split("\r\n")
	if lines.is_empty():
		return {}
	var request_line := lines[0].split(" ")
	if request_line.size() < 2:
		return {}
	var headers := {}
	for i in range(1, lines.size()):
		var line: String = lines[i]
		var split_at := line.find(":")
		if split_at <= 0:
			continue
		var key := line.substr(0, split_at).strip_edges().to_lower()
		var value := line.substr(split_at + 1).strip_edges()
		headers[key] = value
	return {"method": request_line[0].to_upper(), "path": request_line[1], "headers": headers, "body": body}


func _read_http_request(peer: StreamPeerTCP, timeout_ms: int) -> String:
	var deadline := Time.get_ticks_msec() + timeout_ms
	var raw := ""
	while Time.get_ticks_msec() < deadline:
		peer.poll()
		var available := peer.get_available_bytes()
		if available > 0:
			raw += peer.get_utf8_string(available)
			if _http_request_complete(raw):
				return raw
		OS.delay_msec(5)
	return raw


func _http_request_complete(raw: String) -> bool:
	var separator := raw.find("\r\n\r\n")
	if separator == -1:
		return false
	var header_block := raw.substr(0, separator)
	var body := raw.substr(separator + 4)
	var content_length := _extract_content_length(header_block)
	if content_length <= 0:
		return true
	return body.to_utf8_buffer().size() >= content_length


func _extract_content_length(header_block: String) -> int:
	for line in header_block.split("\r\n"):
		var split_at := line.find(":")
		if split_at <= 0:
			continue
		var key := line.substr(0, split_at).strip_edges().to_lower()
		if key != "content-length":
			continue
		var value := line.substr(split_at + 1).strip_edges()
		if value.is_valid_int():
			return int(value)
		return 0
	return 0


func _send_json_response(peer: StreamPeerTCP, status_code: int, payload: Dictionary) -> void:
	var body := JSON.stringify(payload)
	var status_text := STATUS_TEXT.get(status_code, "OK")
	var response := "HTTP/1.1 %d %s\r\n" % [status_code, status_text]
	response += "Content-Type: %s\r\n" % CONTENT_TYPE_JSON
	response += "Content-Length: %d\r\n" % body.length()
	response += "Connection: close\r\n\r\n"
	response += body
	peer.put_data(response.to_utf8_buffer())
	peer.disconnect_from_host()


func _error_payload(route: String, code: String, message: String) -> Dictionary:
	return {"ok": false, "route": route, "error": {"code": code, "message": message}}
