let moduleInstance = null;
var Module = {
  onRuntimeInitialized: function () {
    moduleInstance = Module;
    console.log("veclang.wasm module loaded");
  },
};

function vectorFromUint8Array(uint8arr) {
  const vec = new Module["vector_uint8"]();
  for (let i = 0; i < uint8arr.length; i++) {
    vec.push_back(uint8arr[i]);
  }
  return vec;
}

function vectorToUint8Array(vec) {
  const length = vec.size();
  const arr = new Uint8Array(length);
  for (let i = 0; i < length; i++) {
    arr[i] = vec.get(i);
  }
  return arr;
}

function handleProgramBytes(jsArray) {
  window.programBytes = new Uint8Array(jsArray);
}

function runProgram(imageResolution) {
  x = vectorFromUint8Array(window.programBytes);
  y = moduleInstance.generate_img(x, imageResolution);
  z = vectorToUint8Array(y);
  const blob = new Blob([z], { type: "image/bmp" });
  const reader = new FileReader();
  reader.onload = function () {
    const dataUrl = reader.result;
    window.dataUrl = dataUrl;
    window.updateImageOutput(dataUrl);
    window.addImageToGallery(dataUrl);
  };
  reader.readAsDataURL(blob);
}

var config = {
  settings: {
    showPopoutIcon: false,
    showMaximiseIcon: false,
    showCloseIcon: false,
  },

  content: [
    {
      type: "row",
      content: [
        {
          width: 50,
          type: "column",
          content: [
            {
              type: "stack",
              height: 85,

              content: [
                {
                  type: "component",
                  componentName: "codeEditor",
                  title: "Code Editor",
                },
                {
                  type: "component",
                  componentName: "veclangGuide",
                  title: "Veclang Guide",
                },
              ],
            },
            {
              type: "component",
              componentName: "optionsMenu",
              title: "Options",
            },
          ],
        },
        {
          type: "column",
          content: [
            {
              type: "stack",
              height: 30,
              content: [
                {
                  type: "component",
                  componentName: "headerOutput",
                  title: "Program Header",
                },
                {
                  type: "component",
                  componentName: "disOutput",
                  title: "Disassembled Output",
                },
              ],
            },
            {
              type: "row",
              content: [
                {
                  type: "component",
                  componentName: "imageOutput",
                  title: "Image Output",
                  width: 45,
                },
                {
                  type: "component",
                  componentName: "textOutput",
                  title: "Text Output",
                },
              ],
            },
            {
              type: "component",
              componentName: "imageGallery",
              title: "Image Gallery",
              height: 20,
            },
          ],
        },
      ],
    },
  ],
};
var layout = new GoldenLayout(config);
layout.registerComponent("codeEditor", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='codeEditorRoot' class='componentDiv'></div>");
});
layout.registerComponent("veclangGuide", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='veclangGuideRoot' class='componentDiv'></div>");
});
layout.registerComponent("optionsMenu", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='optionsMenuRoot' class='componentDiv'></div>");
});
layout.registerComponent("textOutput", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='textOutputRoot' class='componentDiv'></div>");
});
layout.registerComponent("headerOutput", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='headerOutputRoot' class='componentDiv'></div>");
});
layout.registerComponent("disOutput", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='disOutputRoot' class='componentDiv'></div>");
});
layout.registerComponent("imageOutput", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='imageOutputRoot' class='componentDiv'></div>");
});
layout.registerComponent("imageGallery", function (container, _componentState) {
  container
    .getElement()
    .html("<div id='imageGalleryRoot' class='componentDiv'></div>");
});
layout.on("initialised", () => {
  startReactApp();
});
layout.init();
