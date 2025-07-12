import Parser from "rss-parser";
import axios from "axios";

const parser = new Parser();

export async function fetchRSS(feedUrl) {
  const { data } = await axios.get(feedUrl);
  const feed = await parser.parseString(data);

  const now = new Date();
  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

  return feed.items.filter((item) => {
    const pubDate = new Date(item.pubDate || item.isoDate || 0);
    return pubDate > oneDayAgo;
  });
}
