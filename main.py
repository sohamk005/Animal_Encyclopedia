import tkinter as tk
from tkinter import ttk, messagebox
import json
from PIL import Image, ImageTk
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY") 
print(API_KEY)
if not API_KEY:
    API_KEY = "MISSING_API_KEY_OR_DOTENV_NOT_LOADED" 
API_URL = "https://api.api-ninjas.com/v1/animals?name="


COLOR_BACKGROUND = "#2C3E50"
COLOR_FRAME = "#34495E"
COLOR_TEXT = "#ECF0F1"
COLOR_ACCENT = "#1ABC9C"
COLOR_BUTTON_TEXT = "#2C3E50"


class AnimalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Animal Encyclopedia - Desktop Application")
        self.root.geometry("800x600")
        self.root.configure(bg=COLOR_BACKGROUND)

        self.setup_styles()
        
        self.local_animals_data = self.load_local_data()
        self.api_search_results = []

        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLOR_BACKGROUND)
        style.configure('TLabel', background=COLOR_BACKGROUND, foreground=COLOR_TEXT, font=("Helvetica", 12))
        style.configure('Dark.TLabelframe', background=COLOR_BACKGROUND, bordercolor=COLOR_TEXT)
        style.configure('Dark.TLabelframe.Label', background=COLOR_BACKGROUND, foreground=COLOR_TEXT, font=("Helvetica", 12, "bold"))
        style.configure('TButton', background=COLOR_ACCENT, foreground=COLOR_BUTTON_TEXT, font=("Helvetica", 12, "bold"), borderwidth=0)
        style.map('TButton', background=[('active', '#16A085')])
        style.configure('TEntry', fieldbackground=COLOR_FRAME, foreground=COLOR_TEXT, bordercolor=COLOR_ACCENT, insertcolor=COLOR_TEXT)


    def load_local_data(self):
        try:
            with open('animals.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", "animals.json not found! Please make sure the file is in the same directory.")
            return []
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error decoding animals.json. Please check the file format.")
            return []

    def create_widgets(self):
        search_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Search Animal:", style='TLabel').pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40, font=("Helvetica", 12), style='TEntry')
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind("<Return>", self.search_animals)

        search_button = ttk.Button(search_frame, text="Search", command=self.search_animals, style='TButton')
        search_button.pack(side=tk.LEFT, padx=5)

        content_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        content_frame.pack(expand=True, fill=tk.BOTH)

        results_frame = ttk.LabelFrame(content_frame, text="Search Results", padding="10", style='Dark.TLabelframe')
        results_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.results_listbox = tk.Listbox(
            results_frame, height=25, font=("Helvetica", 11), bg=COLOR_FRAME, fg=COLOR_TEXT,
            highlightthickness=0, borderwidth=0, selectbackground=COLOR_ACCENT, selectforeground=COLOR_BUTTON_TEXT
        )
        self.results_listbox.pack(expand=True, fill=tk.Y)
        self.results_listbox.bind("<<ListboxSelect>>", self.show_animal_info)

        details_frame = ttk.LabelFrame(content_frame, text="Animal Information", padding="10", style='Dark.TLabelframe')
        details_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.image_label = ttk.Label(details_frame, style='TLabel', justify=tk.CENTER)
        self.image_label.pack(pady=10)

        self.info_text = tk.Text(
            details_frame, wrap=tk.WORD, font=("Helvetica", 12), height=15, bg=COLOR_BACKGROUND,
            fg=COLOR_TEXT, borderwidth=0, highlightthickness=0
        )
        self.info_text.pack(expand=True, fill=tk.BOTH, pady=5)
        self.info_text.config(state=tk.DISABLED)
        
        self.populate_listbox(self.local_animals_data, is_local=True)

    def populate_listbox(self, animals, is_local=False):
        self.results_listbox.delete(0, tk.END)
        self.is_local_search = is_local
        for animal in animals:
            self.results_listbox.insert(tk.END, animal['name'])

    def search_animals(self, event=None):
        """Searches local data first, then uses the API as a fallback."""
        query = self.search_entry.get().strip().lower()
        if not query:
            self.populate_listbox(self.local_animals_data, is_local=True)
            return

        local_results = [
            animal for animal in self.local_animals_data 
            if query in animal['name'].lower()
        ]

        if local_results:
            self.populate_listbox(local_results, is_local=True)
            return

        messagebox.showinfo("Searching Online", f"'{query.capitalize()}' not in local data. Searching online...")

        if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
            messagebox.showerror("API Key Error", "Please add your API key at the top of the main.py file.")
            return
        
        headers = {'X-Api-Key': API_KEY}
        try:
            response = requests.get(API_URL + query, headers=headers)
            response.raise_for_status()
            
            self.api_search_results = response.json()

            if not self.api_search_results:
                messagebox.showinfo("Not Found", f"No results found for '{query}' locally or online.")
            else:
                self.populate_listbox(self.api_search_results, is_local=False)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Could not connect to the API: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def show_animal_info(self, event=None):
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            return
        selected_name = self.results_listbox.get(selected_indices[0])
        if self.is_local_search:
            self.display_local_info(selected_name)
        else:
            self.display_api_info(selected_name)
            
    def display_local_info(self, name):
        animal_info = next((animal for animal in self.local_animals_data if animal['name'] == name), None)
        if animal_info:
            try:
                img = Image.open(animal_info['image'])
                img.thumbnail((200, 200))
                self.photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo_image, text="")
            except Exception:
                self.image_label.config(image='', text="Image not found")

            info_string = f"Scientific Name: {animal_info['scientific_name']}\n\n"
            info_string += f"Type: {animal_info['type']}\n"
            info_string += f"Region: {animal_info['region']}\n"
            info_string += f"Conservation Status: {animal_info['conservation_status']}\n\n"
            info_string += f"Habitat: {animal_info['habitat']}\n\n"
            info_string += f"Description: {animal_info['description']}"
            
            self.update_info_text(info_string)

    def display_api_info(self, name):
        animal_info = next((animal for animal in self.api_search_results if animal['name'] == name), None)
        if animal_info:
            self.image_label.config(image='', text="Image Not Available\n(Online API Result)")

            taxonomy = animal_info.get('taxonomy', {})
            characteristics = animal_info.get('characteristics', {})
            
            info_string = f"Scientific Name: {taxonomy.get('scientific_name', 'N/A')}\n\n"
            info_string += f"Type: {characteristics.get('group', 'N/A')}\n"
            info_string += f"Location: {', '.join(animal_info.get('locations', ['N/A']))}\n"
            info_string += f"Diet: {characteristics.get('diet', 'N/A')}\n\n"
            info_string += f"Habitat: {characteristics.get('habitat', 'N/A')}\n\n"
            info_string += f"Biggest Threat: {characteristics.get('biggest_threat', 'N/A')}\n\n"
            info_string += f"Distinctive Feature: {characteristics.get('most_distinctive_feature', 'N/A')}"
            
            self.update_info_text(info_string)
            
    def update_info_text(self, text):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', text)
        self.info_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimalApp(root)
    root.mainloop()