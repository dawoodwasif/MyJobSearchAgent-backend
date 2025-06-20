import tempfile
import subprocess
import os
import shutil


def render_latex(latex_command, latex_data):
    src_path = os.path.dirname(os.path.realpath(__file__)) + "/inputs"

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Copy auxiliary files to temporary directory
        shutil.copytree(src_path, tmpdirname, dirs_exist_ok=True)

        # write latex data to a file
        with open(f"{tmpdirname}/resume.tex", "w") as f:
            f.write(latex_data)

        # run latex command
        print("LaTeX command:", latex_command)
        print("Working directory:", tmpdirname)
        
        try:
            latex_process = subprocess.Popen(latex_command, cwd=tmpdirname)
            latex_process.wait()

            # Check if PDF was created
            pdf_path = f"{tmpdirname}/resume.pdf"
            if not os.path.exists(pdf_path):
                print("ERROR: PDF file was not created")
                return None

            # read pdf data
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            return pdf_data
        except FileNotFoundError as e:
            print(f"ERROR: LaTeX command not found: {latex_command}")
            print("Please install LaTeX (TeX Live, MiKTeX, or similar)")
            print("For Windows: https://miktex.org/download")
            print("For Ubuntu: sudo apt-get install texlive-full")
            return None
        except Exception as e:
            print(f"ERROR: LaTeX compilation failed: {e}")
            return None


def render_cover_letter(latex_command, latex_data, output_filename="cover_letter.pdf"):
    """
    Renders a cover letter from LaTeX to PDF.
    
    Parameters:
        latex_command (list): The command to compile LaTeX (e.g., ["pdflatex", "cover_letter.tex"]).
        latex_data (str): The LaTeX data for the cover letter.
        output_filename (str): Name of the generated PDF file (default: "cover_letter.pdf").

    Returns:
        bytes: Binary data of the compiled PDF.
    """
    src_path = os.path.dirname(os.path.realpath(__file__)) + "/inputs"

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Copy auxiliary files to temporary directory
        shutil.copytree(src_path, tmpdirname, dirs_exist_ok=True)

        # Write the LaTeX data to a temporary .tex file
        tex_file_path = os.path.join(tmpdirname, "cover_letter.tex")
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(latex_data)

        try:
            # Run the LaTeX compilation command
            print("DEBUG: Running LaTeX command:", latex_command)
            print("DEBUG: Working directory:", tmpdirname)
            latex_process = subprocess.Popen(latex_command, cwd=tmpdirname)
            latex_process.wait()

            # Check if PDF was created
            pdf_file_path = os.path.join(tmpdirname, output_filename)
            if not os.path.exists(pdf_file_path):
                print("ERROR: Cover letter PDF file was not created")
                # Try alternative output name
                alt_pdf_path = os.path.join(tmpdirname, "cover_letter.pdf")
                if os.path.exists(alt_pdf_path):
                    pdf_file_path = alt_pdf_path
                else:
                    return None

            # Read and return the PDF file content
            with open(pdf_file_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()

            return pdf_data
        except FileNotFoundError as e:
            print(f"ERROR: LaTeX command not found: {latex_command}")
            print("Please install LaTeX (TeX Live, MiKTeX, or similar)")
            print("For Windows: https://miktex.org/download")
            print("For Ubuntu: sudo apt-get install texlive-full")
            return None
        except Exception as e:
            print(f"ERROR: Cover letter LaTeX compilation failed: {e}")
            return None