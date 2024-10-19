import time
import pandas as pd
import customtkinter as ctk
import aiohttp
import asyncio
import csv
import warnings
from PIL import Image, ImageTk
from io import BytesIO

warnings.simplefilter('ignore')

async def fetch_image_details(session, semaphore, url):
    async with semaphore:
        try:
            async with session.get(url, ssl=False) as response:
                if response.status == 200:
                    img = Image.open(BytesIO(await response.read()))
                    width, height = img.size
                    mode = img.mode
                    img_format = img.format
                    return (url, width, height, mode, img_format)
                else:
                    return (url, "Error", "Failed to fetch", "", "")
        except Exception as e:
            return (url, "Error", str(e), "", "")

async def process_images(urls, output_file, progress_update_func, max_concurrent_requests=10):
    start_time = time.time()
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    total_urls = len(urls)

    if total_urls == 0:
        progress_update_func("No URLs to process.", 100)
        return 0

    progress_increment = 100 / total_urls
    progress_update_func("Processing URLs...", 0)

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Width", "Height", "Mode", "Format"])

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_image_details(session, semaphore, url) for url in urls]
            start_processing_time = time.time()

            for i, result in enumerate(await asyncio.gather(*tasks)):
                writer.writerow(result)
                elapsed = time.time() - start_processing_time
                estimated_total_time = (elapsed / (i + 1)) * total_urls
                estimated_time_remaining = estimated_total_time - elapsed

                progress = (i + 1) * progress_increment
                progress_update_func(
                    f"Progress: {progress:.2f}% | Est. Time Remaining: {estimated_time_remaining:.2f} seconds",
                    progress
                )

                await asyncio.sleep(0)  

    progress_update_func("Processing complete.", 100)

    end_time = time.time()
    return end_time - start_time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ImageDetailsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("PixelPeek")
        self.geometry("700x500")
        self.load_logo()
        self.create_widgets()

    def load_logo(self):
        try:
            logo_image = Image.open("logo.png")
            logo_image = logo_image.resize((200, 100))
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            self.logo_label = ctk.CTkLabel(self, image=self.logo_photo, text="")
            self.logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")

    def create_widgets(self):
        self.progress_percentage = ctk.CTkLabel(self,             
    text="PixelPeek",  
    text_color="blue",      
    font=("Arial", 24),    
    corner_radius=10,     
    fg_color=("white", "lightgrey") )
        self.progress_percentage.pack()

        self.select_button = ctk.CTkButton(self, text="Select Excel File", command=self.select_file)
        self.select_button.pack(pady=20)

        self.progress_var = ctk.StringVar()
        self.progress_label = ctk.CTkLabel(self, textvariable=self.progress_var)
        self.progress_label.pack(pady=10)

        self.progress_percentage = ctk.CTkLabel(self, text="0%")
        self.progress_percentage.pack()

        self.progress_bar = ctk.CTkProgressBar(self, width=600, height=20)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=20)

        self.process_button = ctk.CTkButton(self, text="Start Processing", command=self.start_processing)
        self.process_button.pack(pady=20)

        self.file_path = None

    def select_file(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx;*.xls")],
            title="Select an Excel file"
        )
        if file_path:
            self.file_path = file_path
            self.progress_var.set(f"Selected file: {file_path}")

    def start_processing(self):
        if not self.file_path:
            self.progress_var.set("No file selected.")
            return

        self.progress_var.set("Processing started...")
        asyncio.run(self.run_processing())

    async def run_processing(self):
        try:
            df = pd.read_excel(self.file_path, sheet_name='Sheet1')
            urls = df.values.flatten()
            output_file = 'image_details.csv'

            elapsed_time = await process_images(urls, output_file, self.update_progress)
            self.progress_var.set(f"Image details saved to {output_file} \n\n Total execution time: {elapsed_time:.2f} seconds")

        except Exception as e:
            self.progress_var.set(f"Error: {e}")

    def update_progress(self, message, progress):
        print(f"Update Progress called with message: '{message}' and progress: {progress}")  # Debugging
        self.progress_var.set(message)
        self.progress_percentage.configure(text=f"{progress:.2f}%")
        self.progress_bar.set(progress / 100)  
        self.update_idletasks()  

if __name__ == "__main__":
    app = ImageDetailsApp()
    app.mainloop()
