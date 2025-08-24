import { createContext, useContext, useState, useRef, useEffect } from "react";

export const TextOutputContext = createContext();

export default function TextOutput({ outputName }) {
  const [lines, setLines] = useState([]);
  const endRef = useRef(null);

  const appendLine = (line) => setLines((prev) => [...prev, line]);
  const appendLines = (text) => {
    const newLines = text.split(/\r?\n/); // handles \n and \r\n
    setLines((prev) => [...prev, ...newLines]);
  };
  const clear = () => setLines([]);

  // Auto-scroll on new lines
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [lines]);

  window[`${outputName}Output`] = {
    appendLine,
    appendLines,
    clear,
  };

  return (
    <TextOutputContext.Provider
      value={{ lines, appendLine, appendLines, clear }}
    >
      <div
        style={{
          background: "#111",
          color: "#fff",
          fontFamily: "monospace",
          fontSize: "14px",
          padding: "10px",
          width: "100%",
          height: "100%",
          overflowY: "scroll",
          borderRadius: "6px",
          whiteSpace: "pre-wrap",
        }}
      >
        {lines.map((line, i) => (
          <div style={{ marginLeft: "10px" }} key={i}>
            {line}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </TextOutputContext.Provider>
  );
}

export function useTerminal() {
  const context = useContext(TerminalContext);
  if (!context)
    throw new Error("useTerminal must be used inside TerminalProvider");
  return context;
}
