import { useState } from "react";

import Plot from "react-plotly.js";
import { useResizeDetector } from "react-resize-detector";

import vl_sample_image_b64 from "../assets/vl_sample_image.base64?raw";

export default function ImageOutput() {
  const { width, height, ref } = useResizeDetector({
    // refreshMode: 'debounce',
    // refreshRate: 1000
  });
  const [dataURI, setdataURI] = useState(vl_sample_image_b64);

  const update = (value) => {
    setdataURI(value);
  };
  window.updateImageOutput = update;

  return (
    <div ref={ref} style={{ display: "flex", height: "100%" }}>
      <Plot
        data={[]}
        layout={{
          plot_bgcolor: "black",
          dragmode: "zoom",
          margin: { t: 0, l: 0, r: 0, b: 0 },
          xaxis: { visible: false, range: [0, 1] },
          yaxis: { visible: false, range: [0, 1], scaleanchor: "x" },
          width: width,
          height: height,
          images: [
            {
              source: dataURI,
              xref: "x",
              yref: "y",
              x: 0,
              y: 0,
              sizex: 1.1,
              sizey: 1.1,
              xanchor: "left",
              yanchor: "bottom",
              sizing: "stretch",
            },
          ],
        }}
        config={{
          displaylogo: false,
          responsive: true,
          autosize: true,
          useResizeHandler: true,
        }}
        useResizeHandler={true}
        style={{
          height: "100%",
          width: "100%",
          overflow: "hidden",
        }}
      />
    </div>
  );
}
