package main

import (
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

// Whitelist defines allowed commands
var allowedCommands = map[string]bool{
	"ls":      true,
	"cat":     true,
	"grep":    true,
	"git":     true,
	"echo":    true,
	"find":    true,
    "pwd":     true,
    "whoami":  true,
    "date":    true,
    "python3": true, // Riskier, but needed for agents.
    "go":      true,
    "docker":  true, // Useful for containment
    "curl":    true,
    "mkdir":   true,
    "bash":    true,

    // File Ops
    "cp":      true,
    "mv":      true,
    "touch":   true,
    "tar":     true,
    "unzip":   true,
    
    // Text Processing
    "head":    true,
    "tail":    true,
    "sed":     true,
    "awk":     true,
    "diff":    true,
    
    // Network
    "wget":    true,
    "ping":    true,
    
    // Dev Stack
    "node":    true,
    "npm":     true,
    "npx":     true,
    "make":    true,
    "gcc":     true,
    "g++":     true,

    "rm":      false, // EXPLICITLY BLOCKED
    "sudo":    false, // EXPLICITLY BLOCKED
}

type ShellExecutor struct {
    DefaultCwd string
}

func NewShellExecutor(cwd string) *ShellExecutor {
    return &ShellExecutor{DefaultCwd: cwd}
}

func (s *ShellExecutor) Execute(command string, args []string, cwd string) (string, error) {
    if !allowedCommands[command] {
        return "", fmt.Errorf("Command '%s' is NOT in the Allowed Whitelist. Access Denied.", command)
    }

    // Extra Safety Checks on Args
    for _, arg := range args {
        if strings.Contains(arg, "../..") {
            return "", fmt.Errorf("Path traversal detected in args. Access Denied.")
        }
        if arg == "&" || arg == ";" || arg == "|" {
            return "", fmt.Errorf("Shell chaining operators detected. Access Denied. Use single commands.")
        }
    }

    cmd := exec.Command(command, args...)
    
    // Set Working Directory
    if cwd != "" {
        cmd.Dir = cwd
    } else {
        cmd.Dir = s.DefaultCwd
    }

    var stdout, stderr bytes.Buffer
    cmd.Stdout = &stdout
    cmd.Stderr = &stderr

    err := cmd.Run()
    
    output := stdout.String()
    if stderr.Len() > 0 {
        output += "\n[STDERR]: " + stderr.String()
    }

    if err != nil {
        return output, fmt.Errorf("Exit Code %v: %s", err, output)
    }

    return output, nil
}
