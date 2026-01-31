package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
	"os"
	"path/filepath"
	"strings"
)


func validatePath(path string) (string, error) {
	if path == "" {
		return "", fmt.Errorf("Missing or invalid 'path' argument")
	}
	absPath, err := filepath.Abs(path)
	if err != nil {
		return "", fmt.Errorf("Invalid path")
	}
	baseDir := "/home/holloway/ziva" // HARDCODED SANDBOX ROOT
	if !strings.HasPrefix(absPath, baseDir) {
		return "", fmt.Errorf("Access Denied: Path '%s' is outside sandbox '%s'", path, baseDir)
	}
	return absPath, nil
}

func handleExecute(w http.ResponseWriter, r *http.Request) {
    // ... (method check and decoding remains, usually implied unless I replace whole func)
    // To be safe and clean, I will rewrite the switch block mostly.
    
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req ToolRequest
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	log.Printf("📥 Received Tool Request: %s (%s)", req.ToolName, req.ID)

	resp := ToolResponse{
		ID:        req.ID,
		Status:    "error",
		Timestamp: time.Now().Unix(),
	}

	switch req.ToolName {
	case "ping":
		resp.Status = "success"
		resp.Result = "pong"
        
	case "read_file":
		path, _ := req.Arguments["path"].(string)
		absPath, err := validatePath(path)
		if err != nil {
			resp.Error = err.Error()
			break
		}
		
		content, err := os.ReadFile(absPath)
		if err != nil {
			resp.Error = fmt.Sprintf("Read Error: %v", err)
			break
		}
		resp.Result = string(content)
		resp.Status = "success"

	case "write_file":
		path, _ := req.Arguments["path"].(string)
		content, _ := req.Arguments["content"].(string)
		// mode: "overwrite" (default) or "append"
		mode, _ := req.Arguments["mode"].(string) 
		
		absPath, err := validatePath(path)
		if err != nil {
			resp.Error = err.Error()
			break
		}
		
		// Ensure dir exists
		if err := os.MkdirAll(filepath.Dir(absPath), 0755); err != nil {
            resp.Error = fmt.Sprintf("Dir Creation Error: %v", err)
            break
        }

		flag := os.O_WRONLY | os.O_CREATE | os.O_TRUNC
		if mode == "append" {
			flag = os.O_WRONLY | os.O_CREATE | os.O_APPEND
		}
		
		f, err := os.OpenFile(absPath, flag, 0644)
		if err != nil {
			resp.Error = fmt.Sprintf("File Open Error: %v", err)
			break
		}
		_, err = f.WriteString(content)
		f.Close()
		
		if err != nil {
			resp.Error = fmt.Sprintf("Write Error: %v", err)
			break
		}
		resp.Status = "success"
		resp.Result = fmt.Sprintf("Successfully wrote to %s (mode: %s)", path, mode)


	case "execute_shell":
        // Parse Args
        cmdName, _ := req.Arguments["command"].(string)
        
        // JSON arrays come as []interface{}, need conversion
        var args []string
        if rawArgs, ok := req.Arguments["args"].([]interface{}); ok {
            for _, v := range rawArgs {
                if s, ok := v.(string); ok {
                    args = append(args, s)
                }
            }
        }
        
        cwd, _ := req.Arguments["cwd"].(string)
        
        // Validate CWD if provided
        if cwd != "" {
            validCwd, err := validatePath(cwd)
             if err != nil {
                 resp.Error = err.Error()
                 break
             }
             // Success
             cwd = validCwd 
        }


        executor := NewShellExecutor("/home/holloway/ziva")
        if executor == nil {
            log.Println("❌ CRITICAL: executor is nil!")
            resp.Error = "Internal Server Error"
            break
        }
        
        output, err := executor.Execute(cmdName, args, cwd)

        
        resp.Result = output
        if err != nil {
            resp.Error = err.Error()
            // Don't set status error if we got output (exit code != 0 is common)
            // But usually validation error is fatal.
            // Let's rely on Error field.
            resp.Status = "error"
        } else {
            resp.Status = "success"
        }


	case "run_container":
		image, _ := req.Arguments["image"].(string)
		
		// Parse Command Args
		var cmdArgs []string
		if rawArgs, ok := req.Arguments["args"].([]interface{}); ok {
			for _, v := range rawArgs {
				if s, ok := v.(string); ok {
					cmdArgs = append(cmdArgs, s)
				}
			}
		}

        // Parse Env Vars
        envVars := make(map[string]string)
        if rawEnv, ok := req.Arguments["env"].(map[string]interface{}); ok {
            for k, v := range rawEnv {
                if s, ok := v.(string); ok {
                    envVars[k] = s
                }
            }
        }
        
        allowNetwork, _ := req.Arguments["allow_network"].(bool)

        runner := NewContainerRunner("/home/holloway/ziva")
        output, err := runner.Run(image, cmdArgs, envVars, allowNetwork)
        
        resp.Result = output
        if err != nil {
            resp.Error = err.Error()
            resp.Status = "error"
        } else {
            resp.Status = "success"
        }

	default:
		resp.Error = fmt.Sprintf("Tool '%s' not implemented in Go Runtime yet.", req.ToolName)
	}

	w.Header().Set("Content-Type", "application/json")

	json.NewEncoder(w).Encode(resp)
	
	resultLog := "✅ Success"
	if resp.Status != "success" {
		resultLog = "❌ Failed: " + resp.Error
	}
	log.Printf("📤 Sent Response: %s", resultLog)
}


func main() {
	http.HandleFunc("/execute", handleExecute)
    // ... rest of main logic (ensure imports are correct)


	port := ":8090"
	log.Printf("🛡️ Ziva Go Runtime (The Body) listening on %s", port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}
