using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

public class JKAFurniturePlacer : MonoBehaviour
{
    [Header("Attach to an object in an AR Foundation scene")]
    public ARRaycastManager raycastManager;
    public ARPlaneManager planeManager;
    public Camera arCamera;
    public int selectedModel = 0;
    static readonly List<ARRaycastHit> Hits = new List<ARRaycastHit>();
    GameObject placed;

    void Update()
    {
        if (Input.touchCount == 0 || Input.GetTouch(0).phase != TouchPhase.Began) return;
        if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject(Input.GetTouch(0).fingerId)) return;
        var touch = Input.GetTouch(0);
        if (raycastManager != null && raycastManager.Raycast(touch.position, Hits, TrackableType.PlaneWithinPolygon))
        {
            Pose pose = Hits[0].pose;
            if (placed == null) placed = BuildFurniture(selectedModel);
            placed.transform.SetPositionAndRotation(pose.position, pose.rotation);
            placed.SetActive(true);
        }
    }

    public void SelectModel(int modelIndex) { selectedModel = Mathf.Clamp(modelIndex, 0, 4); }
    public void RotatePlaced() { if (placed != null) placed.transform.Rotate(0, 15, 0, Space.World); }
    public void ScalePlaced(float factor) { if (placed != null) placed.transform.localScale = Vector3.one * Mathf.Clamp(placed.transform.localScale.x * factor, .4f, 2f); }

    GameObject BuildFurniture(int kind)
    {
        GameObject root = new GameObject("JKA Furniture Preview");
        Color wood = new Color(.43f,.25f,.13f), cushion = new Color(.16f,.43f,.39f), cream = new Color(.82f,.76f,.66f), dark = new Color(.12f,.13f,.13f);
        if (kind == 0) { // sofa
            Part(root,"Sofa base",new Vector3(0,.28f,0),new Vector3(1.8f,.25f,.72f),wood);
            Part(root,"Seat cushion",new Vector3(0,.46f,.02f),new Vector3(1.72f,.18f,.66f),cushion);
            Part(root,"Back",new Vector3(0,.78f,-.28f),new Vector3(1.75f,.65f,.16f),cushion);
            Part(root,"Left arm",new Vector3(-.88f,.58f,0),new Vector3(.16f,.52f,.76f),cushion); Part(root,"Right arm",new Vector3(.88f,.58f,0),new Vector3(.16f,.52f,.76f),cushion);
        } else if (kind == 1) { // lounge chair
            Part(root,"Chair seat",new Vector3(0,.45f,0),new Vector3(.76f,.18f,.62f),cushion); Part(root,"Chair back",new Vector3(0,.78f,-.25f),new Vector3(.76f,.66f,.14f),cream);
            Part(root,"Left arm",new Vector3(-.39f,.62f,0),new Vector3(.1f,.35f,.62f),wood); Part(root,"Right arm",new Vector3(.39f,.62f,0),new Vector3(.1f,.35f,.62f),wood);
        } else if (kind == 2) { // table
            Part(root,"Tabletop",new Vector3(0,.48f,0),new Vector3(1.05f,.09f,.62f),wood);
            for(int x=-1;x<=1;x+=2) for(int z=-1;z<=1;z+=2) Part(root,"Table leg",new Vector3(x*.43f,.23f,z*.23f),new Vector3(.07f,.46f,.07f),dark);
        } else if (kind == 3) { // bed
            Part(root,"Bed frame",new Vector3(0,.25f,0),new Vector3(1.5f,.2f,1.9f),wood); Part(root,"Mattress",new Vector3(0,.4f,0),new Vector3(1.45f,.18f,1.82f),cream); Part(root,"Headboard",new Vector3(0,.72f,-.93f),new Vector3(1.55f,.8f,.12f),wood);
        } else { // wardrobe
            Part(root,"Wardrobe body",new Vector3(0,1f,0),new Vector3(1.15f,2f,.5f),wood); Part(root,"Left door",new Vector3(-.29f,1f,-.26f),new Vector3(.55f,1.9f,.025f),cream); Part(root,"Right door",new Vector3(.29f,1f,-.26f),new Vector3(.55f,1.9f,.025f),cream);
        }
        root.transform.localScale = Vector3.one * .6f;
        return root;
    }
    GameObject Part(GameObject parent,string name,Vector3 position,Vector3 scale,Color color)
    {
        GameObject p=GameObject.CreatePrimitive(PrimitiveType.Cube); p.name=name; p.transform.SetParent(parent.transform,false); p.transform.localPosition=position; p.transform.localScale=scale;
        var renderer=p.GetComponent<Renderer>(); var mat=new Material(Shader.Find("Universal Render Pipeline/Lit")); mat.color=color; renderer.material=mat; return p;
    }
}