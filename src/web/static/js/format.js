const TRACING_LABELS = { done: "Готово", run: "В процессе", error: "Ошибка" };
const TIME_OF_DAY_LABELS = { morning: "Утро", day: "День", evening: "Вечер", night: "Ночь" };

function formatDuration(seconds) {
  if (seconds == null) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}ч ${m}м ${s}с`;
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}
