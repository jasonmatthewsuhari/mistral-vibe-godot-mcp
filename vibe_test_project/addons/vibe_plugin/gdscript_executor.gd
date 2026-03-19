@tool
extends RefCounted

static func execute(code: String) -> Error:
	var script := GDScript.new()
	script.source_code = code
	var err := script.reload()
	if err != OK:
		push_error("Vibe: GDScript compile error: %s" % error_string(err))
		return err
	var instance = script.new()
	if instance.has_method("run"):
		instance.run()
	instance.free()
	return OK
