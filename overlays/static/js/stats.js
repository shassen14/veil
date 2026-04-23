/**
 * Shared viewer stats utilities.
 * Globals: setValue, applyViewerStats
 */

function setValue(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.classList.remove("empty");
}

function applyViewerStats(data) {
  if (data.last_follower?.display_name)
    setValue("last-follower", data.last_follower.display_name);
  if (data.last_sub?.display_name)
    setValue("last-sub", data.last_sub.display_name);
  if (data.last_raider?.display_name)
    setValue("last-raider", data.last_raider.display_name);
  if (data.last_bits?.display_name)
    setValue("last-bits", `${data.last_bits.display_name} (${data.last_bits.bits})`);
  if (data.longest_subs?.length) {
    const s = data.longest_subs[0];
    setValue("longest-sub", `${s.display_name} (${s.cumulative_months}mo)`);
  }
}
