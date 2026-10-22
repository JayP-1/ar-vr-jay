using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

// Starter for a Unity AR Foundation app. Add this to a scene object and map
// each model_key to a prefab in the Inspector. Set apiBaseUrl to your Mac LAN IP.
public class FurnitureARReceiver : MonoBehaviour
{
    [Serializable] public class ProductPayload
    {
        public int id;
        public string title;
        public string brand;
        public string category;
        public float? price;
        public string currency;
        public string product_url;
        public string model_key;
    }
    [Serializable] public class SelectedPayload
    {
        public ProductPayload product;
        public string updated_at;
    }
    [Serializable] public class ProductPrefab
    {
        public string modelKey;
        public GameObject prefab;
    }

    [Header("Set to http://YOUR_MAC_LAN_IP:5000")]
    public string apiBaseUrl = "http://192.168.1.10:5000";
    public float pollSeconds = 3f;
    public List<ProductPrefab> productPrefabs = new List<ProductPrefab>();
    public Transform placementAnchor;
    private string lastUpdatedAt = "";
    private GameObject spawned;

    void Start() { StartCoroutine(PollLoop()); }

    IEnumerator PollLoop()
    {
        while (true)
        {
            using (UnityWebRequest req = UnityWebRequest.Get(apiBaseUrl.TrimEnd('/') + "/api/selected"))
            {
                req.timeout = 8;
                yield return req.SendWebRequest();
                if (req.result == UnityWebRequest.Result.Success)
                {
                    SelectedPayload payload = null;
                    try { payload = JsonUtility.FromJson<SelectedPayload>(req.downloadHandler.text); } catch {}
                    if (payload != null && payload.product != null &&
                        !String.IsNullOrEmpty(payload.updated_at) && payload.updated_at != lastUpdatedAt)
                    {
                        lastUpdatedAt = payload.updated_at;
                        SpawnProduct(payload.product);
                    }
                }
            }
            yield return new WaitForSeconds(pollSeconds);
        }
    }

    void SpawnProduct(ProductPayload product)
    {
        if (String.IsNullOrEmpty(product.model_key))
        {
            Debug.LogWarning("Selected product has no model_key. Add a 3D model/prefab and map it in the Inspector.");
            return;
        }
        ProductPrefab mapping = productPrefabs.Find(x => x.modelKey == product.model_key);
        if (mapping == null || mapping.prefab == null)
        {
            Debug.LogWarning("No prefab mapped for model_key: " + product.model_key);
            return;
        }
        if (spawned != null) Destroy(spawned);
        Vector3 pos = placementAnchor != null ? placementAnchor.position : Camera.main.transform.position + Camera.main.transform.forward * 1.5f;
        Quaternion rot = placementAnchor != null ? placementAnchor.rotation : Quaternion.identity;
        spawned = Instantiate(mapping.prefab, pos, rot);
        Debug.Log("Spawned AR product: " + product.title);
    }
}
