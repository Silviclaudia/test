import threading
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from app import create_app, db
from app.models import User

class SeleniumTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        cls.driver = webdriver.Chrome(options=options)

        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

        cls.server_thread = threading.Thread(
            target=lambda: cls.app.run(port=5001, debug=False, use_reloader=False)
        )
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        
        time.sleep(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        db.drop_all()
        cls.app_context.pop()

    def test_1_home_page_title(self):
        self.driver.get("http://127.0.0.1:5001/")
        self.assertIn("Dashboard", self.driver.title)

    def test_2_navigation_to_login(self):
        self.driver.get("http://127.0.0.1:5001/")
        login_link = self.driver.find_element(By.LINK_TEXT, "Sign In")
        login_link.click()
        self.assertIn("/login", self.driver.current_url)

    def test_3_registration_elements(self):
        self.driver.get("http://127.0.0.1:5001/register")
        self.assertTrue(self.driver.find_element(By.NAME, "username").is_displayed())
        self.assertTrue(self.driver.find_element(By.NAME, "email").is_displayed())

    def test_4_terms_and_conditions_link(self):
        """Ensure the terms link opens the correct document."""
        self.driver.get("http://127.0.0.1:5001/register")
        self.driver.find_element(By.LINK_TEXT, "Terms and Conditions").click()
        self.assertIn("Terms & Conditions", self.driver.page_source)

    def test_5_responsive_header(self):
        self.driver.set_window_size(800, 600)
        self.driver.get("http://127.0.0.1:5001/")
        brand = self.driver.find_element(By.CLASS_NAME, "brand")
        self.assertTrue(brand.is_displayed())