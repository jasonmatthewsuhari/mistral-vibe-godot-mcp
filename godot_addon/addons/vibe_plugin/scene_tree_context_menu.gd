@tool
extends EditorContextMenuPlugin

const VibePromptDialogScript := preload("res://addons/vibe_plugin/vibe_prompt_dialog.gd")
const VibeHTTPHelperScript := preload("res://addons/vibe_plugin/vibe_http_helper.gd")
const GDScriptExecutorScript := preload("res://addons/vibe_plugin/gdscript_executor.gd")

const BACKEND_URL := "http://localhost:8765"


func _popup_menu(paths: PackedStringArray) -> void:
	if paths.size() != 1:
		return
	var node_path := paths[0]
	add_context_menu_item("Vibe: Automate", func(_p): _on_automate(node_path))


func _on_automate(node_path: String) -> void:
	var dialog: AcceptDialog = VibePromptDialogScript.new()
	dialog.title = "Vibe: Automate"
	EditorInterface.get_base_control().add_child(dialog)
	dialog.prompt_confirmed.connect(func(prompt_text: String) -> void:
		_do_automate(prompt_text, node_path)
	)
	dialog.popup_centered()


func _do_automate(instruction: String, node_path: String) -> void:
	var helper: Node = VibeHTTPHelperScript.new()
	EditorInterface.get_base_control().add_child(helper)
	helper.request_completed.connect(func(ok: bool, body: Dictionary) -> void:
		if ok:
			var code: String = body.get("gdscript_code", "")
			if code.is_empty():
				_show_error("LLM returned empty script")
			else:
				var err := GDScriptExecutorScript.execute(code)
				if err != OK:
					_show_error("Script execution error: %s" % error_string(err))
		else:
			_show_error("Automate failed: %s" % str(body.get("detail", "Unknown error")))
		helper.queue_free()
	)
	helper.post_json(BACKEND_URL + "/automate", {
		"instruction": instruction,
		"node_info": node_path,
	})


func _show_error(message: String) -> void:
	var dlg := AcceptDialog.new()
	dlg.title = "Vibe Plugin Error"
	dlg.dialog_text = message
	EditorInterface.get_base_control().add_child(dlg)
	dlg.popup_centered()
	dlg.confirmed.connect(dlg.queue_free)
