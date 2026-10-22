#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using Unity.XR.CoreUtils;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using System;

public static class JKASetupARScene
{
    [MenuItem("JKA Furnishing/Create AR Placement Scene")]
    public static void CreateScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var session = new GameObject("AR Session"); session.AddComponent<ARSession>();
        var origin = new GameObject("XR Origin (Mobile AR)");
        var xrOrigin = origin.AddComponent<XROrigin>();
        var cameraGO = new GameObject("AR Camera"); cameraGO.tag = "MainCamera";
        cameraGO.transform.SetParent(origin.transform, false);
        cameraGO.transform.localPosition = new Vector3(0, 1.2f, 0);
        var cam = cameraGO.AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
        cameraGO.AddComponent<ARCameraManager>(); cameraGO.AddComponent<ARCameraBackground>();
        xrOrigin.Camera = cam;
        var planes = origin.AddComponent<ARPlaneManager>();
        var raycasts = origin.AddComponent<ARRaycastManager>();
        var placerGO = new GameObject("JKA Furniture Placer");
        var placer = placerGO.AddComponent<JKAFurniturePlacer>();
        var so = new SerializedObject(placer);
        so.FindProperty("raycastManager").objectReferenceValue = raycasts;
        so.FindProperty("planeManager").objectReferenceValue = planes;
        so.FindProperty("arCamera").objectReferenceValue = cam;
        so.ApplyModifiedPropertiesWithoutUndo();
        CreateControls(placer);
        var lightGO = new GameObject("Directional Light");
        var light = lightGO.AddComponent<Light>(); light.type = LightType.Directional; light.intensity = 1.1f;
        lightGO.transform.rotation = Quaternion.Euler(50,-30,0);
        EditorSceneManager.SaveScene(scene, "Assets/Scenes/JKA_AR_Placement.unity");
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene("Assets/Scenes/JKA_AR_Placement.unity", true) };
        EditorUtility.DisplayDialog("JKA Furnishing", "AR placement scene created. Connect JKAFurniturePlacer to UI buttons for model selection, then configure ARCore/ARKit and build to a supported phone.", "OK");
    }
    static void CreateControls(JKAFurniturePlacer placer)
    {
        var es = new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
        var canvasGO = new GameObject("JKA AR Controls", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        var canvas = canvasGO.GetComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvasGO.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(1080, 1920);
        var panelGO = new GameObject("Control Panel", typeof(RectTransform), typeof(Image), typeof(VerticalLayoutGroup));
        panelGO.transform.SetParent(canvasGO.transform, false);
        var pr = panelGO.GetComponent<RectTransform>(); pr.anchorMin = new Vector2(0,0); pr.anchorMax = new Vector2(1,0); pr.pivot = new Vector2(.5f,0); pr.anchoredPosition = new Vector2(0,28); pr.sizeDelta = new Vector2(-28,260);
        panelGO.GetComponent<Image>().color = new Color(.08f,.09f,.08f,.88f);
        var layout = panelGO.GetComponent<VerticalLayoutGroup>(); layout.padding = new RectOffset(12,12,12,12); layout.spacing=8; layout.childControlHeight=true; layout.childForceExpandHeight=true; layout.childControlWidth=true; layout.childForceExpandWidth=true;
        var row1 = MakeRow(panelGO.transform, "Furniture choices");
        string[] names = {"SOFA", "CHAIR", "TABLE", "BED", "WARDROBE"};
        for (int i=0;i<names.Length;i++) { int idx=i; MakeButton(row1, names[i], ()=>placer.SelectModel(idx)); }
        var row2 = MakeRow(panelGO.transform, "Placement controls");
        MakeButton(row2, "ROTATE +15°", ()=>placer.RotatePlaced());
        MakeButton(row2, "SMALLER", ()=>placer.ScalePlaced(.9f));
        MakeButton(row2, "LARGER", ()=>placer.ScalePlaced(1.1f));
    }
    static Transform MakeRow(Transform parent, string name)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(HorizontalLayoutGroup)); go.transform.SetParent(parent,false);
        var l=go.GetComponent<HorizontalLayoutGroup>(); l.spacing=8; l.childControlHeight=true; l.childForceExpandHeight=true; l.childControlWidth=true; l.childForceExpandWidth=true;
        return go.transform;
    }
    static void MakeButton(Transform parent, string label, Action click)
    {
        var go = new GameObject(label, typeof(RectTransform), typeof(Image), typeof(Button)); go.transform.SetParent(parent,false);
        var image=go.GetComponent<Image>(); image.color = label.Contains("SOFA") ? new Color(.78f,.89f,.42f) : new Color(.96f,.95f,.90f);
        var button=go.GetComponent<Button>(); button.onClick.AddListener(()=>click());
        var textGO = new GameObject("Label", typeof(RectTransform), typeof(Text)); textGO.transform.SetParent(go.transform,false);
        var t=textGO.GetComponent<Text>(); t.text=label; t.alignment=TextAnchor.MiddleCenter; t.font=Resources.GetBuiltinResource<Font>("Arial.ttf"); t.fontSize=24; t.fontStyle=FontStyle.Bold; t.color=new Color(.13f,.14f,.13f);
        var tr=textGO.GetComponent<RectTransform>(); tr.anchorMin=Vector2.zero; tr.anchorMax=Vector2.one; tr.offsetMin=Vector2.zero; tr.offsetMax=Vector2.zero;
    }

}
#endif