import requests
import xml.etree.ElementTree as ET
import time
import logging
from utils.network_policy import allow_external_news, guard_outbound_url

CACHE = {
    'data': None,
    'timestamp': 0
}

CACHE_DURATION = 3600  # 1 hour

def get_latest_tech_news():
    """
    Fetches the latest news from a public RSS feed (Infobae - Noticias Argentinas).
    Caches the result for 1 hour to prevent slow page loads and rate limiting.
    Returns a list of news titles (strings).
    """
    global CACHE
    now = time.time()

    if not allow_external_news():
        return []
    
    if CACHE['data'] and (now - CACHE['timestamp']) < CACHE_DURATION:
        return CACHE['data']
        
    try:
        url = "https://www.infobae.com/arc/outboundfeeds/rss/"
        guard_outbound_url(url, purpose="news")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            response.encoding = 'utf-8'
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            if items:
                # Extraer hasta 10 titulares de noticias
                news_list = [item.findtext('title') for item in items[:10] if item.findtext('title')]
                
                if news_list:
                    CACHE['data'] = news_list
                    CACHE['timestamp'] = now
                    return news_list
                
    except Exception as e:
        logging.error(f"[TECH NEWS] Failed to fetch news: {e}")
        
    return []
