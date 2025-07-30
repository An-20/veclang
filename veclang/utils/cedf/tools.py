import abc
import json
import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb

from veclang.utils.cedf.cedf import (
    encode_cedf_to_bytes,
    decode_cedf_from_bytes,
    CEDF_HEADER_FIELDS,
    CEDFHeader,
)


class CEDFViewer(ctk.CTk, abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def get_title() -> str:
        """Gets the title for the window"""

    @staticmethod
    def get_filetypes() -> list[tuple[str, str]]:
        """
        Gets a list of filetypes e.g.:
        [("SEDF files", "*.sedf"), ("All files", "*.*")]
        """
        return [("SEDF files", "*.sedf"), ("All files", "*.*")]

    @staticmethod
    def default_format(data: bytes) -> str:
        """Default formatter included in ABC in case subclasses want to use as a fallback."""
        lines = []
        width = 16
        for i in range(0, len(data), width):
            chunk = data[i : i + width]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{i:08X}  {hex_part:<48}  {ascii_part}")
        return "\n".join(lines)

    def __init__(self):
        super().__init__()
        self.title(self.get_title())
        self.geometry("950x750")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((1, 2, 3), weight=1)

        self.file_path = None
        self.sedf_id = None
        self.binary_payload = b""

        # --- Labels ---
        ctk.CTkLabel(
            self, text="Header Viewer", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
        self.header_text = ctk.CTkTextbox(self, height=90, font=("Courier New", 14))
        self.header_text.grid(
            row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10)
        )
        self.header_text.configure(state="disabled")

        ctk.CTkLabel(
            self, text="JSON Editor", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=2, column=0, sticky="w", padx=10)
        self.json_editor = ctk.CTkTextbox(self, font=("Courier New", 14))
        self.json_editor.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            self, text="Binary Payload Viewer", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=2, column=1, sticky="w", padx=10)
        self.binary_viewer = ctk.CTkTextbox(self, font=("Courier New", 14))
        self.binary_viewer.grid(row=3, column=1, sticky="nsew", padx=10, pady=(0, 10))
        self.binary_viewer.configure(state="disabled")

        # --- Buttons ---
        self.load_button = ctk.CTkButton(
            self, text="Open CEDF File", command=self.load_file
        )
        self.load_button.grid(row=4, column=0, pady=10, padx=10, sticky="ew")

        self.save_button = ctk.CTkButton(
            self, text="Save JSON Changes", command=self.save_json_changes
        )
        self.save_button.grid(row=4, column=1, pady=10, padx=10, sticky="ew")

    def load_file(self, path=None):
        if not path:
            path = fd.askopenfilename(filetypes=self.get_filetypes())
        if not path:
            return
        try:
            with open(path, "rb") as f:
                blob = f.read()
            header, json_header, binary_payload = decode_cedf_from_bytes(blob)
            self.file_path = path
            self.sedf_id = header.sedf_id
            self.binary_payload = binary_payload

            self.display_header(header)
            self.json_editor.delete("1.0", "end")
            self.json_editor.insert("1.0", json.dumps(json_header, indent=2))

            self.binary_viewer.configure(state="normal")
            self.binary_viewer.delete("1.0", "end")
            self.binary_viewer.insert("1.0", self.default_format(binary_payload))
            self.binary_viewer.configure(state="disabled")

        except Exception as e:
            mb.showerror("Error", f"Failed to load file:\n{e}")

    def save_json_changes(self):
        if not self.file_path:
            mb.showwarning("No file", "No file loaded.")
            return
        try:
            new_json = json.loads(self.json_editor.get("1.0", "end").strip())
            blob = encode_cedf_to_bytes(new_json, self.binary_payload, self.sedf_id)
            with open(self.file_path, "wb") as f:
                f.write(blob)
            mb.showinfo("Saved", "JSON header updated successfully.")
        except json.JSONDecodeError:
            mb.showerror("Invalid JSON", "Failed to parse JSON.")
        except Exception as e:
            mb.showerror("Error", f"Failed to save file:\n{e}")

    def display_header(self, header: CEDFHeader):
        self.header_text.configure(state="normal")
        self.header_text.delete("1.0", "end")
        for name, _ in CEDF_HEADER_FIELDS:
            value = getattr(header, name)
            if isinstance(value, bytes):
                value = value.decode("ascii")
            self.header_text.insert("end", f"{name}: {value}\n")
        self.header_text.configure(state="disabled")


class CEDFViewerUniversal(CEDFViewer):

    @staticmethod
    def get_title() -> str:
        return "Universal CEDF Viewer"


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = CEDFViewerUniversal()
    app.mainloop()
