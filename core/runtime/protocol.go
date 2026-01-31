package main

// ToolRequest defines the strict contract for invoking a tool.
type ToolRequest struct {
	ID        string                 `json:"id"`
	ToolName  string                 `json:"tool_name"`
	Arguments map[string]interface{} `json:"arguments"`
}

// ToolResponse defines the strict contract for tool output.
type ToolResponse struct {
	ID        string `json:"id"`
	Result    string `json:"result,omitempty"`
	Error     string `json:"error,omitempty"`
	Status    string `json:"status"` // "success", "error"
	Timestamp int64  `json:"timestamp"`
}
