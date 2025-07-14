import db from "../config/firebase.js";
import { Timestamp } from "firebase-admin/firestore"; // nếu dùng firebase-admin SDK

export async function clearCollection(collectionName) {
  const snapshot = await db.collection(collectionName).get();
  const batch = db.batch();
  snapshot.forEach((doc) => batch.delete(doc.ref));
  await batch.commit();
}

export async function saveToCollection(collectionName, articles) {
  const batch = db.batch();
  articles.forEach((article) => {
    const docRef = db.collection(collectionName).doc();

    const pubDateString = article.pubDate || article.isoDate;
    const pubDate = pubDateString ? new Date(pubDateString) : new Date();

    batch.set(docRef, {
      title: article.title,
      link: article.link,
      source: article.source || "Unknown",
      pubDate: Timestamp.fromDate(pubDate), // chuẩn hóa timestamp cho sort
      pubDateRaw: pubDateString, // lưu chuỗi gốc để hiển thị (nếu cần)
      createdAt: Timestamp.now(), // dùng timestamp luôn
    });
  });
  await batch.commit();
}

// import db from "../config/firebase.js";

// export async function clearCollection(collectionName) {
//   const snapshot = await db.collection(collectionName).get();
//   const batch = db.batch();
//   snapshot.forEach((doc) => batch.delete(doc.ref));
//   await batch.commit();
// }

// export async function saveToCollection(collectionName, articles) {
//   const batch = db.batch();
//   articles.forEach((article) => {
//     const docRef = db.collection(collectionName).doc();
//     batch.set(docRef, {
//       title: article.title,
//       link: article.link,
//       pubDate: article.pubDate || article.isoDate,
//       createdAt: new Date(),
//     });
//   });
//   await batch.commit();
// }
