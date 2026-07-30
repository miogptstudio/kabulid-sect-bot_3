(function () {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try { tg.setHeaderColor("secondary"); } catch (e) {}
  }

  const user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
  const userId = user ? user.id : null;

  // در توسعه محلی بدون تلگرام
  const API_BASE = "";

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "ranking") loadRanking();
      if (btn.dataset.tab === "sects") loadSects();
      if (btn.dataset.tab === "profile") loadProfile();
    });
  });

  async function api(path) {
    const url = API_BASE + path + (userId ? (path.includes("?") ? "&" : "?") + "tg_id=" + userId : "");
    const res = await fetch(url);
    if (!res.ok) throw new Error("خطا در ارتباط با سرور");
    return res.json();
  }

  async function loadProfile() {
    const el = document.getElementById("profile-content");
    if (!userId) {
      el.innerHTML = "<p class='error'>لطفاً مینی‌اپ را از داخل تلگرام باز کنید.</p>";
      return;
    }
    try {
      const data = await api("/api/profile");
      if (data.error) {
        el.innerHTML = "<p class='error'>" + data.error + "</p><p class='hint'>اول در ربات /start بزن.</p>";
        return;
      }
      el.innerHTML =
        "<h2>" + escapeHtml(data.full_name) + "</h2>" +
        row("رتبه", data.rank) +
        row("نقش", data.role) +
        row("سطح", data.level) +
        row("XP", data.xp) +
        row("جنسیت", data.gender || "—") +
        row("برد / باخت", data.wins + " / " + data.losses) +
        (data.cultivation
          ? row("تذهیب", data.cultivation.realm + " — سطح " + data.cultivation.stage)
          : "") +
        (data.sect ? row("فرقه", data.sect) : row("فرقه", "دوره‌گرد"));
    } catch (e) {
      el.innerHTML = "<p class='error'>" + e.message + "</p>";
    }
  }

  async function loadRanking() {
    const el = document.getElementById("ranking-content");
    try {
      const data = await api("/api/ranking");
      if (!data.top || !data.top.length) {
        el.innerHTML = "<p class='muted'>هنوز کسی نیست.</p>";
        return;
      }
      const medals = ["🥇", "🥈", "🥉"];
      el.innerHTML =
        "<h2>۳ نفر برتر</h2>" +
        data.top
          .map(
            (u, i) =>
              "<div class='rank-item'><span class='medal'>" +
              (medals[i] || i + 1) +
              "</span><div><strong>" +
              escapeHtml(u.full_name) +
              "</strong><div class='muted'>" +
              escapeHtml(u.rank) +
              " · Lv." +
              u.level +
              " · XP " +
              u.xp +
              "</div></div></div>"
          )
          .join("");
    } catch (e) {
      el.innerHTML = "<p class='error'>" + e.message + "</p>";
    }
  }

  async function loadSects() {
    const el = document.getElementById("sects-content");
    try {
      const data = await api("/api/sects");
      if (!data.sects || !data.sects.length) {
        el.innerHTML = "<p class='muted'>فرقه‌ای ثبت نشده. در ربات /createsect</p>";
        return;
      }
      el.innerHTML =
        "<h2>فرقه‌ها</h2>" +
        data.sects
          .map(
            (s) =>
              "<div class='row'><span>" +
              escapeHtml(s.name) +
              " <span class='muted'>(" +
              escapeHtml(s.sect_type) +
              ")</span></span><span class='muted'>" +
              s.member_count +
              " عضو</span></div>"
          )
          .join("");
    } catch (e) {
      el.innerHTML = "<p class='error'>" + e.message + "</p>";
    }
  }

  function row(label, value) {
    return (
      "<div class='row'><span class='muted'>" +
      label +
      "</span><span>" +
      escapeHtml(String(value)) +
      "</span></div>"
    );
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  loadProfile();
})();
