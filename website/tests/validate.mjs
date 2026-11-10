#!/usr/bin/env node
// NaMiOS website — kiểm thử tối thiểu trước khi bàn giao.
// Chạy: node tests/validate.mjs   (từ thư mục website/)
//
// Kiểm 4 nhóm theo docs/specs/namios-pl17-website/04_KY_THUAT_NGHIEM_THU.md §5:
//  A. release-manifest.json khớp cấu trúc schema + bất biến pre_release
//  B. compatibility.json khớp cấu trúc schema (apps/devices/legend)
//  C. KHÔNG có nút/link tải ISO giả nào trong HTML tĩnh khi status=pre_release
//  D. Link nội bộ (href tới trang .html khác trong site) không bị 404

import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

let failures = 0;
let checks = 0;

function ok(label) {
  checks++;
  console.log("  OK   " + label);
}
function fail(label, detail) {
  checks++;
  failures++;
  console.log("  FAIL " + label + (detail ? " — " + detail : ""));
}
function assert(cond, label, detail) {
  if (cond) ok(label); else fail(label, detail);
}

function readJSON(relPath) {
  return JSON.parse(readFileSync(path.join(ROOT, relPath), "utf-8"));
}
function readText(relPath) {
  return readFileSync(path.join(ROOT, relPath), "utf-8");
}

console.log("== A. release-manifest.json ==");
{
  const schema = readJSON("data/release-manifest.schema.json");
  const manifest = readJSON("data/release-manifest.json");

  assert(Array.isArray(schema.required) && schema.required.length > 0, "schema có danh sách required");
  for (const key of schema.required) {
    assert(Object.prototype.hasOwnProperty.call(manifest, key), "manifest có field bắt buộc '" + key + "'");
  }
  assert(schema.properties.status.enum.includes(manifest.status), "status nằm trong enum hợp lệ", manifest.status);
  assert(manifest.status === "pre_release", "status hiện tại = pre_release (đúng với giai đoạn dự án)", manifest.status);

  if (manifest.status === "pre_release") {
    assert(Array.isArray(manifest.downloads) && manifest.downloads.length === 0, "pre_release: downloads[] rỗng — KHÔNG có ISO nào được công bố");
    assert(Array.isArray(manifest.architectures) && manifest.architectures.length === 0, "pre_release: architectures[] rỗng");
    assert(manifest.release_date === null, "pre_release: release_date = null");
  }
  assert(manifest.notify && manifest.notify.mode === "demo", "notify.mode = 'demo' (form không thu thập email thật)");
  assert(typeof manifest.notify.note_vi === "string" && manifest.notify.note_vi.length > 20, "notify có ghi chú demo bằng tiếng Việt");

  for (const d of manifest.downloads) {
    assert(/^[a-f0-9]{64}$/.test(d.sha256 || ""), "download item có sha256 64-hex hợp lệ", d.filename);
  }

  for (const f of manifest.features || []) {
    const allowed = schema.properties.features.items.properties.state.enum;
    assert(allowed.includes(f.state), "feature '" + f.claim_id + "' có state hợp lệ", f.state);
  }
}

console.log("\n== B. compatibility.json ==");
{
  const schema = readJSON("data/compatibility.schema.json");
  const data = readJSON("data/compatibility.json");
  const appDef = schema.definitions.appRecord;
  const devDef = schema.definitions.deviceRecord;

  assert(["verified", "unverified", "cannot_publish"].every((k) => data.legend[k] && data.legend[k].label_vi && data.legend[k].description_vi),
    "legend có đủ 3 trạng thái minh bạch với nhãn + mô tả tiếng Việt");

  const appIds = new Set();
  for (const app of data.apps) {
    for (const key of appDef.required) {
      assert(Object.prototype.hasOwnProperty.call(app, key), "app '" + app.id + "' có field '" + key + "'");
    }
    assert(appDef.properties.category.enum.includes(app.category), "app '" + app.id + "' có category hợp lệ", app.category);
    assert(appDef.properties.type.enum.includes(app.type), "app '" + app.id + "' có type hợp lệ", app.type);
    assert(appDef.properties.result.enum.includes(app.result), "app '" + app.id + "' có result hợp lệ", app.result);
    assert(appDef.properties.transparency_status.enum.includes(app.transparency_status), "app '" + app.id + "' có transparency_status hợp lệ", app.transparency_status);
    assert(!appIds.has(app.id), "app id '" + app.id + "' không trùng lặp");
    appIds.add(app.id);
  }

  const devIds = new Set();
  for (const dev of data.devices) {
    for (const key of devDef.required) {
      assert(Object.prototype.hasOwnProperty.call(dev, key), "device '" + dev.id + "' có field '" + key + "'");
    }
    assert(devDef.properties.result.enum.includes(dev.result), "device '" + dev.id + "' có result hợp lệ", dev.result);
    assert(devDef.properties.transparency_status.enum.includes(dev.transparency_status), "device '" + dev.id + "' có transparency_status hợp lệ", dev.transparency_status);
    for (const c of dev.connection || []) {
      assert(devDef.properties.connection.items.enum.includes(c), "device '" + dev.id + "' connection hợp lệ", c);
    }
    assert(!devIds.has(dev.id), "device id '" + dev.id + "' không trùng lặp");
    devIds.add(dev.id);
  }

  // Không có record nào "verified" mà thiếu ngày kiểm — tính nhất quán tối thiểu.
  for (const app of data.apps) {
    if (app.transparency_status === "verified") {
      assert(!!app.last_tested, "app '" + app.id + "' đánh dấu verified thì phải có last_tested", app.id);
    }
  }
}

console.log("\n== C. Không có nút/link tải ISO giả (pre_release) ==");
{
  const manifest = readJSON("data/release-manifest.json");
  const downloadHtml = readText("download.html");
  const downloadJs = readText("js/download.js");

  assert(manifest.status === "pre_release", "(điều kiện) manifest đang ở pre_release — bắt buộc không có nút tải tĩnh");

  // Lấy đúng khối #download-cta tĩnh (trước khi JS chạy) — khối này chỉ được
  // phép chứa skeleton loading, KHÔNG được chứa nút .btn (nút chỉ do download.js
  // render ra sau khi đọc status từ manifest).
  const ctaBlockMatch = downloadHtml.match(/<div id="download-cta"[\s\S]*?<\/section>/);
  assert(!!ctaBlockMatch, "tìm thấy khối #download-cta trong download.html");
  const ctaBlock = ctaBlockMatch ? ctaBlockMatch[0] : "";
  assert(!/class="btn/.test(ctaBlock), "khối #download-cta tĩnh KHÔNG chứa nút .btn viết cứng (chỉ skeleton)");
  assert(!/\.iso/i.test(ctaBlock), "khối #download-cta tĩnh KHÔNG chứa đường dẫn .iso viết cứng");

  assert(downloadHtml.includes("Nhận thông báo khi có bản thử nghiệm"), "download.html có CTA 'Nhận thông báo khi có bản thử nghiệm'");
  assert(downloadHtml.includes("Xem tiến độ") === false || downloadHtml.includes("tien-do"), "có đường dẫn tới trang tiến độ (about.html#tien-do)");

  assert(downloadJs.includes('status === "pre_release"'), "download.js có nhánh xử lý status pre_release");
  assert(downloadJs.includes("Nhận thông báo khi có bản thử nghiệm"), "download.js render đúng CTA cho pre_release");
  assert(downloadJs.includes("Xem tiến độ"), "download.js render CTA 'Xem tiến độ' cho pre_release");

  // Quét toàn site: không có href trỏ thẳng tới file .iso nào trong HTML tĩnh.
  const fsmod = await import("node:fs");
  const htmlFiles = fsmod.readdirSync(ROOT).filter((f) => f.endsWith(".html"));
  let isoHrefFound = false;
  for (const file of htmlFiles) {
    const text = readText(file);
    if (/href\s*=\s*["'][^"']*\.iso["']/i.test(text)) { isoHrefFound = true; fail("không có href .iso trong " + file); }
  }
  if (!isoHrefFound) ok("không có file .html nào chứa href trỏ thẳng tới *.iso");
}

console.log("\n== D. Link nội bộ không 404 (href tới *.html trong site) ==");
{
  const fsmod = await import("node:fs");
  const htmlFiles = fsmod.readdirSync(ROOT).filter((f) => f.endsWith(".html"));
  const hrefRe = /href\s*=\s*"([^":#][^"]*?\.html)(#[^"]*)?"/g;
  let brokenCount = 0;
  for (const file of htmlFiles) {
    const text = readText(file);
    let m;
    while ((m = hrefRe.exec(text))) {
      const target = m[1];
      if (/^https?:\/\//i.test(target)) continue;
      const resolved = path.join(ROOT, target);
      if (!existsSync(resolved)) { fail(file + " -> " + target + " (file không tồn tại)"); brokenCount++; }
    }
  }
  if (brokenCount === 0) ok("tất cả href nội bộ *.html trỏ tới file có thật trong website/");
}

console.log("\n== Tổng kết ==");
console.log(checks + " kiểm tra, " + failures + " lỗi.");
if (failures > 0) {
  console.log("KẾT QUẢ: FAIL");
  process.exit(1);
} else {
  console.log("KẾT QUẢ: PASS");
  process.exit(0);
}
