
import csv
import time
import re
import os
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import SessionNotCreatedException

class FlipkartScraper:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_top_reviews(self, product_url, count=2):
        """Get the top reviews for a product."""
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        try:
            driver = uc.Chrome(options=options, use_subprocess=True)
        except SessionNotCreatedException as e:
            print(f"Error initializing Chrome driver: {e}")
            return "Error: Driver version mismatch."

        if not product_url.startswith("http"):
            if 'driver' in locals() and driver:
                driver.quit()
            return "No reviews found"

        try:
            driver.get(product_url)
            time.sleep(4)
            try:
                driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
                time.sleep(1)
            except Exception:
                pass

            for _ in range(4):
                ActionChains(driver).send_keys(Keys.END).perform()
                time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            review_blocks = soup.select("div._27M-vq, div.col.EPCmJX, div._6K-7Co")
            seen = set()
            reviews = []

            for block in review_blocks:
                text = block.get_text(separator=" ", strip=True)
                if text and text not in seen:
                    reviews.append(text)
                    seen.add(text)
                if len(reviews) >= count:
                    break
        except Exception as e:
            print(f"An error occurred during review scraping: {e}")
            reviews = []
        finally:
            if 'driver' in locals() and driver:
                driver.quit()

        return " || ".join(reviews) if reviews else "No reviews found"

    def scrape_flipkart_products(self, query, max_products=1, review_count=2):
        """Scrape Flipkart products based on a search query."""
        try:
            options = uc.ChromeOptions()
            driver = uc.Chrome(options=options, use_subprocess=True)
            search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(4)

            try:
                driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
            except Exception:
                pass

            time.sleep(2)
            products = []
            items = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")[:max_products]
            
            for item in items:
                try:
                    title = item.find_element(By.CSS_SELECTOR, "div.KzDlHH").text.strip()
                    price = item.find_element(By.CSS_SELECTOR, "div.Nx9bqj").text.strip()
                    rating = item.find_element(By.CSS_SELECTOR, "div.XQDdHH").text.strip()
                    reviews_text = item.find_element(By.CSS_SELECTOR, "span.Wphh3N").text.strip()
                    match = re.search(r"[\d,]+(?=\s+Reviews)", reviews_text)
                    total_reviews = match.group(0) if match else "N/A"

                    link_el = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
                    href = link_el.get_attribute("href")
                    product_link = href if href.startswith("http") else "https://www.flipkart.com" + href
                    match = re.findall(r"/p/(itm[0-9A-Za-z]+)", href)
                    product_id = match[0] if match else "N/A"
                except Exception as e:
                    print(f"Error processing item: {e}")
                    continue

                top_reviews = self.get_top_reviews(product_link, count=review_count)
                products.append([product_id, title, rating, total_reviews, price, top_reviews])
            if 'driver' in locals() and driver:
                driver.quit()
            return products
        except SessionNotCreatedException as e:
            print(f"Session not created error: {e}. Scraping will not proceed.")
            if os.path.exists("data/product_reviews.csv"):
                print("Falling back to existing CSV data.")
                with open("data/product_reviews.csv", "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    return list(reader)
            return []
        except Exception as e:
            print(f"An unexpected error occurred during scraping: {e}")
            return []
    def save_to_csv(self, data, filename="product_reviews.csv"):
        """Save the scraped product reviews to a CSV file."""
        path = os.path.join(self.output_dir, os.path.basename(filename))
        
        print(f"Saving data to: {path}")
        os.makedirs(self.output_dir, exist_ok=True)
        
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "product_title", "rating", "total_reviews", "price", "top_reviews"])
            writer.writerows(data)
