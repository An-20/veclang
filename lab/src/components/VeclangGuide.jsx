import ReactMarkdown from "react-markdown";
import vl_program_txt from "../assets/veclang_guide.md?raw";

export default function VeclangGuide() {
  return (
    <div
      style={{
        padding: "10px",
        overflowY: "scroll",
        height: "100%",
      }}
    >
      <ReactMarkdown>{vl_program_txt}</ReactMarkdown>
    </div>
  );
}
