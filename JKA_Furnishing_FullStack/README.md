# JKA Furnishing — Cross-Retail Catalogue + Web AR Starter

## Run on macOS
```bash
cd "/Users/jayprakash/Desktop/JAY-VRAAAAA/JKA_Furnishing_FullStack"
source .venv/bin/activate
PORT=5001 python app.py
```
Open http://127.0.0.1:5001. Keep Terminal open.

## What's included
- Existing colourful catalogue UI retained; search, category/retailer filters, sorting, favourites and product handoff.
- Cross-retailer search links for Flipkart, Amazon India, IKEA India, Urban Ladder, Pepperfry, WoodenStreet, Royaloak and Google Shopping. These are live retailer search pages, not copied listings.
- Optional official Flipkart Affiliate API keyword search, enabled only when credentials from an approved account are added to `.env`. API search currently returns up to 10 products per query according to the official docs.
- SQLite catalogue, public-page metadata scraper, CSV import/export, JSON API and selected-product endpoint.

## Enable Flipkart API (optional)
1. Register at https://affiliate.flipkart.com/registerme and confirm your account is eligible for API access.
2. Generate your Affiliate API Token from the official dashboard.
3. Copy `.env.example` to `.env` and set `FLIPKART_AFFILIATE_ID` and `FLIPKART_AFFILIATE_TOKEN`. Never share or commit `.env`.
4. Restart the app. Search using the “Find it everywhere” section on the homepage.

The API is one source, not a complete catalogue of the internet. The cross-retailer links are available even without credentials. Add further authorised feeds/API integrations for automatic in-site comparisons across other retailers. Do not bypass login, CAPTCHA, rate limits or site access restrictions.

## Cross-platform AR (web-based)
- The site currently hands off selected product metadata. A metadata record is not itself a 3D model.
- For a true browser-to-AR experience, host a compatible `.glb`/`.gltf` model and (for iPhone Quick Look) a `.usdz` asset, then attach those model URLs to product records and render them with Google `<model-viewer>`. See https://modelviewer.dev/docs/index.html and Apple Quick Look docs.
- iPhone: open the hosted HTTPS website in Safari and tap “View in AR” for products with USDZ.
- Android: open the hosted HTTPS website in Chrome and tap “View in AR” for supported GLB models; Scene Viewer/ARCore support depends on device compatibility.
- For phone access on your Wi-Fi, run `ipconfig getifaddr en0` on the Mac and open `http://MAC_IP:5001` on the phone. For public access and reliable AR, deploy behind HTTPS (e.g. Render/Railway/Fly.io) and set environment variables there.

## Limitations to state accurately
- This is a working student-project starter, not a universal crawler or production deployment.
- The initial seed entries are illustrative placeholders; do not treat them as verified offers.
- A product is only AR-ready when a compatible 3D asset is available. Retailer photos cannot be converted automatically into accurate, true-scale furniture models.
- Automatic refresh across sources requires each source's authorised API/feed and terms-compliant integration.


## Presentation demo — final package

- The seeded catalogue contains 80+ furniture search cards across sofas, chairs, tables, beds, storage, lighting and decor.
- Each card has an expandable list of retailer search links: Flipkart, Amazon India, IKEA India, Urban Ladder, Pepperfry, WoodenStreet, Royaloak and Google Shopping. They show current search results at the retailer; they are not individual verified offers.
- **Try in my room** opens `/room-preview/<product_id>` with a browser-camera overlay and interactive move/rotate/resize controls. The sample-room fallback remains usable if camera permission is unavailable.
- This is a camera-overlay demo, not true world-locked 3D AR. True AR requires compatible 3D model assets and device/browser testing.
- Affiliate tracking is not fabricated. To use approved Flipkart Affiliate API data, supply your own affiliate ID/token in `.env`; other retailers need their own approved feeds or programmes.
- Use `http://127.0.0.1:5001` on the same Mac for the easiest camera permission path. On phones, use HTTPS for camera access.


## Final 3D / AR presentation build
The top of the home page now contains six interactive GLB models (sofa, accent chair, coffee table, queen bed, wardrobe, dining set). These are actual 3D mesh assets with materials created for this student demo, not emoji overlays and not scans of exact retailer products. The featured cards show a reference price, retailer/source link, and a note that price/product details may change. The rest of the large catalogue uses search links that take users to retailer pages for live offers.

Each featured model has a full 3D page and the model-viewer AR handoff (`webxr`, Android Scene Viewer and iOS Quick Look). On desktop, rotate and inspect the model. On a compatible phone, the native AR launch needs HTTPS and supported browser/device services. See `unity/JKA_Unity_AR_Starter/README.md` for the native Unity AR Foundation starter; the mobile Companion screen is not a direct bridge from the Flask website.


## Product-card AR shortcut
Every catalogue card now has “Try similar in 3D / AR”. It selects a representative GLB model by product category and opens the same AR viewer. This does not mean a retailer listing is automatically converted into its exact 3D model; exact-SKU matching requires an authorised/available model asset. AR scale is set to auto so supported native viewers can allow pinch resizing.
