@tool
extends EditorContextMenuPlugin

const VibePromptDialogScript := preload("res://addons/vibe_plugin/vibe_prompt_dialog.gd")
const VibeHTTPHelperScript := preload("res://addons/vibe_plugin/vibe_http_helper.gd")

const BACKEND_URL := "http://localhost:8765"


func _popup_menu(paths: PackedStringArray) -> void:
	if paths.size() != 1:
		return
	var path: String = paths[0]
	var abs := ProjectSettings.globalize_path(path)
	if DirAccess.dir_exists_absolute(abs):
		add_context_menu_item("Vibe: Generate Asset", func(_p): _on_generate(path, abs))
	elif path.get_extension().to_lower() in ["png", "jpg", "webp"]:
		add_context_menu_item("Vibe: Modify Asset", func(_p): _on_modify(path, abs))


func _on_generate(res_path: String, abs_path: String) -> void:
	_show_prompt("Vibe: Generate Asset", func(text: String): _do_generate(text, abs_path))


func _on_modify(res_path: String, abs_path: String) -> void:
	_show_prompt("Vibe: Modify Asset", func(text: String): _do_modify(text, res_path, abs_path))


func _show_prompt(title: String, callback: Callable) -> void:
	var dialog: AcceptDialog = VibePromptDialogScript.new()
	dialog.title = title
	EditorInterface.get_base_control().add_child(dialog)
	dialog.prompt_confirmed.connect(callback)
	dialog.popup_centered()


func _do_generate(prompt_text: String, abs_folder: String) -> void:
	var loading := _show_loading("Generating asset...")
	var helper: Node = VibeHTTPHelperScript.new()
	EditorInterface.get_base_control().add_child(helper)
	helper.request_completed.connect(func(ok: bool, body: Dictionary) -> void:
		loading.queue_free()
		if ok:
			EditorInterface.get_resource_filesystem().scan()
		else:
			_show_error("Generate failed: %s" % str(body.get("detail", "Unknown error")))
		helper.queue_free()
	)
	helper.post_json(BACKEND_URL + "/generate-asset", {
		"prompt": prompt_text,
		"folder_path": abs_folder,
	})


func _do_modify(prompt_text: String, res_path: String, abs_path: String) -> void:
	var raw_bytes := FileAccess.get_file_as_bytes(res_path)
	if raw_bytes.is_empty():
		_show_error("Could not read file: %s" % res_path)
		return
	var b64 := Marshalls.raw_to_base64(raw_bytes)

	var loading := _show_loading("Modifying asset...")
	var helper: Node = VibeHTTPHelperScript.new()
	EditorInterface.get_base_control().add_child(helper)
	helper.request_completed.connect(func(ok: bool, body: Dictionary) -> void:
		loading.queue_free()
		if ok:
			EditorInterface.get_resource_filesystem().scan()
		else:
			_show_error("Modify failed: %s" % str(body.get("detail", "Unknown error")))
		helper.queue_free()
	)
	helper.post_json(BACKEND_URL + "/modify-asset", {
		"prompt": prompt_text,
		"file_path": abs_path,
		"image_base64": b64,
	})


func _show_loading(message: String) -> AcceptDialog:
	var dlg := AcceptDialog.new()
	dlg.title = "Vibe Plugin"
	dlg.dialog_text = message
	dlg.get_ok_button().hide()
	EditorInterface.get_base_control().add_child(dlg)
	dlg.popup_centered()
	return dlg


func _show_error(message: String) -> void:
	var dlg := AcceptDialog.new()
	dlg.title = "Vibe Plugin Error"
	dlg.dialog_text = message
	EditorInterface.get_base_control().add_child(dlg)
	dlg.popup_centered()
	dlg.confirmed.connect(dlg.queue_free)
