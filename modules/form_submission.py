import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class FormSubmitter:
    def __init__(self, settings):
        self.settings = settings
        self.session = requests.Session()
        
    def detect_login_form(self, url):
        """Detect login form on a page"""
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        forms = soup.find_all('form')
        login_forms = []
        
        for form in forms:
            inputs = form.find_all('input')
            has_username = any(i.get('name', '').lower() in ['username', 'email', 'login'] for i in inputs)
            has_password = any(i.get('type') == 'password' for i in inputs)
            
            if has_username and has_password:
                login_forms.append({
                    'action': urljoin(url, form.get('action', '')),
                    'method': form.get('method', 'get').upper(),
                    'inputs': {i.get('name'): i.get('value', '') for i in inputs if i.get('name')}
                })
                
        return login_forms
        
    def submit_login_form(self, form_data, credentials):
        """Submit login form with credentials"""
        # Update form data with credentials
        form_data['inputs'].update({
            'username': credentials.get('username'),
            'password': credentials.get('password')
        })
        
        if form_data['method'] == 'POST':
            response = self.session.post(
                form_data['action'],
                data=form_data['inputs'],
                headers={'Referer': form_data['action']}
            )
        else:
            response = self.session.get(
                form_data['action'],
                params=form_data['inputs']
            )
            
        return response
        
    def is_logged_in(self, response):
        """Check if login was successful"""
        # Implement custom logic to check for login success
        # This could be checking for a specific element, cookie, or redirect
        return 'logout' in response.text.lower() or 'welcome' in response.text.lower()