import { runRssJob } from "./tasks/rssJob.js";

runRssJob()
  .then(() => {
    console.log("✅ RSS job finished.");
    process.exit(0);
  })
  .catch((err) => {
    console.error("❌ Error:", err.message);
    process.exit(1);
  });

// import cron from "node-cron";
// import { runRssJob } from "./tasks/rssJob.js";

// const TIMEZONE = "Asia/Ho_Chi_Minh";

// cron.schedule(
//   "0 6,11,16,21 * * *",
//   () => {
//     console.log(
//       `[CRON] Bắt đầu job theo lịch lúc ${new Date().toLocaleString("vi-VN", {
//         timeZone: TIMEZONE,
//       })}`
//     );
//     runRssJob();
//   },
//   {
//     timezone: TIMEZONE,
//   }
// );

// console.log(
//   `[INIT] Khởi động job ngay lúc ${new Date().toLocaleString("vi-VN", {
//     timeZone: TIMEZONE,
//   })}`
// );
// runRssJob();
