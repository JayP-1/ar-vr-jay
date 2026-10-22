using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

// Optional placement scaffold. Add ARRaycastManager and ARPlaneManager to the
// AR Session Origin/XR Origin, then attach this to a scene object and assign
// the spawned furniture Transform. Tap detected planes to move the model.
public class FurniturePlacementStarter : MonoBehaviour
{
    public ARRaycastManager raycastManager;
    public Camera arCamera;
    public Transform furnitureToPlace;
    static readonly List<ARRaycastHit> Hits = new List<ARRaycastHit>();

    void Update()
    {
        if (Input.touchCount == 0 || raycastManager == null || furnitureToPlace == null) return;
        Touch touch = Input.GetTouch(0);
        if (touch.phase != TouchPhase.Began) return;
        if (raycastManager.Raycast(touch.position, Hits, TrackableType.PlaneWithinPolygon))
        {
            Pose pose = Hits[0].pose;
            furnitureToPlace.SetPositionAndRotation(pose.position, pose.rotation);
        }
    }
}
