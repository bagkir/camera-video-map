document.addEventListener("DOMContentLoaded", async () => {
  const map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "&copy; OpenStreetMap contributors",
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    },
    center: [37.62, 55.75], // Москва
    zoom: 9,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  map.on("load", async () => {
    const res = await fetch("/api/v1/cameras/geojson");
    if (!res.ok) {
      console.error("Не удалось загрузить камеры:", res.status);
      return;
    }
    const geojson = await res.json();

    map.addSource("cameras", {
      type: "geojson",
      data: geojson,
      cluster: true,
      clusterRadius: 50,
    });

    // Кластеры — кружок с цифрой (как на макете)
    map.addLayer({
      id: "cluster-circles",
      type: "circle",
      source: "cameras",
      filter: ["has", "point_count"],
      paint: {
        "circle-radius": 16,
        "circle-color": "#7c3aed",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });

    map.addLayer({
      id: "cluster-count",
      type: "symbol",
      source: "cameras",
      filter: ["has", "point_count"],
      layout: {
        "text-field": ["get", "point_count_abbreviated"],
        "text-size": 12,
      },
      paint: { "text-color": "#ffffff" },
    });

    // Одиночные камеры — маленький/большой кружок по has_video
    map.addLayer({
      id: "camera-circles",
      type: "circle",
      source: "cameras",
      filter: ["!", ["has", "point_count"]],
      paint: {
        // ТЗ 1.2.1: "если загрузки раньше не было — кружок маленький, если была — большой"
        "circle-radius": ["case", ["get", "has_video"], 9, 5],
        "circle-color": ["case", ["get", "has_video"], "#2e7d32", "#9e9e9e"],
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
      },
    });

    // Клик по кластеру — приблизить
    map.on("click", "cluster-circles", async (e) => {
      const clusterId = e.features[0].properties.cluster_id;
      const source = map.getSource("cameras");
      const zoom = await source.getClusterExpansionZoom(clusterId);
      map.easeTo({ center: e.features[0].geometry.coordinates, zoom });
    });

    // Клик по одиночной камере — попап
    map.on("click", "camera-circles", (e) => {
      const { id, camera_name } = e.features[0].properties;
      new maplibregl.Popup()
        .setLngLat(e.features[0].geometry.coordinates)
        .setHTML(`<strong>${camera_name}</strong><br><a href="/cameras/${id}">Перейти к локации</a>`)
        .addTo(map);
    });

    for (const layerId of ["cluster-circles", "camera-circles"]) {
      map.on("mouseenter", layerId, () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", layerId, () => (map.getCanvas().style.cursor = ""));
    }
  });
});
