import db from "../config/firebase.js";

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
    batch.set(docRef, {
      title: article.title,
      link: article.link,
      pubDate: article.pubDate || article.isoDate,
      source: article.source || "Unknown",
      createdAt: new Date(),
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
