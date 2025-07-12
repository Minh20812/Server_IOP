// src/jobs/rssJob.js
import { fetchRSS } from "../services/rssFetcher.js";
import {
  clearCollection,
  saveToCollection,
} from "../services/firestoreService.js";
import { FEED_CONFIGS } from "../data/feedList.js";

function getVietnamTime() {
  return new Date().toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}

export async function runRssJob() {
  console.log(`[${getVietnamTime()}] Start fetching RSS...`);

  for (const feed of FEED_CONFIGS) {
    console.log(`Fetching ${feed.url} -> ${feed.collection}`);
    try {
      const articles = await fetchRSS(feed.url);
      await clearCollection(feed.collection);
      await saveToCollection(feed.collection, articles);
      console.log(`✅ Updated ${feed.collection}: ${articles.length} articles`);
    } catch (err) {
      console.error(`❌ Failed ${feed.collection}:`, err.message);
    }
  }

  console.log(`[${getVietnamTime()}] Finished fetching RSS.`);
}
