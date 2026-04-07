(function () {
    const state = {
        payload: window.__DASHBOARD_PAYLOAD__ || null,
        csrfToken: document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
        currentScreen: "home",
        theme: document.body.classList.contains("light-mode") ? "light" : "dark",
    };

    if (!state.payload) {
        return;
    }

    const swipeTrack = document.querySelector("#swipe-track");
    const backdrops = {
        alert: document.querySelector("#alert-sheet-backdrop"),
        day: document.querySelector("#day-sheet-backdrop"),
        habitForm: document.querySelector("#habit-form-backdrop"),
        taskForm: document.querySelector("#task-form-backdrop"),
        confirm: document.querySelector("#confirm-backdrop"),
    };
    const confirmState = { action: null, id: null };
    const journalState = {
        timer: null,
        activeDate: null,
    };

    function applyTheme(theme) {
        state.theme = theme === "light" ? "light" : "dark";
        document.body.classList.toggle("light-mode", state.theme === "light");
        try {
            localStorage.setItem("domatrix-theme", state.theme);
        } catch (error) {}

        const icon = document.querySelector("#theme-icon");
        const label = document.querySelector("#theme-label");
        if (icon) {
            icon.textContent = state.theme === "light" ? "☾" : "☀";
        }
        if (label) {
            label.textContent = state.theme === "light" ? "Dark" : "Light";
        }
    }

    function showToast(message) {
        let toast = document.querySelector(".toast");
        if (!toast) {
            toast = document.createElement("div");
            toast.className = "toast";
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add("visible");
        window.clearTimeout(showToast.timer);
        showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2200);
    }

    function updateJournalStatus(text) {
        const status = document.querySelector("#journal-status");
        if (status) {
            status.textContent = text;
        }
    }

    function setScreen(screen) {
        state.currentScreen = screen;
        swipeTrack?.classList.toggle("on-tasks", screen === "tasks");
        const label = document.querySelector("#section-toggle-label");
        if (label) {
            label.textContent = screen === "tasks" ? "Habits" : "To-do list";
        }
    }

    function toggleSheet(name, visible) {
        const sheet = backdrops[name];
        if (!sheet) {
            return;
        }
        sheet.classList.toggle("is-hidden", !visible);
    }

    function closeAllSheets() {
        Object.keys(backdrops).forEach((key) => toggleSheet(key, false));
    }

    function refreshUI(payload) {
        state.payload = payload;
        document.querySelector("#home-section-panel").innerHTML = payload.partials.home_section;
        document.querySelector("#tasks-section-panel").innerHTML = payload.partials.tasks_section;
        document.querySelector("#alert-sheet-panel").innerHTML = payload.partials.alert_sheet;
        document.querySelector("#day-sheet-panel").innerHTML = payload.partials.day_sheet;
        document.querySelector("#task-nav-badge").textContent = payload.meta.task_nav_badge;

        const habitDate = document.querySelector("#habit-start-date");
        const taskDate = document.querySelector("#task-due-date");
        if (habitDate && !habitDate.dataset.lockedDate) {
            habitDate.value = payload.meta.today;
        }
        if (taskDate && !taskDate.dataset.lockedDate) {
            taskDate.value = payload.meta.selected_date || payload.meta.today;
        }
        const monthPicker = document.querySelector(".month-picker-select");
        const yearPicker = document.querySelector(".year-picker-select");
        if (monthPicker && payload.calendar?.selected_month) {
            monthPicker.value = payload.calendar.selected_month;
        }
        if (yearPicker && payload.calendar?.selected_year) {
            yearPicker.value = payload.calendar.selected_year;
        }
        bindJournalAutosave();
    }

    async function request(url, options) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok || data.ok === false) {
            const message = data.message || (data.errors ? Object.values(data.errors).flat().join(", ") : "Request failed");
            throw new Error(message);
        }
        return data;
    }

    async function submitForm(form) {
        const formData = new FormData(form);
        const result = await request(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": state.csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
        });

        refreshUI(result.payload);
        form.reset();

        const isTaskForm = form.id === "task-form";
        const dateField = form.querySelector('input[type="date"]');
        if (dateField) {
            dateField.value = isTaskForm ? result.payload.meta.selected_date : result.payload.meta.today;
            delete dateField.dataset.lockedDate;
        }
        closeAllSheets();
        showToast(result.message || "Updated.");
    }

    async function refreshDate(dateValue) {
        const result = await request(`/api/dashboard/?date=${dateValue}`, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        refreshUI(result.payload);
        toggleSheet("day", true);
    }

    async function saveJournalNote(dateValue, content) {
        updateJournalStatus("Saving...");
        const result = await request("/journal/save/", {
            method: "POST",
            headers: {
                "X-CSRFToken": state.csrfToken,
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({ date: dateValue, content }),
        });
        updateJournalStatus("Saved");
        showToast("Saved");
        return result;
    }

    function bindJournalAutosave() {
        const textarea = document.querySelector("#daily-note-textarea");
        if (!textarea || textarea.dataset.bound === "true") {
            return;
        }

        textarea.dataset.bound = "true";
        journalState.activeDate = textarea.dataset.noteDate;
        updateJournalStatus("Idle");

        textarea.addEventListener("input", () => {
            updateJournalStatus("Typing...");
            window.clearTimeout(journalState.timer);
            journalState.timer = window.setTimeout(async () => {
                try {
                    await saveJournalNote(textarea.dataset.noteDate, textarea.value);
                    const refreshed = await request(`/api/dashboard/?date=${state.payload.meta.selected_date}`, {
                        method: "GET",
                        headers: { "X-Requested-With": "XMLHttpRequest" },
                    });
                    refreshUI(refreshed.payload);
                    setScreen(state.currentScreen);
                } catch (error) {
                    updateJournalStatus("Error");
                    showToast(error.message);
                }
            }, 1500);
        });
    }

    function presetTaskDate(dateValue) {
        const input = document.querySelector("#task-due-date");
        if (!input) {
            return;
        }
        input.value = dateValue || state.payload.meta.selected_date || state.payload.meta.today;
        input.dataset.lockedDate = "true";
    }

    function toggleSection() {
        setScreen(state.currentScreen === "home" ? "tasks" : "home");
    }

    function toggleSkipForm(id, visible) {
        document.querySelectorAll(".skip-inline-form").forEach((form) => {
            form.classList.add("is-hidden");
        });
        const form = document.querySelector(`[data-skip-form="${id}"]`);
        if (form && visible) {
            form.classList.remove("is-hidden");
            form.querySelector("input")?.focus();
        }
    }

    function promptDelete(kind, id) {
        confirmState.action = kind;
        confirmState.id = id;
        document.querySelector("#confirm-title").textContent = kind === "delete-task" ? "Delete task" : "Delete habit";
        document.querySelector("#confirm-heading").textContent = kind === "delete-task" ? "Delete this task?" : "Delete this habit?";
        document.querySelector("#confirm-copy").textContent = kind === "delete-task"
            ? "The task will be removed from the calendar and alerts."
            : "The habit and its streak history will be removed.";
        toggleSheet("confirm", true);
    }

    async function performDelete() {
        if (!confirmState.action || !confirmState.id) {
            return;
        }

        const isTask = confirmState.action === "delete-task";
        const result = await request(`/${isTask ? "tasks" : "habits"}/${confirmState.id}/delete/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": state.csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        refreshUI(result.payload);
        setScreen(isTask ? "tasks" : "home");
        toggleSheet("confirm", false);
        confirmState.action = null;
        confirmState.id = null;
        showToast(result.message);
    }

    async function syncCalendarPicker() {
        const month = document.querySelector(".month-picker-select")?.value;
        const year = document.querySelector(".year-picker-select")?.value;
        if (!month || !year) {
            return;
        }
        await refreshDate(`${year}-${month}-01`);
        setScreen("tasks");
    }

    document.querySelector("#task-form")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await submitForm(event.currentTarget);
            setScreen("tasks");
        } catch (error) {
            showToast(error.message);
        }
    });

    document.querySelector("#habit-form")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await submitForm(event.currentTarget);
            setScreen("home");
        } catch (error) {
            showToast(error.message);
        }
    });

    document.addEventListener("click", async (event) => {
        const trigger = event.target.closest("[data-action]");
        if (!trigger) {
            return;
        }

        const action = trigger.dataset.action;
        const id = trigger.dataset.id;

        try {
            if (action === "toggle-task") {
                const result = await request(`/tasks/${id}/toggle/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                refreshUI(result.payload);
                setScreen("tasks");
                showToast(result.completed ? "Task completed." : "Task reopened.");
            } else if (action === "delete-task") {
                promptDelete("delete-task", id);
            } else if (action === "toggle-habit") {
                const result = await request(`/habits/${id}/toggle/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ date: state.payload.meta.today }),
                });
                refreshUI(result.payload);
                setScreen("home");
                showToast(result.completed ? "Habit marked complete." : "Habit mark removed.");
            } else if (action === "open-skip-form") {
                toggleSkipForm(id, true);
            } else if (action === "cancel-skip-form") {
                toggleSkipForm(id, false);
            } else if (action === "confirm-skip-habit") {
                const form = document.querySelector(`[data-skip-form="${id}"]`);
                const reason = form?.querySelector("input")?.value || "";
                const result = await request(`/habits/${id}/skip/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ date: state.payload.meta.today, reason }),
                });
                refreshUI(result.payload);
                setScreen("home");
                showToast(result.message);
            } else if (action === "undo-skip-habit") {
                const result = await request(`/habits/${id}/undo-skip/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ date: state.payload.meta.today }),
                });
                refreshUI(result.payload);
                setScreen("home");
                showToast(result.message);
            } else if (action === "delete-habit") {
                promptDelete("delete-habit", id);
            } else if (action === "select-date") {
                await refreshDate(trigger.dataset.date);
                setScreen("tasks");
            } else if (action === "toggle-section") {
                toggleSection();
            } else if (action === "toggle-theme") {
                applyTheme(state.theme === "light" ? "dark" : "light");
            } else if (action === "open-alert-sheet") {
                toggleSheet("alert", true);
            } else if (action === "close-alert-sheet") {
                toggleSheet("alert", false);
            } else if (action === "open-day-sheet") {
                toggleSheet("day", true);
            } else if (action === "close-day-sheet") {
                toggleSheet("day", false);
            } else if (action === "open-habit-form") {
                toggleSheet("habitForm", true);
            } else if (action === "close-habit-form") {
                toggleSheet("habitForm", false);
            } else if (action === "open-task-form") {
                presetTaskDate(trigger.dataset.date);
                toggleSheet("taskForm", true);
            } else if (action === "close-task-form") {
                toggleSheet("taskForm", false);
                const input = document.querySelector("#task-due-date");
                if (input) {
                    delete input.dataset.lockedDate;
                }
            } else if (action === "close-confirm") {
                toggleSheet("confirm", false);
                confirmState.action = null;
                confirmState.id = null;
            }
        } catch (error) {
            showToast(error.message);
        }
    });

    document.addEventListener("change", async (event) => {
        const trigger = event.target.closest("[data-action='pick-month'], [data-action='pick-year']");
        if (!trigger) {
            return;
        }
        try {
            await syncCalendarPicker();
        } catch (error) {
            showToast(error.message);
        }
    });

    document.querySelector("#confirm-submit")?.addEventListener("click", async () => {
        try {
            await performDelete();
        } catch (error) {
            showToast(error.message);
        }
    });

    Object.values(backdrops).forEach((sheet) => {
        sheet?.addEventListener("click", (event) => {
            if (event.target === sheet) {
                sheet.classList.add("is-hidden");
            }
        });
    });

    let touchStartX = 0;
    let touchDeltaX = 0;

    swipeTrack?.addEventListener("touchstart", (event) => {
        touchStartX = event.changedTouches[0].clientX;
        touchDeltaX = 0;
    });

    swipeTrack?.addEventListener("touchmove", (event) => {
        touchDeltaX = event.changedTouches[0].clientX - touchStartX;
    });

    swipeTrack?.addEventListener("touchend", () => {
        if (Math.abs(touchDeltaX) < 45) {
            return;
        }
        if (touchDeltaX < 0) {
            setScreen("tasks");
        } else {
            setScreen("home");
        }
    });

    if (state.payload.alerts?.has_items) {
        window.setTimeout(() => toggleSheet("alert", true), 450);
    }

    applyTheme(state.theme);
    bindJournalAutosave();
    setScreen("home");
})();
