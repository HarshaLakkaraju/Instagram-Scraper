# Instagram Scraper with Modal Navigation

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.15%2B-orange)](https://selenium.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A production-grade Instagram content scraper that uses modal navigation for sequential post scraping, featuring session persistence, multi-profile support, and robust error handling.

## ✨ Features

### 🎯 Core Capabilities
- **Modal Navigation**: Scrape posts sequentially using Instagram's built-in modal viewer
- **Session Persistence**: Save and reload authentication sessions (no daily logins required)
- **Multi-Profile Support**: Scrape multiple usernames in a single run
- **Content Type Selection**: Choose between posts, reels, or both
- **Chronological Order**: Posts are collected in correct chronological sequence
- **Production Ready**: Comprehensive logging, error recovery, and graceful degradation

### 🔧 Technical Features
- **Headless Mode**: Run without GUI for server deployments
- **Stealth Mode**: Anti-detection measures with realistic user agents
- **Rate Limiting**: Intelligent delays between profile requests
- **JSON Output**: Structured, machine-readable results
- **Logging**: Detailed execution logs with timestamps
- **Graceful Error Handling**: Continue scraping even if individual profiles fail

## 📋 Prerequisites

- Python 3.8 or higher
- Google Chrome browser installed
- ChromeDriver (automatically managed by Selenium Manager)
- Instagram account credentials

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/instascraper.git
   cd instascraper
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install selenium python-dotenv
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   ```env
   IG_USERNAME=your_instagram_username
   IG_PASSWORD=your_instagram_password
   HEADLESS=false  # Set to true for server use
   ```

## ⚙️ Configuration

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IG_USERNAME` | Yes | - | Your Instagram username |
| `IG_PASSWORD` | Yes | - | Your Instagram password |
| `HEADLESS` | No | `false` | Run browser in background |
| `CONTENT_TYPE` | No | `both` | `posts`, `reels`, or `both` |
| `POSTS_PER_PROFILE` | No | `4` | Number of posts to scrape |
| `REELS_PER_PROFILE` | No | `2` | Number of reels to scrape |

## 📖 Usage

### Basic Command
```bash
python final_instascraper_inputjson.py -u username1 username2 username3
```

### Complete Example
```bash
python final_instascraper_inputjson.py \
  -u selenagomez natgeo instagram \
  -p 10 \
  -r 5 \
  -t both \
  --no-session \
  --quiet
```

### Command Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--users` | `-u` | Space-separated usernames to scrape | **Required** |
| `--posts` | `-p` | Number of posts per profile | `4` |
| `--reels` | `-r` | Number of reels per profile | `2` |
| `--type` | `-t` | Content type: `posts`, `reels`, or `both` | `both` |
| `--no-session` | - | Disable session persistence | `false` |
| `--quiet` | - | Suppress logging output | `false` |

## 📊 Output Format

The script outputs JSON to stdout with the following structure:

```json
{
  "profiles": [
    {
      "profile": {
        "username": "instagram",
        "profile_url": "https://www.instagram.com/instagram/",
        "scraped_at": "2024-01-15T10:30:00.000000",
        "posts": [
          {
            "content_url": "https://www.instagram.com/p/C1234567890/",
            "content_id": "C1234567890",
            "scraped_at": "2024-01-15T10:30:01.000000",
            "content_type": "post",
            "order": 1
          }
        ],
        "reels": [
          {
            "content_url": "https://www.instagram.com/reel/C0987654321/",
            "content_id": "C0987654321",
            "scraped_at": "2024-01-15T10:30:02.000000",
            "content_type": "reel",
            "order": 1
          }
        ]
      },
      "summary": {
        "username": "instagram",
        "posts_count": 4,
        "reels_count": 2,
        "scraping_time_seconds": 12.34,
        "success": true
      }
    }
  ],
  "summary": {
    "total_profiles": 3,
    "successful_profiles": 3,
    "total_posts": 12,
    "total_reels": 6,
    "scraped_at": "2024-01-15T10:45:00.000000",
    "success_rate": 100.0
  }
}
```

## 🔄 Session Management

The scraper implements intelligent session handling:

1. **First Run**: Creates `instagram_session.pkl` with authentication cookies
2. **Subsequent Runs**: Automatically loads saved session
3. **Session Validation**: Checks if session is still valid before using
4. **Automatic Refresh**: Falls back to fresh login if session expires

To force a fresh login:
```bash
python final_instascraper_inputjson.py -u username --no-session
```

## 🏗️ Architecture

### Key Components
- **`InstagramScraperWithLogin`**: Main scraper class with all functionality
- **Modal Navigation System**: Uses Instagram's post viewer for sequential access
- **Session Manager**: Handles cookie persistence and validation
- **Content Discovery**: Dual strategy for posts (modal) and reels (traditional)

### Scraping Methods
1. **Posts**: Opens first post, navigates sequentially using right arrow
2. **Reels**: Traditional link discovery from profile page
3. **Hybrid**: Can collect both content types in single run

## 🛡️ Anti-Detection Measures

- **User Agent Rotation**: Realistic browser fingerprints
- **CDP Stealth**: Navigator.webdriver property masking
- **Realistic Delays**: Random intervals between actions
- **Headless Optimization**: Modern Chrome headless mode
- **Cookie Management**: Proper session handling

## 📈 Performance Tips

1. **Batch Processing**: Process multiple usernames in single session
2. **Headless Mode**: Use `HEADLESS=true` for server deployments
3. **Content Selection**: Use `-t posts` or `-t reels` for faster scraping
4. **Rate Limiting**: Default delays prevent rate limiting
5. **Session Reuse**: Reuse saved sessions across runs

## ⚠️ Limitations & Considerations

### Technical Limitations
- Requires active Instagram account
- Subject to Instagram's rate limits
- May require CAPTCHA solving for new sessions
- Instagram UI changes may break selectors

### Best Practices
1. **Respect Rate Limits**: Don't scrape more than 10-15 profiles/hour
2. **Use Responsibly**: Comply with Instagram's Terms of Service
3. **Monitor Logs**: Check logs for authentication issues
4. **Regular Updates**: Update selectors if Instagram changes UI

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Login failed" | Check credentials in `.env`, disable 2FA temporarily |
| "No posts found" | Profile may be private or have no content |
| "Session expired" | Run with `--no-session` to refresh |
| "Element not found" | Instagram UI may have changed - update selectors |
| "ChromeDriver error" | Ensure Chrome is updated to latest version |

### Debug Mode
Remove `--quiet` flag and check logs:
```bash
python final_instascraper_inputjson.py -u testuser 2>&1 | tee debug.log
```

## 📝 Logging

Logs are saved to `instagram_scraper_YYYYMMDD_HHMMSS.log` with:
- Timestamps for all operations
- Success/failure status for each profile
- Error details and stack traces
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Development Setup
```bash
git clone https://github.com/yourusername/instascraper.git
cd instascraper
pip install -e ".[dev]"
pytest tests/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

This tool is for educational and research purposes only. Users are responsible for:
- Complying with Instagram's Terms of Service
- Respecting copyright and privacy laws
- Not overloading Instagram's servers
- Obtaining necessary permissions for data collection

The authors are not responsible for any misuse or damages caused by this software.

## 📚 Documentation

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Instagram API Terms](https://developers.facebook.com/docs/instagram)
- [Python dotenv](https://github.com/theskumar/python-dotenv)

---

**Note**: This tool interacts with Instagram's web interface. Usage may be subject to Instagram's rate limits and Terms of Service. Use responsibly and consider implementing appropriate delays between requests.
