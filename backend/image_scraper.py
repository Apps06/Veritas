"""
Image Scraper for Veritas Training Data Collection
Collects AI-generated and real images from various sources
"""
import os
import requests
import hashlib
import time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class ImageScraper:
    """Scrapes images from web sources for training data"""
    
    def __init__(self, base_dir="training_data"):
        self.base_dir = Path(base_dir)
        self.ai_dir = self.base_dir / "ai"
        self.real_dir = self.base_dir / "real"
        
        # Create directories
        self.ai_dir.mkdir(parents=True, exist_ok=True)
        self.real_dir.mkdir(parents=True, exist_ok=True)
        
        self.headers = {
            "User-Agent": "Veritas-Scraper/1.0 (Educational Research)"
        }
        
        self.collected = {"ai": 0, "real": 0}
    
    def _save_image(self, url, category, prefix=""):
        """Download and save an image"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                # Generate unique filename from URL hash
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                ext = url.split('.')[-1].split('?')[0][:4]
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
                
                filename = f"{prefix}_{url_hash}.{ext}"
                
                save_dir = self.ai_dir if category == "ai" else self.real_dir
                filepath = save_dir / filename
                
                if not filepath.exists():
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    self.collected[category] += 1
                    print(f"✓ Saved {category}: {filename}")
                    return True
        except Exception as e:
            print(f"✗ Failed to save {url[:50]}...: {e}")
        return False
    
    def scrape_thispersondoesnotexist(self, count=50):
        """Scrape AI-generated faces from thispersondoesnotexist.com"""
        print(f"\n📷 Scraping AI faces (target: {count})...")
        
        for i in range(count):
            # This site generates a new face each request
            url = f"https://thispersondoesnotexist.com/?{int(time.time()*1000)+i}"
            self._save_image(url, "ai", "gan_face")
            time.sleep(1)  # Be respectful
        
        print(f"Collected {self.collected['ai']} AI images so far")
    
    def scrape_unsplash(self, query="portrait photo", count=50):
        """Scrape real photos from Unsplash (requires API key or scraping)"""
        print(f"\n📷 Scraping real photos from Unsplash (target: {count})...")
        
        # Use Unsplash source for random images (no API key needed)
        for i in range(count):
            url = f"https://source.unsplash.com/random/512x512/?{query}&sig={i}"
            self._save_image(url, "real", "unsplash")
            time.sleep(0.5)
        
        print(f"Collected {self.collected['real']} real images so far")
    
    def scrape_picsum(self, count=50):
        """Scrape real photos from Lorem Picsum"""
        print(f"\n📷 Scraping real photos from Picsum (target: {count})...")
        
        for i in range(count):
            url = f"https://picsum.photos/512/512?random={i}"
            self._save_image(url, "real", "picsum")
            time.sleep(0.3)
        
        print(f"Collected {self.collected['real']} real images so far")
    
    def scrape_lexica_ai(self, count=50):
        """Scrape AI art from Lexica.art (Stable Diffusion showcase)"""
        print(f"\n📷 Scraping AI art from Lexica (target: {count})...")
        
        try:
            # Lexica has a public API
            response = requests.get(
                "https://lexica.art/api/v1/search",
                params={"q": "portrait realistic photo"},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                images = data.get("images", [])[:count]
                
                for img in images:
                    url = img.get("src") or img.get("srcSmall")
                    if url:
                        self._save_image(url, "ai", "lexica")
                        time.sleep(0.3)
        except Exception as e:
            print(f"Lexica scraping failed: {e}")
        
        print(f"Collected {self.collected['ai']} AI images so far")
    
    def collect_dataset(self, images_per_source=100):
        """Run full collection pipeline"""
        print("=" * 50)
        print("Veritas Training Data Collection")
        print("=" * 50)
        
        # Collect AI images
        self.scrape_thispersondoesnotexist(images_per_source // 2)
        self.scrape_lexica_ai(images_per_source // 2)
        
        # Collect real images
        self.scrape_unsplash("portrait photograph", images_per_source // 2)
        self.scrape_picsum(images_per_source // 2)
        
        print("\n" + "=" * 50)
        print(f"Collection Complete!")
        print(f"  AI Images: {self.collected['ai']}")
        print(f"  Real Images: {self.collected['real']}")
        print(f"  Saved to: {self.base_dir.absolute()}")
        print("=" * 50)
        
        return self.collected


if __name__ == "__main__":
    scraper = ImageScraper()
    scraper.collect_dataset(images_per_source=100)
