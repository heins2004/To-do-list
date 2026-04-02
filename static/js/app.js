(function () {
    const state = {
        payload: window.__DASHBOARD_PAYLOAD__ || null,
        csrfToken: document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
    };

    if (!state.payload) {
        return;
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

    function refreshUI(payload) {
        state.payload = payload;
        document.querySelector("#task-list-panel").innerHTML = payload.partials.task_list;
        document.querySelector("#habit-list-panel").innerHTML = payload.partials.habit_list;
        document.querySelector("#calendar-panel").innerHTML = payload.partials.calendar;
        document.querySelector("#selected-day-panel").innerHTML = payload.partials.selected_day;
        document.querySelector("#achievement-panel").innerHTML = payload.partials.achievements;
        document.querySelector("#stats-panel").innerHTML = payload.partials.stats;
        document.querySelector("#alert-count").textContent = payload.meta.overdue_count;
        const selectedTag = document.querySelector("#selected-date-tag");
        if (selectedTag) {
            selectedTag.textContent = payload.meta.selected_date;
        }
    }

    async function request(url, options) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok || data.ok === false) {
            throw new Error(data.message || "Request failed");
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
        const dateField = form.querySelector('input[type="date"]');
        if (dateField) {
            dateField.value = state.payload.meta.today;
        }
        showToast(result.message || "Updated.");
    }

    async function refreshDate(dateValue) {
        const result = await request(`/api/dashboard/?date=${dateValue}`, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        refreshUI(result.payload);
    }

    document.querySelector("#task-form")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await submitForm(event.currentTarget);
        } catch (error) {
            showToast(error.message);
        }
    });

    document.querySelector("#habit-form")?.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await submitForm(event.currentTarget);
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
        const selectedDate = state.payload.meta.selected_date;

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
                showToast(result.completed ? "Task completed." : "Task reopened.");
            } else if (action === "delete-task") {
                const result = await request(`/tasks/${id}/delete/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                refreshUI(result.payload);
                showToast(result.message);
            } else if (action === "toggle-habit") {
                const result = await request(`/habits/${id}/toggle/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ date: selectedDate }),
                });
                refreshUI(result.payload);
                showToast(result.completed ? "Habit marked complete." : "Habit mark removed.");
            } else if (action === "delete-habit") {
                const result = await request(`/habits/${id}/delete/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": state.csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                refreshUI(result.payload);
                showToast(result.message);
            } else if (action === "select-date") {
                await refreshDate(trigger.dataset.date);
            }
        } catch (error) {
            showToast(error.message);
        }
    });
})();
