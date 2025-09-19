#!/usr/bin/env python3
import requests
import sqlite3
import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
import feedparser
from bs4 import BeautifulSoup
import praw
import subprocess
import os
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class NewsSourceManager:
    """뉴스 소스 관리자"""

    def __init__(self):
        # API 키 설정 (환경변수 또는 직접 설정)
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')  # NewsAPI.org 키

        # Reddit 설정
        self.reddit = None
        self.setup_reddit()

        # 헤더 설정 (웹 스크래핑용)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 한국 뉴스 RSS 피드
        self.korean_rss_feeds = {
            'naver_finance': 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258',
            'hankyung': 'https://www.hankyung.com/feed/stock',
            'maeil': 'https://www.mk.co.kr/rss/30300001/',
            'seoul_finance': 'http://www.sedaily.com/RSS/S11.xml'
        }

        # 종목 키워드 매핑
        self.symbol_keywords = {
            # 미국 주식
            'AAPL': ['Apple', 'iPhone', 'iPad', 'Mac', 'Tim Cook', '애플'],
            'MSFT': ['Microsoft', 'Windows', 'Azure', 'Office', 'Teams', '마이크로소프트'],
            'GOOGL': ['Google', 'Alphabet', 'YouTube', 'Android', 'Chrome', '구글'],
            'AMZN': ['Amazon', 'AWS', 'Alexa', 'Prime', 'Bezos', '아마존'],
            'TSLA': ['Tesla', 'Elon Musk', 'Model', 'electric vehicle', 'EV', '테슬라'],
            'META': ['Meta', 'Facebook', 'Instagram', 'WhatsApp', 'Metaverse', '메타'],
            'NVDA': ['NVIDIA', 'GPU', 'AI chip', 'gaming', 'datacenter', '엔비디아'],

            # 한국 주식
            '005930.KS': ['삼성전자', 'Samsung Electronics', '갤럭시', 'Galaxy', '반도체', '스마트폰'],
            '000660.KS': ['SK하이닉스', 'SK Hynix', '메모리', 'DRAM', 'NAND'],
            '035420.KS': ['NAVER', '네이버', '라인', 'Line', '웹툰', '검색'],
            '005490.KS': ['POSCO', '포스코', '철강', '스틸'],
            '051910.KS': ['LG화학', 'LG Chem', '배터리', '전기차배터리'],
            '207940.KS': ['삼성바이오로직스', 'Samsung Biologics', '바이오'],
            '005380.KS': ['현대차', 'Hyundai Motor', '자동차', '전기차'],
            '006400.KS': ['삼성SDI', 'Samsung SDI', '배터리', 'ESS']
        }

    def setup_reddit(self):
        """Reddit API 설정"""
        try:
            # Reddit 무료 API 사용 (read-only)
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID', 'temp_client_id'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET', 'temp_secret'),
                user_agent='StockNewsCollector/1.0',
                check_for_async=False
            )
        except Exception as e:
            logging.warning(f"Reddit API setup failed: {e}")
            self.reddit = None

    def get_newsapi_articles(self, query, language='en', page_size=20):
        """NewsAPI.org에서 뉴스 수집"""
        if not self.newsapi_key:
            return []

        try:
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'language': language,
                'sortBy': 'publishedAt',
                'pageSize': page_size,
                'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'apiKey': self.newsapi_key
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('articles', [])
            else:
                logging.error(f"NewsAPI error: {response.status_code}")
                return []

        except Exception as e:
            logging.error(f"Error fetching NewsAPI articles: {e}")
            return []

    def get_yahoo_finance_news(self, symbol):
        """Yahoo Finance에서 뉴스 스크래핑"""
        try:
            # 한국 주식은 심볼 변환
            if symbol.endswith('.KS') or symbol.endswith('.KQ'):
                search_symbol = symbol.replace('.KS', '.KS').replace('.KQ', '.KQ')
            else:
                search_symbol = symbol

            url = f"https://finance.yahoo.com/quote/{search_symbol}/news"

            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Yahoo Finance 뉴스 항목 찾기
            news_items = soup.find_all('div', {'class': re.compile(r'.*stream-item.*|.*news-item.*')})

            for item in news_items[:10]:  # 최대 10개
                try:
                    title_elem = item.find('h3') or item.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # 링크 찾기
                    link_elem = item.find('a', href=True)
                    link = ''
                    if link_elem:
                        link = link_elem['href']
                        if link.startswith('/'):
                            link = urljoin('https://finance.yahoo.com', link)

                    # 시간 정보
                    time_elem = item.find('div', {'class': re.compile(r'.*time.*|.*date.*')})
                    published_time = datetime.now().isoformat()

                    if time_elem:
                        time_text = time_elem.get_text(strip=True)
                        # 간단한 시간 파싱 (Yahoo의 상대시간)
                        if 'hour' in time_text or 'minute' in time_text:
                            published_time = (datetime.now() - timedelta(hours=1)).isoformat()

                    articles.append({
                        'title': title,
                        'description': title,  # Yahoo는 제목만 사용
                        'url': link,
                        'publishedAt': published_time,
                        'source': {'name': 'Yahoo Finance'},
                        'content': ''
                    })

                except Exception as e:
                    continue

            return articles

        except Exception as e:
            logging.error(f"Error scraping Yahoo Finance news for {symbol}: {e}")
            return []

    def get_korean_rss_news(self):
        """한국 RSS 뉴스 수집"""
        all_articles = []

        for source_name, rss_url in self.korean_rss_feeds.items():
            try:
                # RSS가 아닌 HTML 페이지인 경우 스크래핑
                if 'naver.com' in rss_url:
                    articles = self.scrape_naver_finance(rss_url)
                else:
                    feed = feedparser.parse(rss_url)
                    articles = []

                    for entry in feed.entries[:10]:  # 최대 10개
                        try:
                            published_time = datetime.now().isoformat()

                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published_time = datetime(*entry.published_parsed[:6]).isoformat()

                            articles.append({
                                'title': entry.get('title', ''),
                                'description': entry.get('summary', ''),
                                'url': entry.get('link', ''),
                                'publishedAt': published_time,
                                'source': {'name': source_name},
                                'content': entry.get('description', '')
                            })

                        except Exception as e:
                            continue

                all_articles.extend(articles)

            except Exception as e:
                logging.error(f"Error fetching RSS from {source_name}: {e}")
                continue

        return all_articles

    def scrape_naver_finance(self, url):
        """네이버 금융 뉴스 스크래핑"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # 네이버 금융 뉴스 항목 찾기
            news_items = soup.find_all('tr') + soup.find_all('dl', {'class': 'newsList'})

            for item in news_items[:10]:
                try:
                    # 제목 찾기
                    title_elem = item.find('a', {'class': re.compile(r'.*title.*|.*tit.*')})
                    if not title_elem:
                        title_elem = item.find('a')

                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')

                    if link and link.startswith('/'):
                        link = urljoin('https://finance.naver.com', link)

                    # 시간 정보
                    time_elem = item.find('span', {'class': re.compile(r'.*date.*|.*time.*')})
                    published_time = datetime.now().isoformat()

                    articles.append({
                        'title': title,
                        'description': title,
                        'url': link,
                        'publishedAt': published_time,
                        'source': {'name': 'Naver Finance'},
                        'content': ''
                    })

                except Exception as e:
                    continue

            return articles

        except Exception as e:
            logging.error(f"Error scraping Naver Finance: {e}")
            return []

    def get_reddit_posts(self, symbol, subreddit_list=['stocks', 'investing', 'SecurityAnalysis']):
        """Reddit에서 주식 관련 포스트 수집"""
        if not self.reddit:
            return []

        articles = []

        try:
            for subreddit_name in subreddit_list:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # 심볼 키워드로 검색
                    keywords = self.symbol_keywords.get(symbol, [symbol])

                    for keyword in keywords[:2]:  # 최대 2개 키워드
                        try:
                            for post in subreddit.search(keyword, time_filter='day', limit=5):
                                articles.append({
                                    'title': post.title,
                                    'description': post.selftext[:200] if post.selftext else post.title,
                                    'url': f"https://reddit.com{post.permalink}",
                                    'publishedAt': datetime.fromtimestamp(post.created_utc).isoformat(),
                                    'source': {'name': f'Reddit r/{subreddit_name}'},
                                    'content': post.selftext,
                                    'score': post.score,
                                    'num_comments': post.num_comments
                                })
                        except Exception as e:
                            continue

                except Exception as e:
                    logging.error(f"Error accessing subreddit {subreddit_name}: {e}")
                    continue

        except Exception as e:
            logging.error(f"Error fetching Reddit posts: {e}")

        return articles

class MCPNewsAnalyzer:
    """MCP news_analyzer 연동"""

    def __init__(self):
        self.mcp_path = Path('mcp/tools/news_analyzer/runner.py')

    def analyze_sentiment(self, title, content="", source=""):
        """MCP news_analyzer로 감성 분석"""
        try:
            # MCP가 없는 경우 더미 분석기 사용
            if not self.mcp_path.exists():
                return self.dummy_sentiment_analysis(title, content)

            # MCP 호출
            cmd = [
                'python', str(self.mcp_path),
                '--text', f"{title} {content}",
                '--source', source
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                try:
                    analysis = json.loads(result.stdout)
                    return {
                        'sentiment_score': analysis.get('sentiment_score', 0),
                        'sentiment_label': analysis.get('sentiment_label', 'neutral'),
                        'confidence': analysis.get('confidence', 0.5),
                        'keywords': analysis.get('keywords', [])
                    }
                except json.JSONDecodeError:
                    pass

            # 실패 시 더미 분석기 사용
            return self.dummy_sentiment_analysis(title, content)

        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            return self.dummy_sentiment_analysis(title, content)

    def dummy_sentiment_analysis(self, title, content=""):
        """더미 감성 분석기 (MCP 없을 때 사용)"""
        text = f"{title} {content}".lower()

        # 긍정 키워드
        positive_words = [
            'buy', 'bullish', 'growth', 'profit', 'gain', 'rise', 'increase',
            'strong', 'beat', 'exceed', 'outperform', 'positive', 'good',
            '상승', '호재', '급등', '성장', '수익', '긍정', '매수'
        ]

        # 부정 키워드
        negative_words = [
            'sell', 'bearish', 'loss', 'fall', 'decrease', 'decline', 'drop',
            'weak', 'miss', 'underperform', 'negative', 'bad', 'crash',
            '하락', '악재', '급락', '손실', '부정', '매도'
        ]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            sentiment_score = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
            sentiment_label = 'positive'
        elif negative_count > positive_count:
            sentiment_score = max(0.2, 0.5 - (negative_count - positive_count) * 0.1)
            sentiment_label = 'negative'
        else:
            sentiment_score = 0.5
            sentiment_label = 'neutral'

        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'confidence': 0.6,
            'keywords': []
        }

class NewsSentimentCollector:
    """뉴스 감성 수집기 메인 클래스"""

    def __init__(self):
        self.news_manager = NewsSourceManager()
        self.sentiment_analyzer = MCPNewsAnalyzer()

        self.setup_directories()
        self.setup_logging()
        self.setup_database()

        self.running = False

        # 수집 대상 심볼 (watchlist에서 로드)
        self.symbols = self.load_watchlist()

    def setup_directories(self):
        """필요한 디렉토리 생성"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.news_dir = Path(f'data/news/{today}')
        self.news_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """로깅 설정"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = f'logs/news_collector_{today}.log'

        Path('logs').mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def setup_database(self):
        """SQLite 데이터베이스 설정"""
        self.db_path = "news.db"
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE,
                symbol TEXT,
                title TEXT,
                description TEXT,
                url TEXT,
                source TEXT,
                published_at DATETIME,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                sentiment_score REAL,
                sentiment_label TEXT,
                confidence REAL,
                keywords TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS symbol_sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                date DATE,
                avg_sentiment REAL,
                article_count INTEGER,
                positive_count INTEGER,
                negative_count INTEGER,
                neutral_count INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def load_watchlist(self):
        """감시 종목 리스트 로드"""
        try:
            if Path('watchlist.txt').exists():
                with open('watchlist.txt', 'r') as f:
                    symbols = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                return symbols
            else:
                # 기본 심볼
                return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', '005930.KS', '000660.KS']

        except Exception as e:
            self.logger.error(f"Error loading watchlist: {e}")
            return ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

    def calculate_content_hash(self, article):
        """기사 내용 해시 계산 (중복 제거용)"""
        content = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_relevant_to_symbol(self, article, symbol):
        """기사가 특정 심볼과 관련있는지 확인"""
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()

        # 심볼 키워드 확인
        keywords = self.news_manager.symbol_keywords.get(symbol, [symbol.replace('.KS', '').replace('.KQ', '')])

        for keyword in keywords:
            if keyword.lower() in text:
                return True

        return False

    def collect_news_for_symbol(self, symbol):
        """특정 심볼의 뉴스 수집"""
        all_articles = []

        try:
            # 1. NewsAPI에서 수집
            if self.news_manager.newsapi_key:
                keywords = self.news_manager.symbol_keywords.get(symbol, [symbol])
                for keyword in keywords[:2]:  # 최대 2개 키워드
                    articles = self.news_manager.get_newsapi_articles(keyword)
                    all_articles.extend(articles)

            # 2. Yahoo Finance에서 수집
            yahoo_articles = self.news_manager.get_yahoo_finance_news(symbol)
            all_articles.extend(yahoo_articles)

            # 3. Reddit에서 수집
            reddit_articles = self.news_manager.get_reddit_posts(symbol)
            all_articles.extend(reddit_articles)

            # 4. 한국 주식인 경우 한국 뉴스도 수집
            if symbol.endswith('.KS') or symbol.endswith('.KQ'):
                korean_articles = self.news_manager.get_korean_rss_news()
                # 관련성 필터링
                relevant_articles = [
                    article for article in korean_articles
                    if self.is_relevant_to_symbol(article, symbol)
                ]
                all_articles.extend(relevant_articles)

            # 관련성 재확인 및 필터링
            relevant_articles = []
            for article in all_articles:
                if self.is_relevant_to_symbol(article, symbol):
                    relevant_articles.append(article)

            self.logger.info(f"Collected {len(relevant_articles)} relevant articles for {symbol}")
            return relevant_articles

        except Exception as e:
            self.logger.error(f"Error collecting news for {symbol}: {e}")
            return []

    def save_article_to_db(self, symbol, article, sentiment_data):
        """기사를 데이터베이스에 저장"""
        try:
            conn = sqlite3.connect(self.db_path)

            article_hash = self.calculate_content_hash(article)

            # 중복 확인
            cursor = conn.execute('SELECT id FROM news_articles WHERE hash = ?', (article_hash,))
            if cursor.fetchone():
                conn.close()
                return False  # 이미 존재

            # 기사 저장
            conn.execute('''
                INSERT INTO news_articles
                (hash, symbol, title, description, url, source, published_at,
                 sentiment_score, sentiment_label, confidence, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_hash,
                symbol,
                article.get('title', ''),
                article.get('description', ''),
                article.get('url', ''),
                article.get('source', {}).get('name', ''),
                article.get('publishedAt', datetime.now().isoformat()),
                sentiment_data['sentiment_score'],
                sentiment_data['sentiment_label'],
                sentiment_data['confidence'],
                json.dumps(sentiment_data['keywords'])
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving article to DB: {e}")
            return False

    def save_article_to_json(self, symbol, articles_with_sentiment):
        """기사를 JSON 파일로 저장"""
        try:
            safe_symbol = symbol.replace('.', '_')
            json_file = self.news_dir / f'{safe_symbol}_news.json'

            # 기존 데이터 로드
            existing_data = []
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = []

            # 새 데이터 추가
            existing_data.extend(articles_with_sentiment)

            # 중복 제거 (해시 기준)
            seen_hashes = set()
            unique_data = []

            for article in existing_data:
                article_hash = self.calculate_content_hash(article)
                if article_hash not in seen_hashes:
                    seen_hashes.add(article_hash)
                    unique_data.append(article)

            # 최근 100개만 유지
            unique_data = unique_data[-100:]

            # 파일 저장
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving articles to JSON: {e}")

    def update_symbol_sentiment_summary(self, symbol):
        """심볼별 감성 요약 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            today = datetime.now().date()

            # 오늘의 기사들에 대한 감성 통계
            cursor = conn.execute('''
                SELECT
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as total_count,
                    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM news_articles
                WHERE symbol = ? AND DATE(published_at) = ?
            ''', (symbol, today))

            result = cursor.fetchone()

            if result and result[1] > 0:  # 기사가 있는 경우
                avg_sentiment, total_count, positive_count, negative_count, neutral_count = result

                # 기존 레코드 삭제 후 새로 삽입
                conn.execute('DELETE FROM symbol_sentiment WHERE symbol = ? AND date = ?', (symbol, today))

                conn.execute('''
                    INSERT INTO symbol_sentiment
                    (symbol, date, avg_sentiment, article_count, positive_count, negative_count, neutral_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, today, avg_sentiment, total_count, positive_count, negative_count, neutral_count))

                conn.commit()

            conn.close()

        except Exception as e:
            self.logger.error(f"Error updating sentiment summary for {symbol}: {e}")

    def get_symbol_sentiment_score(self, symbol):
        """심볼의 뉴스 감성 점수 조회 (0-100)"""
        try:
            conn = sqlite3.connect(self.db_path)
            today = datetime.now().date()

            cursor = conn.execute('''
                SELECT avg_sentiment, article_count, positive_count, negative_count
                FROM symbol_sentiment
                WHERE symbol = ? AND date = ?
            ''', (symbol, today))

            result = cursor.fetchone()
            conn.close()

            if result:
                avg_sentiment, article_count, positive_count, negative_count = result

                # 감성 점수를 0-100 스케일로 변환
                # 0.5 (중립) = 50점, 1.0 (매우 긍정) = 100점, 0.0 (매우 부정) = 0점
                base_score = avg_sentiment * 100

                # 기사 수에 따른 신뢰도 조정
                confidence_multiplier = min(1.0, article_count / 10)  # 10개 이상이면 100% 신뢰

                # 긍정/부정 비율 고려
                if article_count > 0:
                    sentiment_ratio = (positive_count - negative_count) / article_count
                    ratio_bonus = sentiment_ratio * 10  # 최대 ±10점

                    final_score = base_score + ratio_bonus
                    final_score = max(0, min(100, final_score))
                    final_score *= confidence_multiplier

                    return {
                        'score': final_score,
                        'article_count': article_count,
                        'avg_sentiment': avg_sentiment,
                        'confidence': confidence_multiplier
                    }

            return {'score': 50, 'article_count': 0, 'avg_sentiment': 0.5, 'confidence': 0}

        except Exception as e:
            self.logger.error(f"Error getting sentiment score for {symbol}: {e}")
            return {'score': 50, 'article_count': 0, 'avg_sentiment': 0.5, 'confidence': 0}

    def clean_old_news(self):
        """24시간 이상 된 뉴스 정리"""
        try:
            conn = sqlite3.connect(self.db_path)

            # 24시간 이상 된 기사 삭제
            cutoff_time = datetime.now() - timedelta(hours=24)

            cursor = conn.execute('DELETE FROM news_articles WHERE published_at < ?', (cutoff_time.isoformat(),))
            deleted_count = cursor.rowcount

            # 오래된 감성 요약 삭제 (7일 이상)
            cutoff_date = (datetime.now() - timedelta(days=7)).date()
            conn.execute('DELETE FROM symbol_sentiment WHERE date < ?', (cutoff_date,))

            conn.commit()
            conn.close()

            if deleted_count > 0:
                self.logger.info(f"Cleaned {deleted_count} old news articles")

        except Exception as e:
            self.logger.error(f"Error cleaning old news: {e}")

    def run_collection_cycle(self):
        """뉴스 수집 사이클 실행"""
        try:
            self.logger.info("Starting news collection cycle...")

            for symbol in self.symbols:
                try:
                    self.logger.info(f"Collecting news for {symbol}...")

                    # 뉴스 수집
                    articles = self.collect_news_for_symbol(symbol)

                    if not articles:
                        continue

                    # 감성 분석 및 저장
                    articles_with_sentiment = []
                    new_articles_count = 0

                    for article in articles:
                        try:
                            # 감성 분석
                            sentiment_data = self.sentiment_analyzer.analyze_sentiment(
                                article.get('title', ''),
                                article.get('description', ''),
                                article.get('source', {}).get('name', '')
                            )

                            # 기사에 감성 데이터 추가
                            article_with_sentiment = article.copy()
                            article_with_sentiment.update(sentiment_data)
                            articles_with_sentiment.append(article_with_sentiment)

                            # 데이터베이스 저장
                            if self.save_article_to_db(symbol, article, sentiment_data):
                                new_articles_count += 1

                            # API 제한 방지
                            time.sleep(0.1)

                        except Exception as e:
                            self.logger.error(f"Error processing article: {e}")
                            continue

                    # JSON 파일 저장
                    if articles_with_sentiment:
                        self.save_article_to_json(symbol, articles_with_sentiment)

                    # 감성 요약 업데이트
                    self.update_symbol_sentiment_summary(symbol)

                    self.logger.info(f"Processed {len(articles)} articles for {symbol}, {new_articles_count} new")

                except Exception as e:
                    self.logger.error(f"Error collecting news for {symbol}: {e}")
                    continue

            # 오래된 뉴스 정리
            self.clean_old_news()

            self.logger.info("News collection cycle completed")

        except Exception as e:
            self.logger.error(f"Error in news collection cycle: {e}")

    def display_sentiment_summary(self):
        """감성 요약 출력"""
        try:
            print("\n" + "=" * 60)
            print("📰 뉴스 감성 분석 현황")
            print("=" * 60)

            for symbol in self.symbols:
                sentiment_data = self.get_symbol_sentiment_score(symbol)

                score = sentiment_data['score']
                article_count = sentiment_data['article_count']

                if article_count > 0:
                    if score >= 70:
                        trend = "🟢 긍정적"
                    elif score <= 30:
                        trend = "🔴 부정적"
                    else:
                        trend = "🟡 중립적"

                    print(f"{symbol}: {score:.1f}점 {trend} ({article_count}개 기사)")
                else:
                    print(f"{symbol}: 뉴스 없음")

            print("=" * 60)

        except Exception as e:
            self.logger.error(f"Error displaying sentiment summary: {e}")

    def start_collection(self, interval_minutes=5):
        """뉴스 수집 시작"""
        self.running = True

        self.logger.info("🚀 Starting news sentiment collector...")
        self.logger.info(f"📊 Monitoring {len(self.symbols)} symbols")
        self.logger.info(f"⏰ Collection interval: {interval_minutes} minutes")

        try:
            while self.running:
                start_time = time.time()

                # 수집 사이클 실행
                self.run_collection_cycle()

                # 감성 요약 출력
                self.display_sentiment_summary()

                # 인터벌 유지
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_minutes * 60 - elapsed)

                if sleep_time > 0:
                    self.logger.info(f"Sleeping for {sleep_time/60:.1f} minutes...")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.logger.info("Collection stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error in collection loop: {e}")
        finally:
            self.running = False

    def stop_collection(self):
        """뉴스 수집 중지"""
        self.running = False
        self.logger.info("Stopping news collection...")

def main():
    """메인 실행 함수"""
    print("📰 뉴스 감성 수집기")
    print("=" * 50)
    print("지원 소스:")
    print("- NewsAPI.org (API 키 필요)")
    print("- Yahoo Finance")
    print("- Reddit")
    print("- 한국 뉴스 RSS")
    print("=" * 50)

    # API 키 확인
    newsapi_key = os.getenv('NEWSAPI_KEY')
    if newsapi_key:
        print(f"✅ NewsAPI 키 설정됨")
    else:
        print("⚠️ NewsAPI 키 없음 (NEWSAPI_KEY 환경변수 설정)")

    try:
        collector = NewsSentimentCollector()
        collector.start_collection(interval_minutes=5)

    except Exception as e:
        print(f"❌ Error starting collector: {e}")

if __name__ == "__main__":
    main()