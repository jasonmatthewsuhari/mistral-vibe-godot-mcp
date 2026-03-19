@tool
extends AcceptDialog

signal prompt_confirmed(text: String)

var _text_edit: TextEdit


func _init() -> void:
	title = "Vibe Prompt"
	size = Vector2i(480, 200)
	_text_edit = TextEdit.new()
	_text_edit.placeholder_text = "Enter your prompt..."
	_text_edit.custom_minimum_size = Vector2i(460, 120)
	add_child(_text_edit)
	confirmed.connect(_on_confirmed)
	canceled.connect(queue_free)


func _on_confirmed() -> void:
	var text := _text_edit.text.strip_edges()
	if text.is_empty():
		return
	prompt_confirmed.emit(text)
	queue_free()
