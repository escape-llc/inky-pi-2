import feedparser
import re

COMICS = {
	"XKCD": {
		"feed": "https://xkcd.com/atom.xml",
		"element": lambda feed,ix: feed.entries[ix].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: feed.entries[ix].title,
		"caption": lambda element: re.search(r'<img[^>]+alt=["\"]([^"\"]+)["\"]', element).group(1),
	},
	"Cyanide & Happiness": {
		"feed": "https://explosm-1311.appspot.com/",
		"element": lambda feed,ix: feed.entries[ix].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: feed.entries[ix].title.split(" - ")[1].strip(),
		"caption": lambda element: "",
	},
	"Saturday Morning Breakfast Cereal": {
		"feed": "http://www.smbc-comics.com/comic/rss",
		"element": lambda feed,ix: feed.entries[ix].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: feed.entries[ix].title.split("-")[1].strip(),
		"caption": lambda element: re.search(r'Hovertext:<br />(.*?)</p>', element).group(1),
	},
	"The Perry Bible Fellowship": {
		"feed": "https://pbfcomics.com/feed/",
		"element": lambda feed: feed.entries[0].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed: feed.entries[0].title,
		"caption": lambda element: re.search(r'<img[^>]+alt=["\"]([^"\"]+)["\"]', element).group(1),
	},
	"Questionable Content": {
		"feed": "http://www.questionablecontent.net/QCRSS.xml",
		"element": lambda feed,ix: feed.entries[ix].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: feed.entries[ix].title,
		"caption": lambda element: "",
	},
	"Poorly Drawn Lines": {
		"feed": "https://poorlydrawnlines.com/feed/",
		"element": lambda feed,ix: feed.entries[ix].get('content', [{}])[0].get('value', ''),
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: feed.entries[ix].title,
		"caption": lambda element: "",
	},
	"Dinosaur Comics": {
		"feed": "https://www.qwantz.com/rssfeed.php",
		"element": lambda feed,ix: feed.entries[ix].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: feed.entries[ix].title,
		"caption": lambda element: re.search(r'title="(.*?)" />', element.replace('\n', '')).group(1),
	},
	"webcomic name": {
		"feed": "https://webcomicname.com/rss",
		"element": lambda feed,ix: feed.entries[ix].description,
		"url": lambda element: re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', element).group(1),
		"title": lambda feed,ix: "",
		"caption": lambda element: "",
	},
}

def get_panel(comic_name, index = None):
	feed = feedparser.parse(COMICS[comic_name]["feed"])
	actual = index
	if actual is None:
		actual = 0
	elif actual >= len(feed.entries):
		actual = 0
	try:
		element = COMICS[comic_name]["element"](feed, actual)
	except IndexError:
		raise RuntimeError("Failed to retrieve latest comic.")

	return {
		"name": comic_name,
		"index": index,
		"actual": actual,
		"count": len(feed.entries),
		"image_url": COMICS[comic_name]["url"](element),
		"title": COMICS[comic_name]["title"](feed, actual),
		"caption": COMICS[comic_name]["caption"](element),
	}