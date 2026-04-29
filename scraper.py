import re
from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup
import json

def scraper(url, resp):
    report_stats(url, resp)
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    if resp is None or resp.status != 200 or resp.raw_response is None:
        return []
    
    contents = resp.raw_response.content

    suspicious_stew = BeautifulSoup(contents, "lxml")

    links = []

    for a in suspicious_stew.find_all('a'):
        href = a.get("href")

        if not href:
            continue
        
        absolute_url = urljoin(url, href)
        defragged, _ = urldefrag(absolute_url)
        links.append(defragged)

    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        netloc = parsed.netloc.lower()
        path = parsed.path.lower()
        low_url = url.lower()

        allowed_domains = ('ics.uci.edu', 'cs.uci.edu', 'informatics.uci.edu', 'stat.uci.edu')
        if not any(netloc == domain or netloc.endswith("." + domain) for domain in allowed_domains):
            return False
        
        if "calendar" in low_url or "ical" in low_url or "tribe" in low_url:
            return False

        if "/events/" in path:
            return False

        if "doku.php" in low_url:
            return False

        if netloc == "gitlab.ics.uci.edu":
            return False

        if netloc == "grape.ics.uci.edu":
            return False

        if netloc == "fano.ics.uci.edu" and path.startswith("/ca/rules/"):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|pps|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def report_stats(url, resp):
    if resp is None or resp.status != 200 or resp.raw_response is None:
        return

    clean_url, _ = urldefrag(url)

    if not is_valid(clean_url):
        return

    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(" ")
    words = re.findall(r"[a-zA-Z0-9]{3,}", text.lower())

    parsed = urlparse(clean_url)

    data = {
        "url": clean_url,
        "subdomain": parsed.netloc.lower(),
        "word_count": len(words),
        "words": words
    }

    with open("report_stats.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")