import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

class PdfOcrProcessor:
    def __init__(self):
        self.selected_folder_path = None
        self.processing_thread = None
        self.stop_processing = False

        # Create the GUI
        self.window = tk.Tk()
        self.window.title("OCR PDF Processor")
        
        # Label for selected folder path
        self.selected_path_label = tk.Label(self.window, text="Selected Folder: ")
        self.selected_path_label.grid(row=0, column=0, padx=10, pady=10)

        # Text widget to display selected folder path
        self.selected_path_text = tk.Text(self.window, height=1, width=50)
        self.selected_path_text.grid(row=0, column=1, padx=10, pady=10)

        # Button to select folder
        self.select_folder_button = tk.Button(self.window, text="Select Folder", command=self.select_folder)
        self.select_folder_button.grid(row=0, column=2, padx=10, pady=10)

        # Button to start OCR
        self.run_ocr_button = tk.Button(self.window, text="Run OCR", command=self.start_ocr_process)
        self.run_ocr_button.grid(row=1, column=1, padx=10, pady=10)

        # Button to stop OCR
        self.stop_ocr_button = tk.Button(self.window, text="Stop OCR", command=self.stop_ocr_process, state=tk.DISABLED)
        self.stop_ocr_button.grid(row=1, column=2, padx=10, pady=10)

        # Entry widget for batch size
        self.batch_size_label = tk.Label(self.window, text="Batch Size: ")
        self.batch_size_label.grid(row=2, column=0, padx=10, pady=10)

        self.batch_size_entry = tk.Entry(self.window, width=10)
        self.batch_size_entry.grid(row=2, column=1, padx=10, pady=10)
        self.batch_size_entry.insert(tk.END, "10")  # Default batch size

        # Center the GUI elements
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure(2, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_rowconfigure(2, weight=1)

    def run(self):
        self.window.mainloop()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.selected_folder_path = folder_path
            self.selected_path_text.delete(1.0, tk.END)
            self.selected_path_text.insert(tk.END, self.selected_folder_path)
            self.run_ocr_button.config(state=tk.NORMAL)

    def start_ocr_process(self):
        if self.selected_folder_path:
            self.run_ocr_button.config(state=tk.DISABLED)
            self.stop_ocr_button.config(state=tk.NORMAL)

            try:
                batch_size = int(self.batch_size_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Batch size must be a valid integer.")
                self.run_ocr_button.config(state=tk.NORMAL)
                self.stop_ocr_button.config(state=tk.DISABLED)
                return

            self.processing_thread = threading.Thread(target=self.process_folder_in_batches, args=(self.selected_folder_path, batch_size))
            self.processing_thread.start()

    def stop_ocr_process(self):
        self.stop_processing = True
        messagebox.showinfo("Stopping OCR", "OCR processing will stop after the current batch completes.")

    def process_folder_in_batches(self, folder_path, batch_size):

        output_root_temp = os.path.join(os.path.dirname(folder_path), "OCR_OUTPUT")

        output_root = os.path.join(output_root_temp, os.path.basename(folder_path))  
        os.makedirs(output_root, exist_ok=True)

        files_to_process = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if file_name.lower().endswith('.pdf'):
                    input_pdf_path = os.path.join(root, file_name)
                    files_to_process.append(input_pdf_path)

        num_files = len(files_to_process)
        num_batches = (num_files + batch_size - 1) // batch_size

        for i in range(num_batches):
            batch_files = files_to_process[i * batch_size:(i + 1) * batch_size]
            self.run_ocrprocess(batch_files, folder_path, output_root)

            if self.stop_processing:
                break

        self.stop_processing = False
        self.run_ocr_button.config(state=tk.NORMAL)
        self.stop_ocr_button.config(state=tk.DISABLED)
        messagebox.showinfo("OCR Processing", "OCR processing completed.")

    def run_ocrprocess(self, file_paths, input_root, output_root):
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as executor:
            futures = []
            for input_pdf_path in file_paths:
                rel_path = os.path.relpath(input_pdf_path, input_root)
                output_dir = os.path.join(output_root, os.path.dirname(rel_path))
                os.makedirs(output_dir, exist_ok=True)

                output_pdf_path = os.path.join(output_dir, os.path.basename(input_pdf_path))
                future = executor.submit(self.ocrpdf_file, input_pdf_path, output_pdf_path)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing file: {e}")

    def ocrpdf_file(self, input_pdf_path, output_pdf_path):
        try:
            subprocess.run(['ocrmypdf', '--force-ocr', input_pdf_path, output_pdf_path], check=True)
            print(f"OCR completed for: {input_pdf_path}")
        except Exception as e:
            print(f"OCR failed for: {input_pdf_path}, Error: {e}")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.window.destroy()

# Create an instance of PdfOcrProcessor
app = PdfOcrProcessor()

# Run the application
app.run()
