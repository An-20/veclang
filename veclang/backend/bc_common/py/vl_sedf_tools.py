import json
import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb

from veclang.utils.cedf.cedf import decode_cedf_from_bytes
from veclang.utils.cedf.tools import CEDFViewer

from veclang.backend.bc_common.py.vl_sedf import VlProgram, VlSEDF
from veclang.backend.bc_compiler.vl_disassembler import disassemble_vl_program


class VlSEDFViewer(CEDFViewer):

    @staticmethod
    def get_title() -> str:
        pass

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

            vl_program = VlSEDF.load(path)

            self.display_header(header)
            self.json_editor.delete("1.0", "end")
            self.json_editor.insert("1.0", json.dumps(json_header, indent=2))

            self.binary_viewer.configure(state="normal")
            self.binary_viewer.delete("1.0", "end")
            self.binary_viewer.insert("1.0", self.format(vl_program))
            self.binary_viewer.configure(state="disabled")

        except Exception as e:
            mb.showerror("Error", f"Failed to load file:\n{e}")

    def format(self, vl_program: VlProgram) -> str:
        try:
            out_str = f"Constants:\n{self.default_format(vl_program['constants'])}\n\n"
            out_str += f"Instructions:\n{disassemble_vl_program(vl_program)}"
            return out_str
        except Exception as e:
            return (
                f"Exception when disassembling: {e}\nRaw data:"
                f"\n{self.default_format(vl_program['constants'] + vl_program['instructions'])}"
            )


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = VlSEDFViewer()
    app.mainloop()
