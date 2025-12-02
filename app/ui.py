import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
from .core import render_pdf

class PDFReRendererUI:

    def __init__(self, root: tk.Tk):

        # window
        width = 500
        height = 380

        self.root = root
        root.title("PDF Re-Render Tool (Ghostscript)")
        root.geometry(f"{width}x{height}")
        root.minsize(width, height)

        self.input_paths = []
        self.output_folder = tk.StringVar()
        self.is_processing = False

        main = tk.Frame(root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # mode selection
        self.mode = tk.StringVar(value="single")
        mode_fr = tk.Frame(main)
        mode_fr.pack(anchor="w", pady=(0, 8))
        tk.Radiobutton(mode_fr, text="Single File", variable=self.mode, value="single", command=self._update_ui).pack(side=tk.LEFT, padx=8)
        tk.Radiobutton(mode_fr, text="Batch", variable=self.mode, value="batch", command=self._update_ui).pack(side=tk.LEFT, padx=8)

        # containers
        self.mode_container = tk.Frame(main)
        self.mode_container.pack(fill="both", expand=True)

        # single
        self.single_frame = tk.Frame(self.mode_container)
        tk.Label(self.single_frame, text="Input PDF:").pack(anchor="w")
        sin_fr = tk.Frame(self.single_frame)
        sin_fr.pack(anchor="w", fill="x", pady=4)
        self.single_input_var = tk.StringVar()
        tk.Entry(sin_fr, textvariable=self.single_input_var, width=56).pack(side=tk.LEFT, padx=4)
        tk.Button(sin_fr, text="Browse", command=self._select_single_input).pack(side=tk.LEFT, padx=4)

        tk.Label(self.single_frame, text="Output PDF:").pack(anchor="w", pady=(8, 0))
        out_fr = tk.Frame(self.single_frame)
        out_fr.pack(anchor="w", fill="x", pady=4)
        self.single_output_var = tk.StringVar()
        tk.Entry(out_fr, textvariable=self.single_output_var, width=56).pack(side=tk.LEFT, padx=4)
        tk.Button(out_fr, text="Browse", command=self._select_single_output).pack(side=tk.LEFT, padx=4)

        # batch
        self.batch_frame = tk.Frame(self.mode_container)
        tk.Label(self.batch_frame, text="Input PDFs:").pack(anchor="w")
        bat_fr = tk.Frame(self.batch_frame)
        bat_fr.pack(anchor="w", fill="x", pady=4)
        self.batch_input_var = tk.StringVar()
        tk.Entry(bat_fr, textvariable=self.batch_input_var, width=56).pack(side=tk.LEFT, padx=4)
        tk.Button(bat_fr, text="Browse Files", command=self._select_batch_input).pack(side=tk.LEFT, padx=4)
        tk.Button(bat_fr, text="Clear", command=self._clear_batch_input).pack(side=tk.LEFT, padx=4)

        tk.Label(self.batch_frame, text="Output Folder:").pack(anchor="w", pady=(8, 0))
        outbat_fr = tk.Frame(self.batch_frame)
        outbat_fr.pack(anchor="w", fill="x", pady=4)
        tk.Entry(outbat_fr, textvariable=self.output_folder, width=56).pack(side=tk.LEFT, padx=4)
        tk.Button(outbat_fr, text="Browse", command=self._select_output_folder).pack(side=tk.LEFT, padx=4)

        # quality
        tk.Label(main, text="Quality:").pack(anchor="w", pady=(8, 0))
        self.quality = tk.StringVar(value="high")
        qf = tk.Frame(main)
        qf.pack(anchor="w", padx=12, pady=4)
        tk.Radiobutton(qf, text="High", variable=self.quality, value="high").pack(side=tk.LEFT)
        tk.Radiobutton(qf, text="Medium", variable=self.quality, value="medium").pack(side=tk.LEFT, padx=8)
        tk.Radiobutton(qf, text="Low", variable=self.quality, value="low").pack(side=tk.LEFT, padx=8)

        # stat
        tk.Label(main, text="Status:").pack(anchor="w", pady=(8, 0))
        self.progress_var = tk.StringVar(value="Ready")
        tk.Label(main, textvariable=self.progress_var, fg="blue").pack(anchor="w", padx=12, pady=4)

        # run button
        self.run_button = tk.Button(main, text="Re-Render PDF(s)", command=self._run_thread, bg="#3463E2", fg="white")
        self.run_button.pack(pady=10)

        self._update_ui()

    # --- UI helper ---
    def _update_ui(self):
        if self.mode.get() == "single":
            self.batch_frame.pack_forget()
            self.single_frame.pack(fill="both", expand=True)
        else:
            self.single_frame.pack_forget()
            self.batch_frame.pack(fill="both", expand=True)

    def _select_single_input(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.single_input_var.set(path)

    def _select_single_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.single_output_var.set(path)

    def _select_batch_input(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if paths:
            self.input_paths = list(paths)
            self.batch_input_var.set(f"{len(self.input_paths)} file(s) selected")

    def _clear_batch_input(self):
        self.input_paths = []
        self.batch_input_var.set("")

    def _select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    # --- processing ---
    def _run_thread(self):
        if self.is_processing:
            messagebox.showwarning("Warning", "A process is already running.")
            return
        t = threading.Thread(target=self._run)
        t.daemon = True
        t.start()

    def _run(self):
        self.is_processing = True
        self.run_button.config(state="disabled")
        try:
            if self.mode.get() == "single":
                self._process_single()
            else:
                self._process_batch()
        finally:
            self.is_processing = False
            self.run_button.config(state="normal")
            if self.progress_var.get().startswith("Processing"):
                self.progress_var.set("Ready")

    def _process_single(self):
        input_pdf = self.single_input_var.get()
        output_pdf = self.single_output_var.get()

        if not input_pdf or not output_pdf:
            messagebox.showerror("Error", "Please select both input and output files.")
            return
        if not os.path.exists(input_pdf):
            messagebox.showerror("Error", "Input PDF file does not exist.")
            return

        self.progress_var.set(f"Processing: {os.path.basename(input_pdf)}...")
        success, msg = render_pdf(input_pdf, output_pdf, self.quality.get())
        if success:
            self.progress_var.set("Success! PDF restrictions removed.")
            messagebox.showinfo("Success", f"PDF re-rendered successfully!\n\nOutput saved to:\n{output_pdf}")
        else:
            messagebox.showerror("Error", f"Failed to re-render {os.path.basename(input_pdf)}:\n{msg}")

    def _process_batch(self):
        if not self.input_paths:
            messagebox.showerror("Error", "Please select PDF files to process.")
            return
        out_folder = self.output_folder.get()
        if not out_folder or not os.path.exists(out_folder):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return

        successful = 0
        failed = 0
        failed_files = []

        for i, input_pdf in enumerate(self.input_paths, 1):
            filename = os.path.basename(input_pdf)
            name, _ = os.path.splitext(filename)
            output_pdf = os.path.join(out_folder, f"{name}_unrestricted.pdf")

            self.progress_var.set(f"Processing ({i}/{len(self.input_paths)}): {filename}...")
            success, msg = render_pdf(input_pdf, output_pdf, self.quality.get())
            if success:
                successful += 1
            else:
                failed += 1
                failed_files.append(f"{filename}: {msg}")

        self.progress_var.set("Batch processing completed.")
        summary = f"Batch Processing Complete!\n\n✓ Successful: {successful}\n✗ Failed: {failed}"
        if failed_files:
            summary += "\n\nFailed files:\n" + "\n".join(failed_files)
        messagebox.showinfo("Batch Complete", summary)
