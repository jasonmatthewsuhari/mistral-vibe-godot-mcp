@tool
extends EditorPlugin

const FilesystemContextMenuScript := preload("res://addons/vibe_plugin/filesystem_context_menu.gd")
const SceneTreeContextMenuScript := preload("res://addons/vibe_plugin/scene_tree_context_menu.gd")

var _fs_menu: EditorContextMenuPlugin
var _tree_menu: EditorContextMenuPlugin


func _enter_tree() -> void:
	_fs_menu = FilesystemContextMenuScript.new()
	_tree_menu = SceneTreeContextMenuScript.new()
	add_context_menu_plugin(EditorContextMenuPlugin.CONTEXT_SLOT_FILESYSTEM, _fs_menu)
	add_context_menu_plugin(EditorContextMenuPlugin.CONTEXT_SLOT_SCENE_TREE, _tree_menu)


func _exit_tree() -> void:
	if _fs_menu:
		remove_context_menu_plugin(_fs_menu)
		_fs_menu = null
	if _tree_menu:
		remove_context_menu_plugin(_tree_menu)
		_tree_menu = null
