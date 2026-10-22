import csv
import io
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, send_file, abort

load_dotenv()
ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "data", "catalogue.db")
SEED_PATH = os.path.join(ROOT, "data", "seed_products.json")
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-dev-change-me")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
SESSION_SELECTED = {"product": None, "updated_at": None}

FEATURED_MODELS = [{'slug': 'sofa', 'title': 'Contemporary 3-Seater Sofa', 'category': 'Sofas', 'price': 7874, 'retailer': 'Flipkart', 'source_url': 'https://www.flipkart.com/furniture/sofa-beds/3-seater~seating-capacity/pr?sid=wwe%2Cosg', 'model_url': '/static/models/sofa_contemporary.glb', 'model_file': 'sofa_contemporary.glb', 'dimensions': 'Approx. 2.05 × 0.82 × 0.85 m', 'note': 'Representative teal upholstered sofa model. Comparable 3-seater sofa listings on Flipkart; exact design differs.'}, {'slug': 'chair', 'title': 'Modern Accent Lounge Chair', 'category': 'Chairs', 'price': 7999, 'retailer': 'Urban Ladder', 'source_url': 'https://www.urbanladder.com/collection/accent-chairs', 'model_url': '/static/models/accent_chair.glb', 'model_file': 'accent_chair.glb', 'dimensions': 'Approx. 0.82 × 0.72 × 0.95 m', 'note': 'Representative lounge-chair model. Comparable accent chair listings on Urban Ladder; exact design differs.'}, {'slug': 'table', 'title': 'Wooden Coffee Table', 'category': 'Tables', 'price': 2690, 'retailer': 'Amazon India', 'source_url': 'https://www.amazon.in/s?k=wooden+coffee+table', 'model_url': '/static/models/coffee_table.glb', 'model_file': 'coffee_table.glb', 'dimensions': 'Approx. 1.12 × 0.62 × 0.53 m', 'note': 'Representative wooden coffee table model. Comparable coffee table listing price from Amazon India search; exact design differs.'}, {'slug': 'bed', 'title': 'Queen Bed Frame', 'category': 'Beds', 'price': 11869, 'retailer': 'Amazon India', 'source_url': 'https://www.amazon.in/s?k=queen+size+bed+frame', 'model_url': '/static/models/queen_bed.glb', 'model_file': 'queen_bed.glb', 'dimensions': 'Approx. 1.62 × 2.02 × 1.10 m', 'note': 'Representative queen-bed model. Comparable Amazon India queen-bed listing; exact design differs.'}, {'slug': 'wardrobe', 'title': '3-Door Wardrobe', 'category': 'Storage', 'price': 12990, 'retailer': 'IKEA India', 'source_url': 'https://www.ikea.com/in/en/cat/wardrobes-19053/', 'model_url': '/static/models/wardrobe.glb', 'model_file': 'wardrobe.glb', 'dimensions': 'Approx. 1.50 × 0.56 × 2.08 m', 'note': 'Representative wardrobe model. Comparable IKEA wardrobe listing; exact design differs.'}, {'slug': 'dining', 'title': 'Wooden Dining Table Set', 'category': 'Tables', 'price': 24997, 'retailer': 'Urban Ladder', 'source_url': 'https://www.urbanladder.com/product/diner-4-seater-dining-table-set-9976631', 'model_url': '/static/models/dining_set.glb', 'model_file': 'dining_set.glb', 'dimensions': 'Approx. 1.45 × 1.90 × 1.20 m', 'note': 'Representative dining set model. Comparable dining furniture listings; exact design differs.'}]

HEADERS = {
    "User-Agent": "JKA-Furnishing-Research/1.0 (+local furniture catalogue; respectful public-page fetcher)",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}
ALLOWED_SCHEMES = {"http", "https"}

def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            brand TEXT DEFAULT '',
            category TEXT DEFAULT 'Other',
            price REAL,
            currency TEXT DEFAULT 'INR',
            image_url TEXT DEFAULT '',
            product_url TEXT DEFAULT '',
            retailer TEXT DEFAULT '',
            colour TEXT DEFAULT '',
            style TEXT DEFAULT '',
            description TEXT DEFAULT '',
            model_key TEXT DEFAULT '',
            model_url TEXT DEFAULT '',
            usdz_url TEXT DEFAULT '',
            source_type TEXT DEFAULT 'seed',
            scraped_at TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_url, title)
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS scrape_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT, status TEXT, detail TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        existing_cols = {row[1] for row in con.execute("PRAGMA table_info(products)").fetchall()}
        if "model_url" not in existing_cols:
            con.execute("ALTER TABLE products ADD COLUMN model_url TEXT DEFAULT ''")
        if "usdz_url" not in existing_cols:
            con.execute("ALTER TABLE products ADD COLUMN usdz_url TEXT DEFAULT ''")
        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if os.path.exists(SEED_PATH):
            with open(SEED_PATH, encoding="utf-8") as f:
                products = json.load(f)
            for p in products:
                insert_product(con, p)

def clean_text(value, limit=700):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()[:limit]

def guess_category(text):
    t = (text or "").lower()
    for words, cat in [
        (("sofa", "couch", "loveseat", "sectional"), "Sofas"),
        (("chair", "armchair", "stool", "recliner"), "Chairs"),
        (("table", "desk", "coffee table", "dining"), "Tables"),
        (("bed", "mattress", "headboard"), "Beds"),
        (("wardrobe", "cabinet", "dresser", "shelf", "bookcase", "storage"), "Storage"),
        (("lamp", "light", "lighting"), "Lighting"),
        (("rug", "carpet", "curtain", "cushion", "decor"), "Decor"),
    ]:
        if any(w in t for w in words):
            return cat
    return "Other"

def insert_product(con, p):
    title = clean_text(p.get("title") or p.get("name") or "Untitled product", 240)
    product_url = clean_text(p.get("product_url") or p.get("url") or "", 1200)
    image_url = clean_text(p.get("image_url") or p.get("image") or "", 1200)
    price = p.get("price")
    try:
        price = float(str(price).replace(",", "").replace("₹", "").strip()) if price not in (None, "") else None
    except (ValueError, TypeError):
        price = None
    retailer = clean_text(p.get("retailer") or (urlparse(product_url).netloc.replace("www.", "") if product_url else "Unknown"), 120)
    brand = clean_text(p.get("brand") or "", 120)
    category = clean_text(p.get("category") or guess_category(title), 80)
    data = (title, brand, category, price, clean_text(p.get("currency") or "INR", 8),
            image_url, product_url, retailer, clean_text(p.get("colour") or p.get("color") or "", 80),
            clean_text(p.get("style") or "", 80), clean_text(p.get("description") or "", 1000),
            clean_text(p.get("model_key") or "", 120), clean_text(p.get("model_url") or "", 1200), clean_text(p.get("usdz_url") or "", 1200), clean_text(p.get("source_type") or "scraped", 30),
            clean_text(p.get("scraped_at") or datetime.now(timezone.utc).isoformat(), 50))
    con.execute("""INSERT INTO products
        (title,brand,category,price,currency,image_url,product_url,retailer,colour,style,description,model_key,model_url,usdz_url,source_type,scraped_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(product_url,title) DO UPDATE SET
        brand=excluded.brand, category=excluded.category,
        price=COALESCE(excluded.price,products.price),
        image_url=CASE WHEN excluded.image_url!='' THEN excluded.image_url ELSE products.image_url END,
        retailer=excluded.retailer, description=CASE WHEN excluded.description!='' THEN excluded.description ELSE products.description END,
        model_url=CASE WHEN excluded.model_url!='' THEN excluded.model_url ELSE products.model_url END,
        usdz_url=CASE WHEN excluded.usdz_url!='' THEN excluded.usdz_url ELSE products.usdz_url END,
        source_type=excluded.source_type, scraped_at=excluded.scraped_at""", data)

def get_products():
    with connect() as con:
        rows = con.execute("SELECT * FROM products ORDER BY CASE WHEN price IS NULL THEN 1 ELSE 0 END, price ASC, title ASC").fetchall()
        return [dict(r) for r in rows]

def parse_jsonld(soup, page_url):
    results = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            obj = stack.pop(0)
            if isinstance(obj, dict):
                if "@graph" in obj and isinstance(obj["@graph"], list):
                    stack.extend(obj["@graph"])
                typ = obj.get("@type", [])
                types = [typ] if isinstance(typ, str) else typ
                if any(t.lower() == "product" for t in types if isinstance(t, str)):
                    offers = obj.get("offers") or {}
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    if isinstance(offers, dict) and "price" not in offers and isinstance(offers.get("offers"), list):
                        offers = offers["offers"][0] if offers["offers"] else {}
                    image = obj.get("image", "")
                    if isinstance(image, list):
                        image = image[0] if image else ""
                    elif isinstance(image, dict):
                        image = image.get("url", "")
                    offer_url = offers.get("url", "") if isinstance(offers, dict) else ""
                    try:
                        price = offers.get("price") if isinstance(offers, dict) else None
                    except Exception:
                        price = None
                    results.append({
                        "title": obj.get("name", ""),
                        "brand": (obj.get("brand", {}).get("name", "") if isinstance(obj.get("brand"), dict) else obj.get("brand", "")),
                        "description": obj.get("description", ""),
                        "image_url": urljoin(page_url, str(image)) if image else "",
                        "product_url": urljoin(page_url, str(offer_url)) if offer_url else page_url,
                        "price": price,
                        "currency": offers.get("priceCurrency", "INR") if isinstance(offers, dict) else "INR",
                        "source_type": "scraped"
                    })
                else:
                    for k in ("itemListElement", "mainEntity", "mainEntityOfPage"):
                        v = obj.get(k)
                        if isinstance(v, list): stack.extend(v)
                        elif isinstance(v, dict): stack.append(v)
    return results

def parse_page(url, html):
    soup = BeautifulSoup(html, "html.parser")
    products = parse_jsonld(soup, url)
    if not products:
        title = ""
        for selector in ['meta[property="og:title"]', 'meta[name="twitter:title"]']:
            tag = soup.select_one(selector)
            if tag and tag.get("content"):
                title = tag["content"]; break
        if not title and soup.title:
            title = soup.title.get_text(" ", strip=True)
        desc = ""
        for selector in ['meta[property="og:description"]', 'meta[name="description"]']:
            tag = soup.select_one(selector)
            if tag and tag.get("content"):
                desc = tag["content"]; break
        image = ""
        for selector in ['meta[property="og:image"]', 'meta[name="twitter:image"]']:
            tag = soup.select_one(selector)
            if tag and tag.get("content"):
                image = urljoin(url, tag["content"]); break
        price = None
        for selector in ['meta[property="product:price:amount"]', 'meta[itemprop="price"]']:
            tag = soup.select_one(selector)
            if tag:
                price = tag.get("content") or tag.get_text(strip=True); break
        # Fallback is only one candidate per submitted URL, not an invented product list.
        if title and not any(x in title.lower() for x in ("access denied", "robot or human", "captcha")):
            products = [{
                "title": title, "description": desc, "image_url": image,
                "product_url": url, "price": price, "source_type": "scraped"
            }]
    for p in products:
        p.setdefault("product_url", url)
        p.setdefault("retailer", urlparse(url).netloc.replace("www.", ""))
        p.setdefault("category", guess_category(p.get("title", "") + " " + p.get("description", "")))
        p["scraped_at"] = datetime.now(timezone.utc).isoformat()
    return products

def scrape_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError("Only complete http:// or https:// URLs are accepted.")
    # This app intentionally does not bypass bot protection, authentication, or access controls.
    resp = requests.get(url, headers=HEADERS, timeout=18, allow_redirects=True)
    if resp.status_code in (401, 403, 429):
        raise RuntimeError(f"Retailer returned HTTP {resp.status_code}; no bypass attempted.")
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type.lower() and "text" not in content_type.lower():
        raise RuntimeError(f"Page is not HTML/text ({content_type or 'unknown content type'}).")
    return parse_page(resp.url, resp.text)

@app.route("/")
def index():
    products = get_products()
    cats = sorted({p["category"] for p in products if p.get("category")})
    retailers = sorted({p["retailer"] for p in products if p.get("retailer")})
    model_by_category = {m["category"]: m["model_url"] for m in FEATURED_MODELS}
    model_by_category["Decor"] = "/static/models/accent_chair.glb"
    model_by_category["Lighting"] = "/static/models/coffee_table.glb"
    return render_template("index.html", products=products, categories=cats, retailers=retailers, featured_models=FEATURED_MODELS, model_by_category=model_by_category)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        urls = [x.strip() for x in request.form.get("urls", "").splitlines() if x.strip()]
        urls = urls[:25]
        added = 0
        results = []
        for url in urls:
            try:
                items = scrape_url(url)
                with connect() as con:
                    for p in items:
                        insert_product(con, p)
                    con.execute("INSERT INTO scrape_runs(url,status,detail) VALUES(?,?,?)",
                                (url, "ok", f"Parsed {len(items)} candidate product record(s)"))
                added += len(items)
                results.append({"url": url, "status": "ok", "detail": f"{len(items)} candidate product record(s) parsed"})
            except Exception as e:
                with connect() as con:
                    con.execute("INSERT INTO scrape_runs(url,status,detail) VALUES(?,?,?)",
                                (url, "error", str(e)[:500]))
                results.append({"url": url, "status": "error", "detail": str(e)[:300]})
            time.sleep(1.0)
        flash(f"Processed {len(urls)} URL(s); parsed {added} candidate record(s). Review the catalogue for duplicates or bad metadata.", "success")
        return render_template("admin.html", results=results, count=len(get_products()))
    with connect() as con:
        runs = [dict(r) for r in con.execute("SELECT * FROM scrape_runs ORDER BY id DESC LIMIT 15").fetchall()]
        existing_cols = {row[1] for row in con.execute("PRAGMA table_info(products)").fetchall()}
        if "model_url" not in existing_cols:
            con.execute("ALTER TABLE products ADD COLUMN model_url TEXT DEFAULT ''")
        if "usdz_url" not in existing_cols:
            con.execute("ALTER TABLE products ADD COLUMN usdz_url TEXT DEFAULT ''")
        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    return render_template("admin.html", results=[], count=count, runs=runs)


@app.route("/room-preview/<int:product_id>")
def room_preview(product_id):
    with connect() as con:
        row = con.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template("room_preview.html", product=dict(row))


@app.route("/featured-ar/<slug>")
def featured_ar(slug):
    model = next((m for m in FEATURED_MODELS if m["slug"] == slug), None)
    if not model:
        abort(404)
    return render_template("featured_ar.html", model=model)

@app.route("/api/products")
def api_products():
    return jsonify({"count": len(get_products()), "products": get_products()})

@app.route("/api/selected", methods=["GET", "POST"])
def api_selected():
    global SESSION_SELECTED
    if request.method == "POST":
        p = request.get_json(silent=True) or {}
        SESSION_SELECTED = {"product": p, "updated_at": datetime.now(timezone.utc).isoformat()}
        return jsonify({"ok": True, **SESSION_SELECTED})
    return jsonify(SESSION_SELECTED)

@app.route("/api/select/<int:product_id>", methods=["POST"])
def select_product(product_id):
    global SESSION_SELECTED
    with connect() as con:
        row = con.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not row:
        abort(404)
    p = dict(row)
    SESSION_SELECTED = {"product": p, "updated_at": datetime.now(timezone.utc).isoformat()}
    return jsonify({"ok": True, **SESSION_SELECTED})



def flipkart_configured():
    return bool(os.getenv("FLIPKART_AFFILIATE_ID", "").strip() and os.getenv("FLIPKART_AFFILIATE_TOKEN", "").strip())

def normalize_flipkart_item(item):
    base = item.get("productBaseInfo") or item.get("productBaseInfoV1") or {}
    attrs = base.get("productAttributes") or {}
    images = attrs.get("imageUrls") or {}
    image = images.get("400x400") or images.get("275x275") or images.get("200x200") or images.get("unknown") or ""
    price_obj = attrs.get("sellingPrice") or attrs.get("flipkartSpecialPrice") or attrs.get("flipkartSellingPrice") or {}
    return {
        "title": attrs.get("title") or "Furniture product",
        "brand": attrs.get("productBrand") or "",
        "category": guess_category((attrs.get("title") or "") + " " + (attrs.get("productDescription") or "")),
        "price": (price_obj.get("amount") if isinstance(price_obj, dict) else None),
        "currency": (price_obj.get("currency") if isinstance(price_obj, dict) else "INR") or "INR",
        "image_url": image, "product_url": attrs.get("productUrl") or "",
        "retailer": "Flipkart", "colour": attrs.get("color") or attrs.get("colour") or "",
        "description": attrs.get("productDescription") or "",
        "source_type": "flipkart-affiliate-api", "in_stock": attrs.get("inStock")
    }

@app.route("/api/discover")
def api_discover():
    query = clean_text(request.args.get("q", ""), 120)
    if not query:
        return jsonify({"query": "", "products": [], "sources": [], "message": "Enter a furniture search term."})
    # Always return cross-retailer search links. These do not pretend to be imported product records.
    from urllib.parse import quote_plus
    q = quote_plus(query)
    sources = [
        {"name":"Flipkart", "url":f"https://www.flipkart.com/search?q={q}"},
        {"name":"Amazon India", "url":f"https://www.amazon.in/s?k={q}"},
        {"name":"IKEA India", "url":f"https://www.ikea.com/in/en/search/?q={q}"},
        {"name":"Urban Ladder", "url":f"https://www.urbanladder.com/search?q={q}"},
        {"name":"Pepperfry", "url":f"https://www.pepperfry.com/site_product/search?q={q}"},
        {"name":"WoodenStreet", "url":f"https://www.woodenstreet.com/search?query={q}"},
        {"name":"Royaloak", "url":f"https://www.royaloakindia.com/catalogsearch/result/?q={q}"},
        {"name":"Google Shopping", "url":f"https://www.google.com/search?tbm=shop&q={q}"}
    ]
    products = []
    message = "Cross-retailer links ready. Add approved Flipkart Affiliate credentials for live product results."
    if flipkart_configured():
        try:
            resp = requests.get(
                "https://affiliate-api.flipkart.net/affiliate/search/json",
                params={"query": query, "resultCount": 10},
                headers={"Fk-Affiliate-Id": os.getenv("FLIPKART_AFFILIATE_ID", "").strip(),
                         "Fk-Affiliate-Token": os.getenv("FLIPKART_AFFILIATE_TOKEN", "").strip(),
                         "Accept":"application/json"}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("productInfoList", []):
                normalized = normalize_flipkart_item(item)
                if normalized.get("title") and (normalized.get("category") != "Other" or any(w in query.lower() for w in ("furniture","sofa","chair","table","bed","lamp","wardrobe","shelf"))):
                    products.append(normalized)
            message = f"Live Flipkart affiliate results: {len(products)} product(s). Other retailers are available through search links."
        except Exception as exc:
            message = "Flipkart API could not be reached. Check affiliate credentials and account access; cross-retailer links still work."
    return jsonify({"query": query, "products": products, "sources": sources, "flipkart_api_enabled": flipkart_configured(), "message": message})

@app.route("/api/flipkart/import", methods=["POST"])
def import_flipkart_results():
    # Explicit admin action: import results from a search query, not an automatic customer task.
    if not flipkart_configured():
        return jsonify({"ok":False,"error":"Set FLIPKART_AFFILIATE_ID and FLIPKART_AFFILIATE_TOKEN in .env first."}), 400
    query = clean_text((request.get_json(silent=True) or {}).get("q", ""), 120)
    if not query:
        return jsonify({"ok":False,"error":"Enter a search query."}), 400
    try:
        resp=requests.get("https://affiliate-api.flipkart.net/affiliate/search/json", params={"query":query,"resultCount":10}, headers={"Fk-Affiliate-Id":os.getenv("FLIPKART_AFFILIATE_ID","").strip(),"Fk-Affiliate-Token":os.getenv("FLIPKART_AFFILIATE_TOKEN","").strip(),"Accept":"application/json"}, timeout=15)
        resp.raise_for_status()
        items=[normalize_flipkart_item(x) for x in resp.json().get("productInfoList", [])]
        with connect() as con:
            for item in items:
                if item.get("title") and item.get("product_url"):
                    insert_product(con,item)
        return jsonify({"ok":True,"imported":len(items)})
    except Exception:
        return jsonify({"ok":False,"error":"Flipkart search failed. Verify credentials/account access and try again."}), 502

@app.route("/export.csv")
def export_csv():
    products = get_products()
    output = io.StringIO()
    fields = ["id","title","brand","category","price","currency","image_url","product_url","retailer","colour","style","description","model_key","model_url","usdz_url","source_type","scraped_at"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader(); writer.writerows(products)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")), mimetype="text/csv",
                     as_attachment=True, download_name="jka_furniture_catalogue.csv")

@app.route("/export.json")
def export_json():
    payload = json.dumps(get_products(), ensure_ascii=False, indent=2).encode("utf-8")
    return send_file(io.BytesIO(payload), mimetype="application/json", as_attachment=True, download_name="jka_furniture_catalogue.json")

@app.route("/import.csv", methods=["POST"])
def import_csv():
    f = request.files.get("csv_file")
    if not f:
        flash("Choose a CSV file first.", "error")
        return redirect(url_for("admin"))
    try:
        stream = io.StringIO(f.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)
        n = 0
        with connect() as con:
            for row in reader:
                row["source_type"] = "csv-import"
                insert_product(con, row); n += 1
        flash(f"Imported {n} CSV row(s).", "success")
    except Exception as e:
        flash(f"Could not import CSV: {e}", "error")
    return redirect(url_for("admin"))

@app.route("/template.csv")
def template_csv():
    return send_file(os.path.join(ROOT, "data", "catalog_template.csv"), as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
