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

      // Thêm source vào mỗi article
      const articlesWithSource = articles.map((article) => ({
        ...article,
        source: feed.source || extractSourceFromArticle(article) || "Unknown",
      }));

      await saveToCollection(feed.collection, articlesWithSource);
      console.log(
        `✅ Updated ${feed.collection}: ${articlesWithSource.length} articles`
      );
    } catch (err) {
      console.error(`❌ Failed ${feed.collection}:`, err.message);
    }
  }

  console.log(`[${getVietnamTime()}] Finished fetching RSS.`);
}

// Helper function để extract source từ article nếu có
function extractSourceFromArticle(article) {
  // Nếu article có source field trực tiếp
  if (article.source) {
    return typeof article.source === "string"
      ? article.source
      : article.source._;
  }

  // Nếu có trong description, parse từ HTML
  if (article.description) {
    const sourceMatch = article.description.match(
      /<font color="#6f6f6f">(.*?)<\/font>/
    );
    if (sourceMatch) {
      return sourceMatch[1];
    }
  }

  // Extract từ title nếu có pattern " - Báo ABC"
  if (article.title) {
    const titleMatch = article.title.match(/ - (.+)$/);
    if (titleMatch) {
      return titleMatch[1];
    }
  }

  return null;
}

// import { fetchRSS } from "../services/rssFetcher.js";
// import {
//   clearCollection,
//   saveToCollection,
// } from "../services/firestoreService.js";
// import { FEED_CONFIGS } from "../data/feedList.js";

// function getVietnamTime() {
//   return new Date().toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
// }

// export async function runRssJob() {
//   console.log(`[${getVietnamTime()}] Start fetching RSS...`);

//   for (const feed of FEED_CONFIGS) {
//     console.log(`Fetching ${feed.url} -> ${feed.collection}`);
//     try {
//       const articles = await fetchRSS(feed.url);
//       await clearCollection(feed.collection);
//       await saveToCollection(feed.collection, articles);
//       console.log(`✅ Updated ${feed.collection}: ${articles.length} articles`);
//     } catch (err) {
//       console.error(`❌ Failed ${feed.collection}:`, err.message);
//     }
//   }

//   console.log(`[${getVietnamTime()}] Finished fetching RSS.`);
// }
