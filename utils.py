import asyncio
from datetime import datetime
from ddgs import DDGS

async def search_disaster_alerts(location: str) -> str:
    """Search for emergency/disaster news from last 3 days only"""
    print(f"🔍 Searching emergency/disaster alerts for: {location} (Last 3 days)")
    
    # Emergency keywords with stricter severity weights
    emergency_keywords = {
        # Critical disasters (severity 9-10)
        'earthquake': 10, 'tsunami': 10, 'hurricane': 9, 'tornado': 9, 'cyclone': 9,
        'wildfire': 9, 'major fire': 9, 'flood': 8, 'flash flood': 10, 'landslide': 9,
        'volcano': 10, 'eruption': 10, 'explosion': 9, 'bombing': 10, 'terrorist': 10,
        'shooting': 9, 'attack': 8, 'evacuation': 9, 'emergency': 7,
        
        # Severe weather/alerts (severity 7-8)
        'severe storm': 8, 'blizzard': 8, 'severe weather': 7, 'emergency warning': 8,
        'critical alert': 9, 'urgent alert': 8, 'immediate danger': 9, 'threat': 7,
        
        # Infrastructure/safety (severity 6-8)
        'major accident': 7, 'train crash': 8, 'plane crash': 9, 'building collapse': 10,
        'bridge collapse': 10, 'gas leak': 8, 'chemical spill': 9, 'toxic': 8,
        'radiation': 10, 'nuclear': 10, 'contamination': 8,
        
        # Breaking emergency indicators
        'breaking emergency': 9, 'urgent breaking': 8, 'emergency alert': 8,
        'disaster alert': 8, 'crisis': 7, 'catastrophe': 9
    }
    
    # Legitimate news sources (focus on major outlets)
    trusted_news_sources = [
        'cnn.com', 'bbc.com', 'reuters.com', 'ap.org', 'apnews.com', 'npr.org',
        'abc.com', 'cbsnews.com', 'nbcnews.com', 'weather.com', 'usatoday.com',
        'washingtonpost.com', 'bloomberg.com', 'theguardian.com', 'skynews.com'
    ]
    
    # Create focused search queries for EMERGENCY NEWS ONLY
    search_queries = [
        f"{location} breaking emergency disaster today news",
        f"{location} urgent alert weather warning earthquake fire flood",
        f"{location} emergency services news disaster alert",
        f"\"breaking news\" {location} emergency disaster alert",
        f"{location} \"emergency alert\" OR \"disaster alert\" OR \"urgent warning\"",
        f"site:cnn.com OR site:bbc.com OR site:reuters.com {location} emergency disaster"
    ]
    
    # Function to check if content is within last 3 days
    def is_within_3_days(title: str, snippet: str) -> bool:
        content = (title + " " + snippet).lower()
        
        # Strong indicators of very recent content (last 3 days)
        very_recent_indicators = [
            'today', 'now', 'live', 'breaking', 'just in', 'current',
            'minutes ago', 'hour ago', 'hours ago', 'this morning', 
            'this afternoon', 'this evening', 'tonight', 'latest',
            'developing', 'ongoing', 'right now', 'currently happening'
        ]
        
        # Recent indicators (within 3 days)
        recent_indicators = [
            'yesterday', 'last night', 'early today', 'late yesterday',
            'two days ago', 'three days ago', '48 hours', '72 hours'
        ]
        
        # Strong exclusion indicators (clearly old content)
        old_indicators = [
            'last week', 'last month', 'days ago', 'weeks ago', 'months ago',
            'last year', 'years ago', 'archive', 'historical', 'past',
            'former', 'previous', 'earlier this week', 'earlier this month',
            'four days ago', 'five days ago', 'week ago', 'annual', 'anniversary'
        ]
        
        # Immediate exclusion for old content
        if any(indicator in content for indicator in old_indicators):
            return False
        
        # Check for recent indicators
        has_very_recent = any(indicator in content for indicator in very_recent_indicators)
        has_recent = any(indicator in content for indicator in recent_indicators)
        
        # Must have recent indicators for 3-day filter
        return has_very_recent or has_recent
    
    # Function to calculate severity score with stricter criteria
    def calculate_severity_score(title: str, snippet: str) -> tuple[int, str]:
        content = (title + " " + snippet).lower()
        max_severity = 0
        matched_keywords = []
        
        for keyword, severity in emergency_keywords.items():
            if keyword in content:
                max_severity = max(max_severity, severity)
                matched_keywords.append(keyword)
        
        # Boost score for multiple emergency keywords
        if len(matched_keywords) > 1:
            max_severity = min(10, max_severity + 1)
        
        # Boost for strong breaking news indicators
        breaking_indicators = ['breaking', 'urgent', 'emergency alert', 'disaster alert']
        if any(indicator in content for indicator in breaking_indicators):
            max_severity = min(10, max_severity + 1)
        
        # Determine emoji based on severity
        if max_severity >= 9:
            emoji = "🚨"  # Critical emergency
        elif max_severity >= 8:
            emoji = "🔴"  # High severity
        elif max_severity >= 7:
            emoji = "🟠"  # Significant
        elif max_severity >= 6:
            emoji = "🟡"  # Moderate
        else:
            emoji = "🟢"  # Advisory
        
        return max_severity, emoji
    
    # Function to check if source is legitimate news
    def is_legitimate_news_source(url: str, title: str) -> bool:
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Prioritize trusted news sources
        for trusted in trusted_news_sources:
            if trusted in url_lower:
                return True
        
        # Check for news indicators
        news_indicators = ['news', 'breaking', 'report', 'alert', 'press']
        return any(indicator in url_lower or indicator in title_lower for indicator in news_indicators)
    
    # Function to check location relevance
    def is_location_relevant(title: str, snippet: str, target_location: str) -> bool:
        content = (title + " " + snippet).lower()
        target_lower = target_location.lower()
        
        # Check for exact location match
        if target_lower in content:
            return True
        
        # Check for location variations
        if ',' in target_location:
            parts = [part.strip() for part in target_location.split(',')]
            for part in parts:
                if part.lower() in content:
                    return True
        
        return False
    
    # Perform searches in parallel
    print(f"Starting {len(search_queries)} focused emergency searches...")
    search_tasks = [
        asyncio.get_event_loop().run_in_executor(
            None, 
            lambda q=query: list(DDGS().text(q, max_results=8))
        ) for query in search_queries
    ]
    all_search_results = await asyncio.gather(*search_tasks)
    
    # Process and filter results
    qualified_news = []
    seen_urls = set()
    
    for results in all_search_results:
        for result in results:
            title = result.get("title", "")
            url = result.get("href", "")
            snippet = result.get("body", "")
            
            # Skip duplicates
            if url in seen_urls or not url:
                continue
            seen_urls.add(url)
            
            # Only include legitimate news sources
            if not is_legitimate_news_source(url, title):
                continue
            
            # Only include content from last 3 days
            if not is_within_3_days(title, snippet):
                continue
            
            # Check location relevance
            if not is_location_relevant(title, snippet, location):
                continue
            
            # Calculate severity score
            severity, emoji = calculate_severity_score(title, snippet)
            
            # Only include emergency-level news (severity >= 7)
            if severity < 7:
                continue
            
            qualified_news.append({
                'title': title,
                'snippet': snippet,
                'url': url,
                'severity': severity,
                'emoji': emoji
            })
    
    # Sort by severity (highest first)
    qualified_news.sort(key=lambda x: x['severity'], reverse=True)
    
    # Limit to top 5 most severe results
    qualified_news = qualified_news[:5]
    
    # Format results
    if qualified_news:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        max_severity = max(item['severity'] for item in qualified_news)
        header_emoji = "🚨" if max_severity >= 9 else "🔴" if max_severity >= 8 else "🟠"
        
        response_parts = [
            f"**{header_emoji} EMERGENCY ALERTS for {location}**",
            f"**Search Time:** {current_time}",
            f"**Time Frame:** Last 3 days only",
            f"**Found {len(qualified_news)} critical emergency alerts (severity ≥7/10)**\n"
        ]
        
        # Group by severity
        critical = [item for item in qualified_news if item['severity'] >= 9]
        high = [item for item in qualified_news if 8 <= item['severity'] < 9]
        significant = [item for item in qualified_news if 7 <= item['severity'] < 8]
        
        if critical:
            response_parts.append("**🚨 CRITICAL EMERGENCIES (Severity 9-10):**")
            for i, item in enumerate(critical, 1):
                response_parts.extend([
                    f"**{i}. {item['emoji']} [{item['severity']}/10] {item['title']}**",
                    f"📰 {item['snippet']}" if item['snippet'] else "📝 No preview available",
                    f"🔗 {item['url']}\n"
                ])
        
        if high:
            response_parts.append("**🔴 HIGH SEVERITY (Severity 8):**")
            for i, item in enumerate(high, 1):
                response_parts.extend([
                    f"**{i}. {item['emoji']} [{item['severity']}/10] {item['title']}**",
                    f"📰 {item['snippet']}" if item['snippet'] else "📝 No preview available",
                    f"🔗 {item['url']}\n"
                ])
        
        if significant:
            response_parts.append("**🟠 SIGNIFICANT ALERTS (Severity 7):**")
            for i, item in enumerate(significant, 1):
                response_parts.extend([
                    f"**{i}. {item['emoji']} [{item['severity']}/10] {item['title']}**",
                    f"📰 {item['snippet']}" if item['snippet'] else "📝 No preview available",
                    f"🔗 {item['url']}\n"
                ])
        
        response_parts.extend([
            "**Sources:** Major news outlets and verified channels",
            "**Note:** Only emergency-level incidents from last 3 days. Verify with official sources."
        ])
        
        response_text = "\n".join(response_parts)
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        response_text = (
            f"**NO CRITICAL EMERGENCY ALERTS for {location}**\n\n"
            f"**Search Time:** {current_time}\n"
            f"**Time Frame:** Last 3 days\n"
            f"**Location:** {location}\n\n"
            f"**Searched:** Major news outlets for emergency-level incidents\n"
            f"**Emergency Threshold:** Severity ≥7/10\n"
            f"**Status:** No critical emergency or disaster alerts detected\n\n"
            f"**🎉 Good News!** No critical emergency alerts found from verified news sources for your location in the last 3 days."
        )
    
    return response_text
