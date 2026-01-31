package main

import (
	"bytes"
	"fmt"
	"os/exec"
	"path/filepath"
)

type ContainerRunner struct {
    WorkspaceRoot string
}

func NewContainerRunner(root string) *ContainerRunner {
    return &ContainerRunner{WorkspaceRoot: root}
}

func (c *ContainerRunner) Run(image string, cmdArgs []string, envVars map[string]string, allowNetwork bool) (string, error) {
    if image == "" {
        return "", fmt.Errorf("Image name cannot be empty")
    }

    // Prepare Docker Command
    // docker run --rm -i ...
    
    // Construct Volume Path
    absTmpPath := filepath.Join(c.WorkspaceRoot, "tmp")
    
    netMode := "none"
    if allowNetwork {
        netMode = "bridge" // or "host" if needed, usually bridge is safer default with internet
    }

    dockerArgs := []string{
        "run",
        "--rm",             // Ephemeral
        "-i",               // Interactive 
        "--network", netMode, 

        "--cpus", "1.0",
        "--memory", "512m",
        "-w", "/workspace",
        "-v", fmt.Sprintf("%s:/workspace", absTmpPath),
    }

    // Add Env Vars
    for k, v := range envVars {
        dockerArgs = append(dockerArgs, "-e", fmt.Sprintf("%s=%s", k, v))
    }

    dockerArgs = append(dockerArgs, image)
    dockerArgs = append(dockerArgs, cmdArgs...)

    cmd := exec.Command("docker", dockerArgs...)

    var stdout, stderr bytes.Buffer
    cmd.Stdout = &stdout
    cmd.Stderr = &stderr

    err := cmd.Run()
    output := stdout.String()
    if stderr.Len() > 0 {
        output += "\n[STDERR]: " + stderr.String()
    }

    if err != nil {
        return output, fmt.Errorf("Container Error: %v\nOutput: %s", err, output)
    }

    return output, nil
}
