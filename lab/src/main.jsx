import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createTheme, ThemeProvider } from "@mui/material/styles";

import "./index.css";

import CodeEditor from "./components/CodeEditor";
import VeclangGuide from "./components/VeclangGuide";
import OptionsMenu from "./components/OptionsMenu";
import Repl from "./components/Repl";
import TextOutput from "./components/TextOutput";
import ImageOutput from "./components/ImageOutput";
import ImageGallery from "./components/ImageGallery";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#f48500",
      light: "#ffc052ff",
      dark: "#b6550a",
    },
  },
});

window.startReactApp = function () {
  createRoot(document.getElementById("codeEditorRoot")).render(
    <StrictMode>
      <CodeEditor />
    </StrictMode>
  );

  createRoot(document.getElementById("replRoot")).render(
    <StrictMode>
      <Repl />
    </StrictMode>
  );

  createRoot(document.getElementById("veclangGuideRoot")).render(
    <StrictMode>
      <VeclangGuide />
    </StrictMode>
  );

  createRoot(document.getElementById("optionsMenuRoot")).render(
    <StrictMode>
      <ThemeProvider theme={theme}>
        <OptionsMenu />
      </ThemeProvider>
    </StrictMode>
  );

  createRoot(document.getElementById("textOutputRoot")).render(
    <StrictMode>
      <TextOutput outputName="txt"></TextOutput>
    </StrictMode>
  );

  createRoot(document.getElementById("headerOutputRoot")).render(
    <StrictMode>
      <TextOutput outputName="header"></TextOutput>
    </StrictMode>
  );

  createRoot(document.getElementById("disOutputRoot")).render(
    <StrictMode>
      <TextOutput outputName="dis"></TextOutput>
    </StrictMode>
  );

  createRoot(document.getElementById("imageOutputRoot")).render(
    <StrictMode>
      <ImageOutput></ImageOutput>
    </StrictMode>
  );

  createRoot(document.getElementById("imageGalleryRoot")).render(
    <StrictMode>
      <ThemeProvider theme={theme}>
        <ImageGallery />
      </ThemeProvider>
    </StrictMode>
  );
};
