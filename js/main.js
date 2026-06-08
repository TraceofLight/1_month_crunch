/**
 * Portfolio interactions: connects user events to state changes and DOM rendering.
 */
const GITHUB_USER = "TraceofLight";
const API_URL = `https://api.github.com/users/${GITHUB_USER}/repos`;
const SCROLL_TOP_THRESHOLD = 300;
const HEADER_SCROLL_THRESHOLD = 60;
const OBSERVER_THRESHOLD = 0.25;

const state = {
  theme: "light",
  projects: [],
  projectStatus: "loading",
  projectError: "",
  activeLanguage: "all",
  formErrors: {
    name: "",
    email: "",
    message: "",
  },
};

const elements = {
  root: document.documentElement,
  header: document.querySelector("[data-header]"),
  menuToggle: document.querySelector("[data-menu-toggle]"),
  navMenu: document.querySelector("[data-nav-menu]"),
  navLinks: document.querySelectorAll("[data-nav-menu] a, .hero-actions a, .logo"),
  themeToggle: document.querySelector("[data-theme-toggle]"),
  themeLabel: document.querySelector("[data-theme-label]"),
  typingText: document.querySelector("[data-typing-text]"),
  scrollTop: document.querySelector("[data-scroll-top]"),
  projectGrid: document.querySelector("[data-project-grid]"),
  projectStatus: document.querySelector("[data-project-status]"),
  retryProjects: document.querySelector("[data-retry-projects]"),
  filterBar: document.querySelector("[data-filter-bar]"),
  contactForm: document.querySelector("[data-contact-form]"),
  formResult: document.querySelector("[data-form-result]"),
  observedSections: document.querySelectorAll(".section-observe"),
};

/**
 * Escapes text before inserting dynamic GitHub content with innerHTML templates.
 * @param {string} value GitHub API text value.
 * @returns {string} HTML-safe text.
 */
const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

/**
 * Reads the saved theme or falls back to the operating system preference.
 * @returns {string} Theme name.
 */
const getInitialTheme = () => {
  const savedTheme = localStorage.getItem("theme");

  if (savedTheme === "dark" || savedTheme === "light") {
    return savedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

/**
 * Applies the current theme state to the document and toggle label.
 */
const renderTheme = () => {
  elements.root.dataset.theme = state.theme;
  elements.themeLabel.textContent = state.theme === "dark" ? "Light" : "Dark";
};

/**
 * Toggles theme state and persists it in localStorage.
 */
const toggleTheme = () => {
  state.theme = state.theme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", state.theme);
  renderTheme();
};

/**
 * Opens or closes the mobile navigation menu.
 */
const toggleMenu = () => {
  const isActive = elements.navMenu.classList.toggle("active");
  elements.menuToggle.setAttribute("aria-expanded", String(isActive));
  elements.menuToggle.setAttribute("aria-label", isActive ? "메뉴 닫기" : "메뉴 열기");
};

/**
 * Closes the mobile menu after moving to a section.
 */
const closeMenu = () => {
  elements.navMenu.classList.remove("active");
  elements.menuToggle.setAttribute("aria-expanded", "false");
  elements.menuToggle.setAttribute("aria-label", "메뉴 열기");
};

/**
 * Smoothly scrolls to an in-page section.
 * @param {Event} event Click event from a navigation anchor.
 */
const handleSmoothScroll = (event) => {
  const targetId = event.currentTarget.getAttribute("href");

  if (!targetId || !targetId.startsWith("#")) {
    return;
  }

  const target = document.querySelector(targetId);

  if (!target) {
    return;
  }

  event.preventDefault();
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  closeMenu();
};

/**
 * Updates header and scroll button state based on the current scroll position.
 */
const handleScroll = () => {
  const isPastHeaderThreshold = window.scrollY >= HEADER_SCROLL_THRESHOLD;
  const isPastTopThreshold = window.scrollY >= SCROLL_TOP_THRESHOLD;

  elements.header.classList.toggle("scrolled", isPastHeaderThreshold);
  elements.scrollTop.classList.toggle("visible", isPastTopThreshold);
};

/**
 * Builds unique language filters from loaded GitHub repositories.
 * @returns {string[]} Language names.
 */
const getLanguages = () => {
  const languages = state.projects
    .map(({ language }) => language)
    .filter((language) => Boolean(language));

  return [...new Set(languages)].sort((a, b) => a.localeCompare(b));
};

/**
 * Renders filter buttons and wires each button to project state updates.
 */
const renderFilters = () => {
  const languages = getLanguages();
  const filterOptions = ["all", ...languages];

  elements.filterBar.innerHTML = filterOptions
    .map((language) => {
      const label = language === "all" ? "전체" : escapeHtml(language);
      const isActive = language === state.activeLanguage ? " active" : "";

      return `<button class="filter-button${isActive}" type="button" data-filter="${escapeHtml(
        language
      )}">${label}</button>`;
    })
    .join("");

  elements.filterBar.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeLanguage = button.dataset.filter;
      renderProjects();
    });
  });
};

/**
 * Renders the Projects section for loading, success, error, and empty states.
 */
const renderProjects = () => {
  elements.retryProjects.classList.toggle("hidden", state.projectStatus !== "error");
  elements.projectGrid.innerHTML = "";

  if (state.projectStatus === "loading") {
    elements.projectStatus.classList.remove("hidden");
    elements.projectStatus.innerHTML =
      '<span class="spinner" aria-hidden="true"></span><span>로딩 중...</span>';
    return;
  }

  if (state.projectStatus === "error") {
    elements.projectStatus.classList.remove("hidden");
    elements.projectStatus.textContent =
      state.projectError || "프로젝트를 불러올 수 없습니다.";
    return;
  }

  renderFilters();

  const filteredProjects =
    state.activeLanguage === "all"
      ? state.projects
      : state.projects.filter(({ language }) => language === state.activeLanguage);

  if (filteredProjects.length === 0) {
    elements.projectStatus.classList.remove("hidden");
    elements.projectStatus.textContent = "표시할 프로젝트가 없습니다.";
    return;
  }

  elements.projectStatus.classList.add("hidden");
  elements.projectGrid.innerHTML = filteredProjects
    .map(
      ({
        name,
        description,
        html_url: htmlUrl,
        language,
        stargazers_count: stars,
        updated_at: updatedAt,
      }) => {
        const updatedDate = new Date(updatedAt).toLocaleDateString("ko-KR");
        const projectDescription = description || "저장소 설명이 아직 없습니다.";

        return `
          <article class="project-card">
            <h3><a href="${escapeHtml(htmlUrl)}">${escapeHtml(name)}</a></h3>
            <p>${escapeHtml(projectDescription)}</p>
            <div class="project-meta">
              <span>${escapeHtml(language || "기타")}</span>
              <span>★ ${stars}</span>
              <span>${updatedDate}</span>
            </div>
          </article>
        `;
      }
    )
    .join("");
};

/**
 * Loads public repositories from GitHub and updates Projects rendering state.
 */
const loadProjects = async () => {
  state.projectStatus = "loading";
  state.projectError = "";
  state.activeLanguage = "all";
  renderProjects();

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error(response.status === 403 ? "GitHub API 호출 한도에 도달했습니다." : "");
    }

    const repos = await response.json();
    state.projects = repos
      .filter(({ fork }) => !fork)
      .sort((a, b) => b.stargazers_count - a.stargazers_count || a.name.localeCompare(b.name));
    state.projectStatus = "success";
  } catch (error) {
    state.projects = [];
    state.projectStatus = "error";
    state.projectError = error.message || "프로젝트를 불러올 수 없습니다.";
  }

  renderProjects();
};

/**
 * Returns validation errors for the contact form.
 * @param {FormData} formData Current form data.
 * @returns {Record<string, string>} Error messages keyed by field name.
 */
const validateForm = (formData) => {
  const { name, email, message } = Object.fromEntries(formData.entries());
  const errors = {
    name: "",
    email: "",
    message: "",
  };
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!name.trim()) {
    errors.name = "이름을 입력해 주세요.";
  }

  if (!email.trim()) {
    errors.email = "이메일을 입력해 주세요.";
  } else if (!emailPattern.test(email.trim())) {
    errors.email = "이메일 형식이 올바르지 않습니다.";
  }

  if (!message.trim()) {
    errors.message = "메시지를 입력해 주세요.";
  }

  return errors;
};

/**
 * Renders form validation errors near each input field.
 */
const renderFormErrors = () => {
  Object.entries(state.formErrors).forEach(([field, message]) => {
    const errorElement = document.querySelector(`[data-error-for="${field}"]`);
    const inputElement = document.querySelector(`[data-field="${field}"]`);

    errorElement.textContent = message;
    inputElement.setAttribute("aria-invalid", String(Boolean(message)));
    inputElement.setAttribute("aria-describedby", `${field}-error`);
  });
};

/**
 * Validates input changes and updates field-level error state.
 * @param {Event} event Input event from a form control.
 */
const handleInput = (event) => {
  const field = event.target.dataset.field;

  if (!field) {
    return;
  }

  const formData = new FormData(elements.contactForm);
  state.formErrors = validateForm(formData);
  state.formErrors[field] = state.formErrors[field];
  elements.formResult.textContent = "";
  renderFormErrors();
};

/**
 * Handles form submission without sending a network request.
 * @param {Event} event Submit event from the contact form.
 */
const handleSubmit = (event) => {
  event.preventDefault();

  const formData = new FormData(elements.contactForm);
  state.formErrors = validateForm(formData);
  renderFormErrors();

  const hasErrors = Object.values(state.formErrors).some(Boolean);

  if (hasErrors) {
    elements.formResult.textContent = "";
    return;
  }

  elements.contactForm.reset();
  elements.formResult.textContent = "문의가 접수되었습니다.";
};

/**
 * Starts a small typing effect in the hero headline.
 */
const startTyping = () => {
  const text = "TraceofLight입니다.";
  let index = 0;

  const typeNext = () => {
    elements.typingText.textContent = text.slice(0, index);
    index += 1;

    if (index <= text.length) {
      window.setTimeout(typeNext, 85);
    }
  };

  typeNext();
};

/**
 * Reveals sections when at least 25% of the section is visible.
 */
const observeSections = () => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
        }
      });
    },
    { threshold: OBSERVER_THRESHOLD }
  );

  elements.observedSections.forEach((section) => observer.observe(section));
};

/**
 * Registers event listeners and starts initial rendering.
 */
const init = () => {
  state.theme = getInitialTheme();
  renderTheme();
  handleScroll();
  startTyping();
  observeSections();
  loadProjects();

  elements.menuToggle.addEventListener("click", toggleMenu);
  elements.themeToggle.addEventListener("click", toggleTheme);
  elements.navLinks.forEach((link) => link.addEventListener("click", handleSmoothScroll));
  elements.scrollTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  elements.retryProjects.addEventListener("click", loadProjects);
  elements.contactForm.addEventListener("submit", handleSubmit);
  elements.contactForm.querySelectorAll("[data-field]").forEach((field) => {
    field.addEventListener("input", handleInput);
  });
  window.addEventListener("scroll", handleScroll);
};

init();
