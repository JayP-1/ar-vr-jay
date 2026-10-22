# JKA Furnishing final demo package

## Web demo (fastest presentation path)
Run the Flask catalogue as usual. The top section contains six interactive GLB furniture models. You can rotate them on desktop; on a supported mobile device, the model-viewer `Place in my room` control launches native AR. For phone AR, the site must be served over HTTPS. `127.0.0.1` only works locally on the Mac.

The 3D furniture files are representative, procedurally assembled models with real mesh geometry and materials. They are not scans of the exact retail products. The displayed prices are reference prices observed on retailer listing/search pages and can change; use the retailer source links to verify. Retailer links are not affiliate-tracked unless your own approved affiliate IDs are configured.

## About the Unity Companion screen
The mobile app's `New Project / Import Project` screen does not import or run a Flask website. For a native Unity AR build, use Unity Editor on the Mac to create/open a Unity project, install AR Foundation plus the platform plugin (ARCore for Android or ARKit for iOS), add an AR Session + XR Origin with AR Plane Manager and AR Raycast Manager, and attach `JKAFurniturePlacer` to a scene object. This folder contains a starter script and the model GLBs. It is not a signed, ready-to-install mobile app and must be configured and built in Unity Editor.

## Models
`static/models/` contains six GLB files for the web 3D viewer. Copies are included under `unity/JKA_Unity_AR_Starter/Assets/StreamingAssets/Models/`.
