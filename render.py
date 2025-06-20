from weasyprint import HTML
import pdfkit
import os
import tempfile

from doc_utils import escape_for_latex

# Define a function to render LaTeX to PDF
def render_latex(command, latex_data):
    """
    Renders LaTeX to PDF using a specified command.

    Args:
        command (list): The command to run LaTeX (e.g., pdflatex).
        latex_data (str): The LaTeX data to render.

    Returns:
        BytesIO: A byte stream of the rendered PDF.
    """
    import subprocess
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        tex_file_path = os.path.join(tmpdirname, "document.tex")
        pdf_file_path = os.path.join(tmpdirname, "document.pdf")

        # Write LaTeX data to the file
        with open(tex_file_path, "w", encoding="utf-8") as tex_file:
            tex_file.write(latex_data)

        # Run LaTeX command
        result = subprocess.run(command, cwd=tmpdirname, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"LaTeX compilation error: {result.stderr.decode()}")
            return None

        with open(pdf_file_path, "rb") as pdf_file:
            return pdf_file.read()

def render_cover_letter(latex_data):
    """
    Renders LaTeX to PDF for the cover letter.
    """
    import subprocess
    import tempfile
    
    latex_command = ["pdflatex", "-interaction=nonstopmode", "cover_letter.tex"]

    with tempfile.TemporaryDirectory() as tmpdirname:
        tex_file_path = os.path.join(tmpdirname, "cover_letter.tex")

        # Write LaTeX data to the file
        with open(tex_file_path, "w", encoding="utf-8") as tex_file:
            tex_file.write(latex_data)

        # Run LaTeX command
        result = subprocess.run(latex_command, cwd=tmpdirname, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"LaTeX compilation error: {result.stderr.decode()}")
            return None

        pdf_path = os.path.join(tmpdirname, "cover_letter.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                return pdf_file.read()
        else:
            return None