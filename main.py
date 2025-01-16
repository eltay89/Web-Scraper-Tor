import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
from bs4 import BeautifulSoup
import threading
import random
from stem import Signal
from stem.control import Controller
import time
import os
import json
from modules.pagination_csv import PaginationHandler, CSVExporter
from modules.javascript_rendering import JavaScriptRenderer
from modules.form_submission import FormSubmitter

# --- Constants ---
TOR_SOCKS_PORT = 9150  # Default Tor Browser SOCKS port
DEFAULT_TOR_CONTROL_PORT = 9051  # Default Tor Control port
DEFAULT_SAVE_DIR = os.path.expanduser("~")
SETTINGS_FILE = "settings.json"

# --- Enhanced CSS Selectors ---
CSS_SELECTORS = {
    "Whole Website": {
        "Entire Page": "*"
    },
    "Basic Elements": {
        "All Elements": "*",
        "Headings (h1-h6)": "h1, h2, h3, h4, h5, h6",
        "Paragraphs (p)": "p",
        "Spans (span)": "span",
        "Divs (div)": "div",
        "Links (a)": "a",
        "Images (img)": "img",
        "Forms (form)": "form",
        "Buttons (button)": "button",
        "Inputs (input)": "input",
        "Textareas (textarea)": "textarea",
    },
    "Headings": {
        "Heading 1 (h1)": "h1",
        "Heading 2 (h2)": "h2",
        "Heading 3 (h3)": "h3",
        "Heading 4 (h4)": "h4",
        "Heading 5 (h5)": "h5",
        "Heading 6 (h6)": "h6",
    },
    "Text": {
        "Paragraphs": "p",
        "Strong Text (strong)": "strong",
        "Emphasized Text (em)": "em",
        "Line Breaks (br)": "br",
    },
    "Lists": {
        "Unordered Lists (ul)": "ul",
        "Ordered Lists (ol)": "ol",
        "List Items (li)": "li",
    },
    "Tables": {
        "Tables": "table",
        "Table Headers (th)": "th",
        "Table Rows (tr)": "tr",
        "Table Data Cells (td)": "td",
    },
    "Media": {
        "Links": "a",
        "Images": "img",
        "Audio (audio)": "audio",
        "Video (video)": "video",
    },
    "Attributes": {
        "Links with href attribute": "a[href]",
        "Images with src attribute": "img[src]",
        "Elements with specific id": "#example-id",  # Replace example-id
        "Elements with specific class": ".example-class",  # Replace example-class
        "Elements with data attribute": "[data-value]", # Example data attribute
        "Links with rel='nofollow'": "a[rel='nofollow']",
        "Images with alt text": "img[alt]",
    },
    "Combinators": {
        "Child elements": "parent > child",
        "Descendant elements": "ancestor descendant",
        "Adjacent sibling elements": "previous + next",
        "General sibling elements": "element ~ siblings",
    },
    "Pseudo-classes": {
        "First child": ":first-child",
        "Last child": ":last-child",
        "Nth child (even)": ":nth-child(even)",
        "Nth child (odd)": ":nth-child(odd)",
        "Hover state": ":hover",
        "Focus state": ":focus",
    },
    "Forms": {
        "Input fields": "input[type='text']",
        "Password fields": "input[type='password']",
        "Submit buttons": "input[type='submit'], button[type='submit']",
        "Checkboxes": "input[type='checkbox']",
        "Radio buttons": "input[type='radio']",
        "Select dropdowns": "select",
        "Option elements": "option",
    },
    "Custom": ""
}

# --- Helper Functions ---

def get_random_user_agent():
    """Returns a random user agent from a predefined list."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

def test_connection(network_option, proxy_address="", tor_control_password="", tor_control_port=DEFAULT_TOR_CONTROL_PORT, tor_socks_ip="127.0.0.1", tor_socks_port=TOR_SOCKS_PORT):
    """Tests the connection for the selected network option."""
    proxies = {}
    if network_option == "HTTP Proxy":
        proxies = {
            'http': f'http://{proxy_address}',
            'https': f'http://{proxy_address}'
        }
    elif network_option == "Tor Network":
        proxies = {
            'http': f'socks5h://{tor_socks_ip}:{tor_socks_port}',
            'https': f'socks5h://{tor_socks_ip}:{tor_socks_port}'
        }

    test_url = "https://check.torproject.org/" if network_option == "Tor Network" else "https://api.ipify.org?format=json"

    try:
        response = requests.get(test_url, proxies=proxies, timeout=10)
        response.raise_for_status()

        if network_option == "Tor Network":
            if "Congratulations. This browser is configured to use Tor." not in response.text:
                raise requests.exceptions.RequestException("Failed to connect to Tor. Check Tor Browser is running and properly configured.")
        return "Connection successful!"
    except requests.exceptions.RequestException as e:
        return f"Connection failed: {e}"
    except Exception as e:
        return f"Connection failed with an unexpected error: {e}"

# --- Scraping Thread ---

class ScrapeThread(threading.Thread):
    """Handles the web scraping in a separate thread."""
    def __init__(self, app, url, selector, network_option, proxy_address, tor_password, tor_port, settings):
        super().__init__()
        self.app = app
        self.url = url
        self.selector = selector
        self.network_option = network_option
        self.proxy_address = proxy_address
        self.tor_password = tor_password
        self.tor_port = tor_port
        self.settings = settings
        self.running = True

    def stop(self):
        """Stops the scraping thread."""
        self.running = False

    def run(self):
        """Performs the web scraping."""
        self.app.update_progress(0)
        try:
            headers = {}
            if self.settings.get("rotate_user_agents", False):
                headers['User-Agent'] = get_random_user_agent()

            proxies = {}
            if self.network_option == "HTTP Proxy":
                if self.proxy_list:
                    # Rotate proxies with error handling
                    max_retries = len(self.proxy_list)
                    retries = 0
                    while retries < max_retries:
                        try:
                            proxy = self.proxy_list[self.current_proxy_index]
                            proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
                            
                            # Test the proxy
                            test_response = requests.get("https://api.ipify.org?format=json",
                                                       proxies=proxies,
                                                       timeout=5)
                            test_response.raise_for_status()
                            
                            # Update status with current proxy
                            self.app.status_label.config(text=f"Using proxy: {proxy}")
                            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
                            break
                        except Exception as e:
                            # Mark bad proxy and try next one
                            self.proxy_list.pop(self.current_proxy_index)
                            if not self.proxy_list:
                                raise Exception("All proxies failed")
                            if self.current_proxy_index >= len(self.proxy_list):
                                self.current_proxy_index = 0
                            retries += 1
                else:
                    proxies = {'http': f'http://{self.proxy_address}', 'https': f'http://{self.proxy_address}'}
            elif self.network_option == "Tor Network":
                proxies = {'http': f'socks5h://{self.settings.get("tor_socks_ip", "127.0.0.1")}:{self.settings.get("tor_socks_port", TOR_SOCKS_PORT)}', 'https': f'socks5h://{self.settings.get("tor_socks_ip", "127.0.0.1")}:{self.settings.get("tor_socks_port", TOR_SOCKS_PORT)}'}

            self.app.update_progress(10)
            
            # Initialize JavaScript renderer if enabled
            js_renderer = None
            if self.app.js_render_var.get():
                js_renderer = JavaScriptRenderer({
                    'timeout': self.settings.get("timeout", 10),
                    'render_wait': self.app.js_wait_var.get(),
                    'proxy': proxies.get('http') if proxies else None
                })

            # Initialize pagination handler if enabled
            if self.app.pagination_var.get():
                pagination_handler = PaginationHandler(
                    self.url,
                    self.selector,
                    {
                        'pagination_selector': 'a[href*="page"]',
                        'max_pages': self.app.max_pages_var.get(),
                        'page_delay': self.app.page_delay_var.get()
                    }
                )
                
                # Scrape all pages
                if js_renderer:
                    all_elements = []
                    for page_url in pagination_handler.get_all_page_urls():
                        soup = js_renderer.render_page(page_url)
                        all_elements.extend(soup.select(self.selector))
                else:
                    all_elements = pagination_handler.scrape_all_pages()
                    
                scraped_data = "\n".join([element.text.strip() for element in all_elements if self.running])
            else:
                # Single page scraping
                if js_renderer:
                    soup = js_renderer.render_page(self.url)
                    elements = soup.select(self.selector)
                else:
                    response = requests.get(self.url, headers=headers, proxies=proxies, timeout=self.settings.get("timeout", 10))
                    response.raise_for_status()
                    self.app.update_progress(30)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    elements = soup.select(self.selector)
                    
                scraped_data = "\n".join([element.text.strip() for element in elements if self.running])

            if self.running:
                self.app.update_progress(80)
                self.app.display_result(scraped_data)
                
                # Export to CSV if enabled
                if self.app.export_csv_var.get():
                    fields = [f.strip() for f in self.app.csv_fields_var.get().split(',')]
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".csv",
                        filetypes=[("CSV files", "*.csv")],
                        title="Save CSV File"
                    )
                    if filename:
                        CSVExporter.export(all_elements if self.app.pagination_var.get() else elements, filename, fields)
                        self.app.status_label.config(text=f"Data exported to {filename}")

                self.app.update_progress(100)
                time.sleep(self.settings.get("request_delay", 1.0))

        except requests.exceptions.RequestException as e:
            if self.running:
                self.app.show_error(f"Request Error: {e}")
        except Exception as e:
            if self.running:
                self.app.show_error(f"An unexpected error occurred: {e}")
        finally:
            if self.running:
                self.app.scraping_finished()

# --- Main Application Window ---

class WebScraperApp(tk.Tk):
    """Main application window for the web scraper."""
    def __init__(self):
        super().__init__()
        self.title("Web Scraper")
        self.state('zoomed')  # Start maximized
        self.minsize(800, 600)  # Set minimum size
        
        # Configure main window resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.settings = {}  # Initialize settings here
        self.scrape_thread = None

        # Initialize StringVar variables here
        self.url_text = tk.StringVar()  # To remember last URL
        self.proxy_address = tk.StringVar()
        self.tor_password = tk.StringVar()
        self.tor_port = tk.StringVar(value=str(DEFAULT_TOR_CONTROL_PORT))
        self.network_option = tk.StringVar(value="Own Network")
        self.selector_category_var = tk.StringVar(value="Basic Elements")
        self.selector_var = tk.StringVar()
        self.rotate_user_agents_var = tk.BooleanVar()
        self.request_delay_var = tk.DoubleVar(value=1.0)
        self.timeout_var = tk.IntVar(value=10)
        self.tor_port_var = tk.IntVar(value=DEFAULT_TOR_CONTROL_PORT)
        self.tor_socks_ip_var = tk.StringVar(value="127.0.0.1")
        self.tor_socks_port_var = tk.IntVar(value=TOR_SOCKS_PORT)
        self.create_widgets()
        self.load_settings()  # Load settings after creating widgets

        # Call these methods to update and toggle based on loaded settings
        self.update_selector_options()
        self.toggle_custom_selector_visibility()
        self.toggle_proxy_tor_fields()

    def create_widgets(self):
        """Creates and arranges GUI widgets."""
        # Styling
        style = ttk.Style(self)
        style.theme_use('clam')

        # Main container with sidebar and content area
        main_container = ttk.Frame(self)
        main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure resizing behavior
        main_container.grid_columnconfigure(0, weight=1, minsize=200)  # Sidebar
        main_container.grid_columnconfigure(1, weight=3)  # Content
        main_container.grid_rowconfigure(0, weight=1)
        
        # Sidebar frame
        sidebar_frame = ttk.Frame(main_container, width=200)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_columnconfigure(0, weight=1)
        sidebar_frame.grid_rowconfigure(0, weight=1)
        
        # Main frame inside sidebar
        main_frame = ttk.Frame(sidebar_frame, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Content Frame (Resizable)
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=0, column=1, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Configure content area widgets
        input_frame = ttk.Frame(content_frame)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=1)
        
        # Configure content area widgets
        input_frame = ttk.Frame(content_frame)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=1)
        
        # Move all settings to sidebar
        main_frame = ttk.Frame(sidebar_frame, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Pagination Frame
        pagination_frame = ttk.LabelFrame(main_frame, text="Pagination", padding=5)
        pagination_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        pagination_frame.grid_columnconfigure(0, weight=1)

        self.pagination_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(pagination_frame, text="Enable Pagination", variable=self.pagination_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(pagination_frame, text="Max Pages:").pack(side=tk.LEFT, padx=(10, 5))
        self.max_pages_var = tk.IntVar(value=10)
        ttk.Spinbox(pagination_frame, from_=1, to=1000, textvariable=self.max_pages_var, width=5).pack(side=tk.LEFT)

        ttk.Label(pagination_frame, text="Page Delay:").pack(side=tk.LEFT, padx=(10, 5))
        self.page_delay_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(pagination_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.page_delay_var, width=5).pack(side=tk.LEFT)

        # Login Frame
        login_frame = ttk.LabelFrame(main_frame, text="Login Credentials", padding=5)
        login_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        login_frame.grid_columnconfigure(0, weight=1)

        self.login_required_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(login_frame, text="Requires Login", variable=self.login_required_var).pack(side=tk.LEFT, padx=5)

        # Username
        username_label = ttk.Label(login_frame, text="Username:")
        username_label.pack(pady=(0, 5))
        self.username_var = tk.StringVar()
        ttk.Entry(login_frame, textvariable=self.username_var, width=20).pack()

        # Password
        password_label = ttk.Label(login_frame, text="Password:")
        password_label.pack(pady=(5, 0))
        self.password_var = tk.StringVar()
        ttk.Entry(login_frame, textvariable=self.password_var, show="*", width=20).pack()

        # JavaScript Rendering Frame
        js_frame = ttk.LabelFrame(main_frame, text="JavaScript Rendering", padding=5)
        js_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        js_frame.grid_columnconfigure(0, weight=1)

        self.js_render_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(js_frame, text="Enable JavaScript Rendering", variable=self.js_render_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(js_frame, text="Render Wait:").pack(side=tk.LEFT, padx=(10, 5))
        self.js_wait_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(js_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.js_wait_var, width=5).pack(side=tk.LEFT)

        # Proxy Rotation Frame
        proxy_rotation_frame = ttk.LabelFrame(main_frame, text="Proxy Rotation", padding=5)
        proxy_rotation_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        proxy_rotation_frame.grid_columnconfigure(0, weight=1)

        self.proxy_rotation_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proxy_rotation_frame, text="Enable Proxy Rotation", variable=self.proxy_rotation_var).pack(side=tk.LEFT, padx=5)

        # Proxy List
        ttk.Label(proxy_rotation_frame, text="Proxy List:").pack(anchor="w")
        self.proxy_list_var = tk.StringVar()
        proxy_entry = ttk.Entry(proxy_rotation_frame, textvariable=self.proxy_list_var, width=30)
        proxy_entry.pack(fill=tk.X, expand=True)
        
        # Load Button
        ttk.Button(proxy_rotation_frame, text="Load from File", command=self.load_proxy_list).pack(pady=(5, 0))

        # Export Frame
        export_frame = ttk.LabelFrame(main_frame, text="Export Options", padding=5)
        export_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        export_frame.grid_columnconfigure(0, weight=1)

        self.export_csv_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(export_frame, text="Export to CSV", variable=self.export_csv_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(export_frame, text="Fields:").pack(side=tk.LEFT, padx=(10, 5))
        self.csv_fields_var = tk.StringVar(value="text,href")
        ttk.Entry(export_frame, textvariable=self.csv_fields_var, width=20).pack(side=tk.LEFT)

        # Input Frame
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding=10)
        input_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        # URL
        ttk.Label(input_frame, text="URL:").grid(row=0, column=0, sticky="e")
        self.url_input = ttk.Entry(input_frame, textvariable=self.url_text)
        self.url_input.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        input_frame.columnconfigure(1, weight=1)

        # Network Options
        network_frame = ttk.Frame(input_frame)
        network_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Radiobutton(network_frame, text="Own Network", variable=self.network_option, value="Own Network", command=self.toggle_proxy_tor_fields).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(network_frame, text="HTTP Proxy", variable=self.network_option, value="HTTP Proxy", command=self.toggle_proxy_tor_fields).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(network_frame, text="Tor", variable=self.network_option, value="Tor Network", command=self.toggle_proxy_tor_fields).pack(side=tk.LEFT, padx=5)

        # Proxy and Tor Frame
        self.proxy_tor_frame = ttk.Frame(input_frame)
        self.proxy_tor_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)

        ttk.Label(self.proxy_tor_frame, text="Proxy Address:").grid(row=0, column=0, sticky="e", padx=5)
        self.proxy_address_entry = ttk.Entry(self.proxy_tor_frame, textvariable=self.proxy_address, state=tk.DISABLED)
        self.proxy_address_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.proxy_tor_frame.columnconfigure(1, weight=1)

        ttk.Label(self.proxy_tor_frame, text="Tor Control Password (optional):").grid(row=1, column=0, sticky="e", padx=5)
        self.tor_password_entry = ttk.Entry(self.proxy_tor_frame, textvariable=self.tor_password, show="*", state=tk.DISABLED)
        self.tor_password_entry.grid(row=1, column=1, sticky="ew", padx=5)

        # CSS Selector
        selector_frame = ttk.Frame(input_frame)
        selector_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Label(selector_frame, text="CSS Selector Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.selector_category_combo = ttk.Combobox(selector_frame, textvariable=self.selector_category_var, values=list(CSS_SELECTORS.keys()), state="readonly")
        self.selector_category_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.selector_category_combo.bind("<<ComboboxSelected>>", self.update_selector_options)

        self.selector_label = ttk.Label(selector_frame, text="Selector:")
        self.selector_label.pack(side=tk.LEFT, padx=(0, 5))
        self.selector_combo = ttk.Combobox(selector_frame, textvariable=self.selector_var, values=[], state="readonly")
        self.selector_combo.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.selector_combo.bind("<<ComboboxSelected>>", self.update_custom_selector_field)

        self.custom_selector_entry = ttk.Entry(selector_frame)
        self.custom_selector_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, sticky="ew", pady=(5, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)

        self.scrape_button = ttk.Button(buttons_frame, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(buttons_frame, text="Stop Scraping", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(buttons_frame, text="Clear Output", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(buttons_frame, text="Save Data", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Progress Bar in content frame
        self.progress_bar = ttk.Progressbar(content_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        content_frame.grid_rowconfigure(0, weight=0)

        # Output Text Area in content frame
        self.output_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(1, weight=1)

        # Status Bar
        self.status_label = ttk.Label(self, text="", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Menu Bar
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save Settings", command=self.save_settings)
        file_menu.add_command(label="Settings", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menu_bar)

    def update_selector_options(self, event=None):
        """Updates the selector dropdown based on the selected category."""
        category = self.selector_category_var.get()
        self.selector_combo.config(values=list(CSS_SELECTORS[category].keys()))
        self.selector_combo.set('')  # Clear the selector combo box
        self.toggle_custom_selector_visibility()

    def toggle_custom_selector_visibility(self):
        """Toggles the visibility of the custom CSS selector input."""
        if self.selector_combo.get():
            self.custom_selector_entry.pack_forget()
        else:
            self.custom_selector_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle_proxy_tor_fields(self):
        """Shows/hides proxy and Tor fields based on the selected network option."""
        network = self.network_option.get()
        self.proxy_address_entry.config(state=tk.NORMAL if network == "HTTP Proxy" else tk.DISABLED)
        self.tor_password_entry.config(state=tk.NORMAL if network == "Tor Network" else tk.DISABLED)

        # Clear fields when disabling
        if network != "HTTP Proxy":
            self.proxy_address.set("")
        if network != "Tor Network":
            self.tor_password.set("")

    def update_custom_selector_field(self, event=None):
        """Updates the custom selector field based on the selected CSS selector."""
        selected_category = self.selector_category_var.get()
        selected_selector = self.selector_combo.get()
        if selected_selector and selected_selector in CSS_SELECTORS[selected_category]:
            self.custom_selector_entry.delete(0, tk.END)
            self.custom_selector_entry.insert(0, CSS_SELECTORS[selected_category][selected_selector])
        else:
            self.custom_selector_entry.delete(0, tk.END)

    def perform_login(self, session, url, username, password):
        """Performs login on the given URL using provided credentials."""
        try:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Identify login form elements (adjust selectors as needed)
            form = soup.find('form')
            if not form:
                self.show_error("Login form not found.")
                return False
            
            inputs = form.find_all('input')
            login_data = {}
            for input_field in inputs:
                name = input_field.get('name')
                input_type = input_field.get('type')
                if name:
                    if input_type == 'text' or input_type == 'email':
                        login_data[name] = username
                    elif input_type == 'password':
                        login_data[name] = password
                    else:
                        login_data[name] = input_field.get('value', '')  # For hidden fields, etc.

            # Identify submit URL (form action)
            login_url = response.urljoin(form.get('action')) if form.get('action') else url

            # Submit the login form
            login_response = session.post(login_url, data=login_data)
            login_response.raise_for_status()

            if login_response.url == url or "logout" in login_response.text.lower():
                self.status_label.config(text="Login successful.")
                return True
            else:
                self.show_error("Login failed. Please check your credentials.")
                return False

        except requests.exceptions.RequestException as e:
            self.show_error(f"Login request error: {e}")
            return False
        except Exception as e:
            self.show_error(f"Login error: {e}")
            return False

    def start_scraping(self):
        """Starts the web scraping process."""
        url = self.url_input.get().strip()
        network_option = self.network_option.get()
        proxy_address = self.proxy_address.get().strip()
        tor_password = self.tor_password.get()
        tor_port = int(self.tor_port.get()) if self.tor_port.get() else DEFAULT_TOR_CONTROL_PORT
        selector_category = self.selector_category_var.get()
        selector_value = self.selector_combo.get()
        selector = self.custom_selector_entry.get().strip()
        tor_socks_ip = self.tor_socks_ip_var.get()
        tor_socks_port = self.tor_socks_port_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
        elif selector_category != "Custom" and not selector_value and selector_category != "Whole Website":
            messagebox.showerror("Error", "Please select a CSS selector or use a custom one.")
        elif selector_category == "Custom" and not selector:
            messagebox.showerror("Error", "Please enter a custom CSS selector.")
        elif network_option == "HTTP Proxy" and not proxy_address:
            messagebox.showerror("Error", "Please enter a proxy address.")
        else:
            if selector_category == "Whole Website":
                selector = "*"
            elif selector_category != "Custom":
                selector = CSS_SELECTORS[selector_category][selector_value]

            # Test connection before starting scraping
            connection_status = test_connection(network_option, proxy_address, tor_password, tor_port, tor_socks_ip, tor_socks_port)
            if "successful" not in connection_status:
                messagebox.showerror("Connection Error", connection_status)
                return

            self.status_label.config(text="Scraping...")
            self.progress_bar['value'] = 0
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state=tk.DISABLED)
            self.scrape_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.clear_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)

            self.scrape_thread = ScrapeThread(self, url, selector, network_option, proxy_address, tor_password, tor_port, self.settings)
            self.scrape_thread.start()

    def stop_scraping(self):
        """Stops the scraping thread."""
        if self.scrape_thread and self.scrape_thread.is_alive():
            self.scrape_thread.stop()
            self.scrape_thread.join() # Wait for the thread to finish
            self.status_label.config(text="Scraping stopped by user.")
            self.scrape_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.clear_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)

    def update_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar["value"] = value
        self.update_idletasks()

    def display_result(self, data):
        """Displays the scraped data in the output area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, data + "\n") # Added newline for better readability
        self.output_text.config(state=tk.DISABLED)

    def show_error(self, message):
        """Displays an error message in the status bar and a messagebox."""
        self.status_label.config(text=f"Error: {message}")
        messagebox.showerror("Error", message)

    def scraping_finished(self):
        """Resets GUI elements after scraping is finished."""
        self.status_label.config(text="Scraping complete!")
        self.scrape_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)

    def on_closing(self):
        """Handles the closing of the application window."""
        self.stop_scraping()
        if self.winfo_exists():
            try:
                # Get the value of tor_port_var before potentially being destroyed
                tor_port_value = self.tor_port_var.get()
                self.save_settings(tor_port_override=tor_port_value) # Pass the value explicitly
            except Exception as e:
                print(f"Error saving settings during closing: {e}")
        self.destroy()

    def clear_output(self):
        """Clears the output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)

    def load_proxy_list(self):
        """Loads a list of proxies from a file."""
        file_path = filedialog.askopenfilename(
            title="Select Proxy List File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=DEFAULT_SAVE_DIR
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    proxies = f.read().splitlines()
                    self.proxy_list_var.set(",".join(proxies))
                    messagebox.showinfo("Success", f"Loaded {len(proxies)} proxies")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load proxy list: {e}")

    def save_data(self):
        """Saves the scraped data to a file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=DEFAULT_SAVE_DIR
        )
        if file_path:
            try:
                data_to_save = self.output_text.get(1.0, tk.END)
                if file_path.endswith(".md"):
                    # Format as Markdown (treat each line as a paragraph)
                    lines = data_to_save.strip().split('\n')
                    markdown_data = "\n\n".join(lines)
                    data_to_save = markdown_data

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(data_to_save)
                messagebox.showinfo("Success", "Data saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {e}")

    def open_settings(self):
        """Opens the settings window."""
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x350")
        settings_window.resizable(False, False)

        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(settings_window, text="Configuration", padding=(10, 10))
        settings_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # --- User Agent Rotation ---
        self.rotate_user_agents_var = tk.BooleanVar(value=self.settings.get("rotate_user_agents", False))
        ttk.Checkbutton(settings_frame, text="Rotate User Agents", variable=self.rotate_user_agents_var,
                        command=lambda: self.show_hint("Randomly rotate user agents for each request.")).pack(anchor="w")

        # --- Request Delay ---
        ttk.Label(settings_frame, text="Request Delay (seconds):").pack(anchor="w")
        self.request_delay_var = tk.DoubleVar(value=self.settings.get("request_delay", 1.0))
        ttk.Spinbox(settings_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.request_delay_var, width=5,
                    command=lambda: self.show_hint("Delay between requests to avoid overloading the server.")).pack(anchor="w")

        # --- Timeout ---
        ttk.Label(settings_frame, text="Request Timeout (seconds):").pack(anchor="w")
        self.timeout_var = tk.IntVar(value=self.settings.get("timeout", 10))
        ttk.Spinbox(settings_frame, from_=1, to=60, increment=1, textvariable=self.timeout_var, width=5,
                    command=lambda: self.show_hint("Maximum time to wait for a response from the server.")).pack(anchor="w")

        # --- Tor Control Port ---
        ttk.Label(settings_frame, text="Tor Control Port:").pack(anchor="w")
        self.tor_port_var_settings = tk.IntVar(value=self.settings.get("tor_port", DEFAULT_TOR_CONTROL_PORT)) # Use a separate variable for the settings window
        ttk.Spinbox(settings_frame, from_=1024, to=65535, increment=1, textvariable=self.tor_port_var_settings, width=7,
                    command=lambda: self.show_hint("Port for Tor control interface.")).pack(anchor="w")

        # --- Tor Browser Settings ---
        tor_browser_frame = ttk.LabelFrame(settings_frame, text="Tor Browser", padding=(5, 5))
        tor_browser_frame.pack(fill="x", expand=True, pady=(5, 0))

        ttk.Label(tor_browser_frame, text="SOCKS IP:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.tor_socks_ip_var_settings = tk.StringVar(value=self.settings.get("tor_socks_ip", "127.0.0.1"))
        ttk.Entry(tor_browser_frame, textvariable=self.tor_socks_ip_var_settings, width=15).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        tor_browser_frame.columnconfigure(1, weight=1)

        ttk.Label(tor_browser_frame, text="SOCKS Port:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.tor_socks_port_var_settings = tk.IntVar(value=self.settings.get("tor_socks_port", TOR_SOCKS_PORT))
        ttk.Spinbox(tor_browser_frame, from_=1, to=65535, increment=1, textvariable=self.tor_socks_port_var_settings, width=7).grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # --- Save Settings Button ---
        ttk.Button(settings_window, text="Save Settings", command=self.save_settings_from_window).pack(pady=20)

    def load_settings(self):
        """Loads settings from the settings file."""
        try:
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {}

        # Apply loaded settings to the main application
        self.url_text.set(self.settings.get("url", ""))
        self.network_option.set(self.settings.get("network_option", "Own Network"))
        self.proxy_address.set(self.settings.get("proxy_address", ""))
        self.tor_password.set(self.settings.get("tor_password", ""))
        self.tor_port.set(str(self.settings.get("tor_port", DEFAULT_TOR_CONTROL_PORT)))
        self.tor_socks_ip_var.set(self.settings.get("tor_socks_ip", "127.0.0.1"))
        self.tor_socks_port_var.set(self.settings.get("tor_socks_port", TOR_SOCKS_PORT))
        self.selector_category_var.set(self.settings.get("selector_category", "Basic Elements"))
        self.update_selector_options()
        self.selector_var.set(self.settings.get("selector", ""))
        self.custom_selector_entry.delete(0, tk.END)
        self.custom_selector_entry.insert(0, self.settings.get("custom_selector", ""))
        self.rotate_user_agents_var.set(self.settings.get("rotate_user_agents", False))
        self.request_delay_var.set(self.settings.get("request_delay", 1.0))
        self.timeout_var.set(self.settings.get("timeout", 10))
        self.toggle_proxy_tor_fields()

    def save_settings(self, tor_port_override=None):
        """Saves settings to the settings file."""
        self.settings["url"] = self.url_text.get()
        self.settings["network_option"] = self.network_option.get()
        self.settings["proxy_address"] = self.proxy_address.get()
        self.settings["tor_password"] = self.tor_password.get()
        self.settings["tor_port"] = tor_port_override if tor_port_override is not None else self.tor_port_var.get()
        self.settings["tor_socks_ip"] = self.tor_socks_ip_var.get()
        self.settings["tor_socks_port"] = self.tor_socks_port_var.get()
        self.settings["selector_category"] = self.selector_category_var.get()
        self.settings["selector"] = self.selector_var.get()
        self.settings["custom_selector"] = self.custom_selector_entry.get()
        self.settings["rotate_user_agents"] = self.rotate_user_agents_var.get()
        self.settings["request_delay"] = self.request_delay_var.get()
        self.settings["timeout"] = self.timeout_var.get()

        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")

    def save_settings_from_window(self):
        """Saves settings from the settings window to the settings file."""
        self.settings["rotate_user_agents"] = self.rotate_user_agents_var.get()
        self.settings["request_delay"] = self.request_delay_var.get()
        self.settings["timeout"] = self.timeout_var.get()
        self.settings["tor_port"] = self.tor_port_var_settings.get()
        self.settings["tor_socks_ip"] = self.tor_socks_ip_var_settings.get()
        self.settings["tor_socks_port"] = self.tor_socks_port_var_settings.get()

        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
        # Update main app variables with settings from settings window
        self.tor_port_var.set(self.settings["tor_port"])
        self.tor_socks_ip_var.set(self.settings["tor_socks_ip"])
        self.tor_socks_port_var.set(self.settings["tor_socks_port"])

    def show_hint(self, message):
        """Displays a hint in the status bar."""
        self.status_label.config(text=message)

    def hide_hint(self, event):
        """Clears the hint from the status bar."""
        self.status_label.config(text="")

    def show_help(self):
        """Displays a help message."""
        help_text = """
        Web Scraper Help

        1. Enter the URL of the website you want to scrape.
        2. Select a network option:
           - Own Network: Use your own internet connection.
           - HTTP Proxy: Use a specified HTTP proxy. Enter the proxy address.
           - Tor Network: Use the Tor network for anonymity. Leave the Tor Control Password field empty if you have configured Tor for passwordless control (by commenting out 'HashedControlPassword' and ensuring 'ControlPort' is enabled in your torrc file). Otherwise, enter your Tor control password.
        3. Choose a CSS selector category and then a specific selector, or enter a custom one.
        4. Click 'Start Scraping' to begin.
        5. The progress bar will show the scraping progress.
        6. The scraped data will appear in the output area.
        7. Click 'Stop Scraping' to halt the process.
        8. Click 'Clear Output' to clear the output area.
        9. Click 'Save Data' to save the output to a text file.
        10. Go to 'File > Settings' to configure advanced settings like user agent rotation, request delay and Tor control port.

        Note: Ensure that you comply with the website's terms of service and robots.txt when scraping.
        """
        messagebox.showinfo("Help", help_text)

# --- Tor Network Control Functions ---

def renew_tor_identity(password, port):
    """Renews Tor's IP address."""
    try:
        with Controller.from_port(port=port) as controller:
            if password:
                controller.authenticate(password=password)
            controller.signal(Signal.NEWNYM)
            print("Tor identity renewed.")
            time.sleep(5)
            return True
    except Exception as e:
        print(f"Error renewing Tor identity: {e}")
        return False

def check_tor_connection():
    """Checks if the connection is going through Tor."""
    try:
        response = requests.get("https://check.torproject.org/", proxies={
            'http': f'socks5h://{settings.get("tor_socks_ip", "127.0.0.1")}:{settings.get("tor_socks_port", TOR_SOCKS_PORT)}',
            'https': f'socks5h://{settings.get("tor_socks_ip", "127.0.0.1")}:{settings.get("tor_socks_port", TOR_SOCKS_PORT)}'
        }, timeout=5)
        return "Congratulations. This browser is configured to use Tor." in response.text
    except Exception:
        return False

# --- Removing Tor Control Passwords ---

def remove_tor_passwords(torrc_path):
    """Removes the hashed control password from the torrc file."""
    try:
        with open(torrc_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.strip().startswith("HashedControlPassword") or line.strip().startswith("ControlPort"):
                # Comment out or remove these lines
                # new_lines.append(f"# {line}")  # Option 1: Comment out
                pass  # Option 2: Remove the lines
            else:
                new_lines.append(line)

        with open(torrc_path, "w") as f:
            f.writelines(new_lines)

        print(f"Tor control password removed from {torrc_path}. Restart Tor for changes to take effect.")

    except FileNotFoundError:
        print(f"Error: torrc file not found at {torrc_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    app = WebScraperApp()
    app.mainloop()

    # --- Example usage of remove_tor_passwords() ---
    # torrc_path = r"C:\Users\[Your Username]\Desktop\Tor Browser\Browser\TorBrowser\Data\Tor\torrc"  # Adjust path if needed
    # remove_tor_passwords(torrc_path)