# Web Scraper Application

This Python application provides a graphical user interface (GUI) for web scraping. It allows users to extract data from websites using CSS selectors, with options to use their own network, HTTP proxies, or the Tor network for enhanced privacy.

## Features

* **User-Friendly GUI:** Built with Tkinter for an intuitive user experience.
* **CSS Selector Support:** Extract data based on various CSS selectors, including basic elements, headings, text, lists, tables, media, attributes, combinators, pseudo-classes, and form elements. Custom CSS selectors are also supported.
* **Network Options:**
    * **Own Network:** Scrape directly using your internet connection.
    * **HTTP Proxy:** Route requests through an HTTP proxy server.
    * **Tor Network:** Anonymize your requests using the Tor network. Supports optional Tor control password.
* **Tor Browser Settings:** Configure Tor SOCKS IP and port directly from the settings.
* **Settings Management:** Save and load application settings, including network configurations, request delays, timeouts, and Tor settings.
* **User Agent Rotation:** Option to randomly rotate user agents for each request to reduce the chance of being blocked.
* **Request Delay:** Set a delay between requests to avoid overloading servers.
* **Progress Tracking:** A progress bar visually indicates the scraping process.
* **Data Output:** Displays scraped data in a scrollable text area.
* **Data Saving:** Save the scraped data to a text or Markdown file.
* **Help Menu:** Provides instructions on how to use the application.

## Requirements

* Python 3.6 or higher
* Required Python libraries:
    * `tkinter`
    * `requests`
    * `beautifulsoup4`
    * `stem`

You can install the required libraries using pip:

```bash
pip install requests beautifulsoup4 stem
```

## How to Use

1. **Run the application:** Execute the Python script `main.py`.
2. **Enter the URL:** In the "Input" section, enter the URL of the website you want to scrape.
3. **Select a Network Option:**
    * Choose "Own Network" to use your direct internet connection.
    * Choose "HTTP Proxy" and enter the proxy address in the format `ip:port`.
    * Choose "Tor Network". If your Tor browser requires a control password, enter it.
4. **Configure Tor Browser Settings (if using Tor):** Go to "File > Settings" and configure the "Tor Browser" section with the correct SOCKS IP and port (usually `127.0.0.1:9150` for the Tor Browser).
5. **Select CSS Selectors:**
    * Choose a category from the "CSS Selector Category" dropdown.
    * Select a predefined selector from the "Selector" dropdown, or manually enter a custom CSS selector in the text field.
6. **Start Scraping:** Click the "Start Scraping" button. The progress will be shown in the progress bar, and the extracted data will appear in the output area.
7. **Stop Scraping (Optional):** If needed, you can halt the scraping process by clicking "Stop Scraping".
8. **Clear Output:** Click "Clear Output" to clear the text area.
9. **Save Data:** Click "Save Data" to save the scraped content to a file. You can choose between `.txt` and `.md` formats.
10. **Adjust Settings:** Go to "File > Settings" to adjust parameters like user agent rotation, request delay, timeout, and Tor control port.

## Executable File

An executable file has been created for this application and is located in the `dist` directory. The file is named `main.exe`. You can run this executable directly without needing to install Python or any dependencies.

## Settings Menu

The "Settings" menu under "File" allows you to configure the following:

* **Rotate User Agents:** Enable or disable random user agent rotation.
* **Request Delay (seconds):** Set the delay between consecutive requests.
* **Request Timeout (seconds):** Set the maximum time to wait for a server response.
* **Tor Control Port:** Configure the Tor control port.
* **Tor Browser Settings:**
    * **SOCKS IP:** The IP address for the Tor SOCKS proxy (default: `127.0.0.1`).
    * **SOCKS Port:** The port for the Tor SOCKS proxy (default: `9150`).

## Help

For more detailed instructions, click "Help" in the menu bar.

## Disclaimer

Please use this application responsibly and ethically. Ensure you understand and comply with the target website's terms of service and robots.txt file before scraping. Avoid overloading websites with excessive requests.

## Contributing

Contributions to this project are welcome. Please feel free to fork the repository and submit pull requests.

## License

(MIT License)
