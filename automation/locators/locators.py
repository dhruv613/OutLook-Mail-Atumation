import orjson
import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

class Locators:
    def __init__(self):
        base_path = os.path.dirname(__file__)
        json_path = os.path.join(base_path, "locators.json")
        with open(json_path, "rb") as file:
            self.locators = orjson.loads(file.read())

    def find(self, driver, key):
        """
        Tries to find an element using all available strategies defined in the JSON.
        Returns the first successfully found element.
        """
        locator = self.locators.get(key)
        if not locator:
            raise Exception(f"Locator key not found: {key}")

        methods = [
            ("id", By.ID),
            ("name", By.NAME),
            ("css", By.CSS_SELECTOR),
            ("xpath", By.XPATH),
            ("link_text", By.LINK_TEXT)
        ]

        for method_key, by in methods:
            value = locator.get(method_key)
            if value:
                # Handle list of values (e.g. multiple XPaths)
                if isinstance(value, list):
                    for v in value:
                        try:
                            return driver.find_element(by, v)
                        except (NoSuchElementException, WebDriverException):
                            pass
                else:
                    try:
                        return driver.find_element(by, value)
                    except (NoSuchElementException, WebDriverException):
                        pass

        raise Exception(f"Element not found using any method for key: {key}")

    def get_locators(self, key):
        """
        Returns a list of tuples (By, value) for all valid strategies for the given key.
        This allows the caller to try multiple strategies (e.g. ID, then XPath).
        """
        locator = self.locators.get(key)
        if not locator:
            raise Exception(f"Locator key not found: {key}")

        methods = [
            ("id", By.ID),
            ("name", By.NAME),
            ("css", By.CSS_SELECTOR),
            ("xpath", By.XPATH),
            ("link_text", By.LINK_TEXT)
        ]

        strategies = []
        for method_key, by in methods:
            value = locator.get(method_key)
            if value:
                if isinstance(value, list):
                    # Flatten list into multiple strategies
                    for v in value:
                        strategies.append((by, v))
                else:
                    strategies.append((by, value))
        
        if not strategies:
            raise Exception(f"No valid locator found for key: {key}")
            
        return strategies

    def get_js(self, key):
        """
        Returns the raw JS selector string for a given key.
        """
        locator = self.locators.get(key)
        if not locator:
            raise Exception(f"Locator key not found: {key}")
        
        js_val = locator.get("js")
        if not js_val:
            raise Exception(f"No 'js' key found for locator: {key}")
            
        return js_val

