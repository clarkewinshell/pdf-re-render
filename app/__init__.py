from .ui import PDFReRendererUI
import tkinter as tk

__all__ = ["run", "PDFReRendererUI"]

def run():
    root = tk.Tk()
    app = PDFReRendererUI(root)
    root.mainloop()
