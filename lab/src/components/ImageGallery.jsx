import { useState } from "react";
import Icon from "@mui/material/Icon";
import DownloadIcon from "@mui/icons-material/Download";

import vl_sample_image_b64 from "../assets/vl_sample_image.base64?raw";

export default function ImageGallery() {
  const initialBmp = {
    uri: vl_sample_image_b64,
    objectURL: vl_sample_image_b64,
  };
  const [images, setImages] = useState([initialBmp]);

  const addImage = (value) => {
    const uri = value.trim();
    const objectURL =
      uri.startsWith("data:") ||
      uri.startsWith("blob:") ||
      uri.startsWith("http")
        ? uri
        : URL.createObjectURL(new Blob([uri], { type: "image/jpeg" }));
    setImages([{ uri, objectURL }, ...images]);
  };

  window.addImageToGallery = addImage;

  const handleDownload = (uri) => {
    const link = document.createElement("a");
    link.href = uri;
    link.download = "image.jpg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      style={{
        whiteSpace: "nowrap",
        padding: "0.5rem",
        height: "100%",
        width: "100%",
        overflowX: "scroll",
      }}
    >
      <div
        style={{
          display: "flex",
          gap: "1rem",
          height: "100%",
          overflowY: "hidden",
        }}
      >
        {images.map((img, index) => (
          <div
            key={index}
            style={{
              position: "relative",
              borderRadius: "0.5rem",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
            }}
            onMouseEnter={(e) => {
              const btn = e.currentTarget.querySelector("button");
              if (btn) btn.style.opacity = 1;
            }}
            onMouseLeave={(e) => {
              const btn = e.currentTarget.querySelector("button");
              if (btn) btn.style.opacity = 0;
            }}
          >
            <img
              src={img.objectURL}
              alt={`Image ${index}`}
              style={{
                height: "100%",
                width: "auto",
                borderRadius: "0.5rem",
              }}
            />
            <button
              onClick={() => handleDownload(img.objectURL)}
              style={{
                position: "absolute",
                top: "0.5rem",
                right: "0.5rem",
                background: "white",
                border: "none",
                borderRadius: "50%",
                padding: "0.25rem 0.5rem",
                boxShadow: "0 1px 4px rgba(0, 0, 0, 0.2)",
                cursor: "pointer",
                opacity: 0,
                transition: "opacity 0.3s",
              }}
            >
              <DownloadIcon color="primary"></DownloadIcon>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
