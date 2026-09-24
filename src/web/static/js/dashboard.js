document.addEventListener("DOMContentLoaded", async () => {
  await loadDashboard();
  await loadAllVideos();
  setupSearchFilters();
});

function renderVideoRow(v, { showAuthor, showCamera }) {
  const tr = document.createElement("tr");
  const cameraCell = showCamera
    ? `<td><a href="/cameras/${v.camera_id}">${v.camera_name}</a></td>`
    : "";
  const authorCell = showAuthor ? `<td>${v.author_name}</td>` : "";

  tr.innerHTML = `
    <td>${v.name}</td>
    ${cameraCell}
    <td>${formatDuration(v.duration_seconds)}</td>
    <td><span class="badge badge-${v.tracing_status}">${TRACING_LABELS[v.tracing_status]}</span></td>
    ${authorCell}
    <td>${new Date(v.uploaded_at).toLocaleString("ru-RU")}</td>
  `;
  return tr;
}

async function loadDashboard() {
  const tbody = document.getElementById("recent-videos-tbody");
  let data;
  try {
    data = await fetchJSON("/api/v1/users/me/dashboard");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5">Не удалось загрузить данные: ${err.message}</td></tr>`;
    return;
  }

  tbody.innerHTML = "";
  if (!data.recent_videos.length) {
    tbody.innerHTML = `<tr><td colspan="5">Вы ещё не загружали видео</td></tr>`;
    return;
  }

  for (const v of data.recent_videos) {
    tbody.appendChild(renderVideoRow(v, { showAuthor: false, showCamera: true }));
  }
}

async function loadAllVideos() {
  const form = document.getElementById("video-search-filters");
  const params = new URLSearchParams();
  if (form.name_search.value) params.set("name_search", form.name_search.value);
  if (form.author_search.value) params.set("author_search", form.author_search.value);

  const tbody = document.getElementById("all-videos-tbody");
  let videos;
  try {
    videos = await fetchJSON(`/api/v1/videos?${params}`);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6">Не удалось загрузить видео: ${err.message}</td></tr>`;
    return;
  }

  tbody.innerHTML = "";
  if (!videos.length) {
    tbody.innerHTML = `<tr><td colspan="6">Ничего не найдено</td></tr>`;
    return;
  }

  for (const v of videos) {
    tbody.appendChild(renderVideoRow(v, { showAuthor: true, showCamera: true }));
  }
}

function setupSearchFilters() {
  document.getElementById("video-search-filters").addEventListener("submit", (e) => {
    e.preventDefault();
    loadAllVideos();
  });
}
