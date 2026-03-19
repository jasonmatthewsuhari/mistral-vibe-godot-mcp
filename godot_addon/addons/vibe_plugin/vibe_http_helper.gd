@tool
extends Node

signal request_completed(ok: bool, body: Dictionary)

var _http: HTTPRequest


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_raw_completed)


func post_json(url: String, payload: Dictionary) -> void:
	var body := JSON.stringify(payload)
	var headers := PackedStringArray(["Content-Type: application/json"])
	var err := _http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		request_completed.emit(false, {"detail": "HTTPRequest failed: %s" % error_string(err)})


func _on_raw_completed(
		result: int,
		response_code: int,
		_headers: PackedStringArray,
		body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		request_completed.emit(false, {"detail": "Network error (result %d)" % result})
		return

	var text := body.get_string_from_utf8()
	var parsed = JSON.parse_string(text)
	if parsed == null:
		request_completed.emit(false, {"detail": "Invalid JSON response"})
		return

	var ok: bool = response_code >= 200 and response_code < 300
	request_completed.emit(ok, parsed if parsed is Dictionary else {"detail": str(parsed)})
