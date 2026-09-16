document.addEventListener("DOMContentLoaded", async () => {
  const cameraId = window.CAMERA_ID;

  const camera = await fetchJSON(`/api/v1/cameras/${cameraId}`);
  document.getElementById("camera-name").textContent = camera.camera_name;
  document.getElementById("camera-place").textContent = camera.camera_place || "";

  setupImportForm(cameraId);
  setupTabs(cameraId);
  setupVideoFilters(cameraId);
  setupAnalysisFilters(cameraId);

  await loadVideos(cameraId);
});


function setupTabs(cameraId) {
  const videoTab = document.getElementById("tab-videos");
  const analysisTab = document.getElementById("tab-analyses");
  const videoPanel = document.getElementById("panel-videos");
  const analysisPanel = document.getElementById("panel-analyses");

  videoTab.addEventListener("click", () => {
    videoTab.classList.add("active");
    analysisTab.classList.remove("active");
    videoPanel.hidden = false;
    analysisPanel.hidden = true;
  });
  analysisTab.addEventListener("click", () => {
    analysisTab.classList.add("active");
    videoTab.classList.remove("active");
    analysisPanel.hidden = false;
    videoPanel.hidden = true;
    loadAnalyses(cameraId);
  });
}

async function uploadOneVideo(cameraId, file) {
  const formData = new FormData();
  formData.append("camera_id", cameraId);
  formData.append("file", file);

  const res = await fetch("/api/v1/videos", { method: "POST", body: formData });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Не удалось загрузить видео");
  }
}

function setupImportForm(cameraId) {
  const form = document.getElementById("import-form");
  const fileInput = document.getElementById("import-file");
  const submitBtn = form.querySelector("button[type=submit]");
  const errorBox = document.getElementById("import-error");

  fileInput.addEventListener("change", () => {
    submitBtn.disabled = !fileInput.files.length;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.textContent = "";
    submitBtn.disabled = true;

    // ТЗ 1.3.4: несколько выбранных видео обрабатываются по одному, строго
    // по очереди — не параллельно.
    const files = Array.from(fileInput.files);
    const failed = [];

    for (let i = 0; i < files.length; i++) {
      submitBtn.textContent =
        files.length > 1 ? `Загрузка ${i + 1}/${files.length}...` : "Загрузка...";
      try {
        await uploadOneVideo(cameraId, files[i]);
      } catch (err) {
        failed.push(`${files[i].name}: ${err.message}`);
      }
    }

    if (failed.length) {
      errorBox.textContent = failed.join("; ");
    } else {
      form.reset();
    }

    await loadVideos(cameraId);
    submitBtn.disabled = !fileInput.files.length;
    submitBtn.textContent = "Импорт";
  });
}

function setupVideoFilters(cameraId) {
  document.getElementById("video-filters").addEventListener("submit", (e) => {
    e.preventDefault();
    loadVideos(cameraId);
  });
}

function setupAnalysisFilters(cameraId) {
  document.getElementById("analysis-filters").addEventListener("submit", (e) => {
    e.preventDefault();
    loadAnalyses(cameraId);
  });
}


async function loadVideos(cameraId) {
  const form = document.getElementById("video-filters");
  const params = new URLSearchParams({ camera_id: cameraId });

  if (form.uploaded_from.value) params.set("uploaded_from", form.uploaded_from.value);
  if (form.uploaded_to.value) params.set("uploaded_to", form.uploaded_to.value);
  if (form.duration_from.value) params.set("duration_from", form.duration_from.value);
  if (form.duration_to.value) params.set("duration_to", form.duration_to.value);
  if (form.time_of_day.value) params.set("time_of_day", form.time_of_day.value);
  if (form.tracing_status.value) params.set("tracing_status", form.tracing_status.value);

  const videos = await fetchJSON(`/api/v1/videos?${params}`);
  const tbody = document.getElementById("videos-tbody");
  tbody.innerHTML = "";

  if (!videos.length) {
    tbody.innerHTML = `<tr><td colspan="8">Видео не найдены</td></tr>`;
    return;
  }

  for (const v of videos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${v.name}</td>
      <td>${formatDuration(v.duration_seconds)}</td>
      <td>${v.resolution_width ?? "—"}x${v.resolution_height ?? "—"}</td>
      <td>${v.fps ?? "—"}</td>
      <td>${TIME_OF_DAY_LABELS[v.time_of_day] ?? "—"}</td>
      <td><span class="badge badge-${v.tracing_status}">${TRACING_LABELS[v.tracing_status]}</span></td>
      <td>${v.author_name}</td>
      <td>${v.counter}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadAnalyses(cameraId) {
  const form = document.getElementById("analysis-filters");
  const params = new URLSearchParams();
  if (form.analysis_type.value) params.set("analysis_type", form.analysis_type.value);
  if (form.status.value) params.set("status", form.status.value);

  const analyses = await fetchJSON(`/api/v1/cameras/${cameraId}/analyses?${params}`);
  const tbody = document.getElementById("analyses-tbody");
  tbody.innerHTML = "";

  if (!analyses.length) {
    tbody.innerHTML = `<tr><td colspan="5">Анализы не найдены</td></tr>`;
    return;
  }

  for (const a of analyses) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${a.video_name}</td>
      <td>${a.analysis_type === "traffic" ? "Траффик" : "Скорости"}</td>
      <td><span class="badge badge-${a.status}">${TRACING_LABELS[a.status]}</span></td>
      <td>${JSON.stringify(a.result ?? {})}</td>
      <td>${new Date(a.created_at).toLocaleString("ru-RU")}</td>
    `;
    tbody.appendChild(tr);
  }
}
