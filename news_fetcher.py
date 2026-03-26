import feedparser
import requests
import os
from datetime import datetime

# 1. 설정: 서버 주소
SERVER_URL = "https://dividend-server.onrender.com/update_intel"

# 2. 뉴스 소스 (국내 & 해외 경제 RSS)
NEWS_SOURCES = {
    "국내경제": "https://www.mk.co.kr/rss/30100041/", # 매일경제 경제섹션
    "해외경제": "https://www.investing.com/rss/news_285.rss" # 인베스팅닷컴 글로벌 뉴스
}

def fetch_and_send_news():
    print(f"📡 뉴스 수집 시작... {datetime.now()}")
    
    for category, url in NEWS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            # 각 소스별 최신 5개 기사만 추출
            for entry in feed.entries[:5]:
                news_data = {
                    "type": "NEWS",
                    "source": category,
                    "title": entry.title,
                    "link": entry.link,
                    "date": entry.published if 'published' in entry else "방금 전"
                }
                
                # 서버로 전송
                res = requests.post(SERVER_URL, json=news_data, timeout=10)
                if res.status_code == 200:
                    print(f"✅ 뉴스 전송 성공: {entry.title[:20]}...")
                
        except Exception as e:
            print(f"❌ {category} 수집 실패: {e}")

if __name__ == "__main__":
    fetch_and_send_news()