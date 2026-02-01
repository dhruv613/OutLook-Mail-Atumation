import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class Locators:
    def __init__(self):
        with open("automation/locators.json", "r") as file:
            self.locators = json.load(file)

    def find(self, driver, key):
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
                try:
                    return driver.find_element(by, value)
                except NoSuchElementException:
                    pass

        raise Exception(f"Element not found using any method for key: {key}")
