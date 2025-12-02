from typing import Tuple
import ghostscript
import os
from PyPDF2 import PdfReader

def render_pdf(input_pdf: str, output_pdf: str, quality: str = "high") -> Tuple[bool, str | None]:

    try:

        # Basic check
        if not os.path.exists(input_pdf):
            return False, "Input file does not exist"

        # Check for encryption
        try:
            reader = PdfReader(input_pdf)
            if getattr(reader, "is_encrypted", False):
                try:
                    # PyPDF2 decrypt() return value variation (int/bool/None)
                    res = reader.decrypt("")
                except TypeError:
                    res = reader.decrypt(b"")
                if res in (0, False, None):
                    return False, "PDF is encrypted and requires a password to process."
        except Exception:
            # if PyPDF2 fails, let ghostscript try
            pass

        quality_settings = {
            "high": ["-dPDFSETTINGS=/prepress", "-r300"],
            "medium": ["-dPDFSETTINGS=/ebook", "-r150"],
            "low": ["-dPDFSETTINGS=/screen", "-r72"],
        }

        quality_args = quality_settings.get(quality, quality_settings["high"])

        args = [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=pdfwrite",
        ] + quality_args + [f"-sOutputFile={output_pdf}", input_pdf]

        gs_args = [a.encode("utf-8") for a in args]

        try:
            # ghostscript argument error handler
            ghostscript.Ghostscript(*gs_args)
            return True, None
        except Exception as e:
            return False, f"Ghostscript error: {e}"
    except Exception as exc:  # unexpected
        return False, str(exc)
