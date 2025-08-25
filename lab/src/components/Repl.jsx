import React, { useState, useRef, useEffect } from "react";

function balanced(code) {
  let parenDepth = 0;
  let braceDepth = 0;
  for (let c of code) {
    if (c === "(") parenDepth++;
    else if (c === ")") parenDepth--;
    else if (c === "{") braceDepth++;
    else if (c === "}") braceDepth--;
    if (parenDepth < 0 || braceDepth < 0) return false;
  }
  return parenDepth === 0 && braceDepth === 0;
}

export default function Repl() {
  // basically a copy of TextOutput with slightly different formatting
  const [input, setInput] = useState("");
  const [output, setOutput] = useState([
    {
      type: "stdout",
      text: "Veclang v2.0.0, compiler v1.0.0, bc_interpreter_wasm",
    },
    {
      type: "stdout",
      text: "Veclang REPL",
    },
  ]);
  const inputRef = useRef(null);
  const endRef = useRef(null);

  const writeStdout = (text) => {
    const newLines = text.split(/\r?\n/);
    const formattedLines = newLines.map((line) => ({
      type: "stdout",
      text: line,
    }));
    setOutput((prev) => [...prev, ...formattedLines]);
  };

  const writeStderr = (text) => {
    const newLines = text.split(/\r?\n/);
    const formattedLines = newLines.map((line) => ({
      type: "stderr",
      text: line,
    }));
    setOutput((prev) => [...prev, ...formattedLines]);
  };

  // will fix one day lol
  window[`replOutput`] = {
    writeStdout,
    writeStderr,
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (balanced(input) || e.ctrlKey) {
        setInput("");
        writeStdout(`>>> ${input}`);
        window.compile_program_repl(input);
      } else {
        setInput((prev) => prev + "\n");
      }
    }
  };

  // Auto-scroll output
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [output]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        background: "#111",
        color: "#fff",
        fontFamily: "monospace",
        borderRadius: "6px",
      }}
    >
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          background: "#000",
          padding: "2px",
          borderRadius: "4px",
          fontSize: "14px",
        }}
      >
        {output.map((line, i) => {
          if (line.type === "stdout") {
            return (
              <div key={i} style={{ color: "#dddddd", marginLeft: "10px" }}>
                {line.text}
              </div>
            );
          } else {
            let style = { marginLeft: "10px" };

            // Only color "error" or "warning" at the start of the line
            const errorMatch = line.text.match(/^(error)\b/i);
            const warningMatch = line.text.match(/^(warning)\b/i);

            if (errorMatch) {
              return (
                <div key={i} style={{ ...style, color: "#fffff" }}>
                  <span style={{ color: "red" }}>{errorMatch[1]}</span>
                  {line.text.slice(errorMatch[1].length)}
                </div>
              );
            } else if (warningMatch) {
              return (
                <div key={i} style={{ ...style, color: "#ffffff" }}>
                  <span style={{ color: "yellow" }}>{warningMatch[1]}</span>
                  {line.text.slice(warningMatch[1].length)}
                </div>
              );
            } else {
              return (
                <div key={i} style={{ ...style, color: "#ffffff" }}>
                  {line.text}
                </div>
              );
            }
          }
        })}
        <div ref={endRef} />
      </div>

      <div style={{ position: "relative" }}>
        <textarea
          ref={inputRef}
          style={{
            width: "100%",
            height: "3em",
            overflow: "auto",
            borderRadius: "4px",
            border: "none",
            background: "#111",
            color: "#ffffff",
            fontFamily: "monospace",
            fontSize: "14px",
            resize: "none",
            outline: "none",
          }}
          rows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type code here... (Shift+Enter for newline, Enter to submit)"
        />
      </div>
    </div>
  );
}
