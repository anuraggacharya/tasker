$(document).ready(function () {
  // Initialize dialog
  const dialog = document.querySelector("#task-dialog");
  if (!dialog.showModal) {
    dialogPolyfill.registerDialog(dialog);
  }

  // Load tasks on page load
  loadTasks();

  // Add Task Button Click
  $("#add-task-btn").click(function () {
    $("#task-form")[0].reset();
    $("#task-id").val("");
    dialog.showModal();
  });

  // Cancel Button Click
  $("#cancel-btn").click(function () {
    dialog.close();
  });

  // Save Button Click
  $("#save-btn").click(function () {
    saveTask();
  });
  function initializeDragAndDrop() {
    // Make task cards draggable
    $(".task-card")
      .attr("draggable", "true")
      .on("dragstart", function (e) {
        e.originalEvent.dataTransfer.setData("text/plain", $(this).data("id"));
        $(this).addClass("dragging");
      })
      .on("dragend", function () {
        $(this).removeClass("dragging");
      });

    // Make columns droppable
    $(".task-list")
      .on("dragover", function (e) {
        e.preventDefault();
        $(this).addClass("drag-over");
      })
      .on("dragleave", function () {
        $(this).removeClass("drag-over");
      })
      .on("drop", function (e) {
        e.preventDefault();
        $(this).removeClass("drag-over");

        const taskId = e.originalEvent.dataTransfer.getData("text/plain");
        const newStatus = $(this).data("status");

        updateTaskStatus(taskId, newStatus);
      });
  }
  // Load tasks function
  function loadTasks() {
    const token = localStorage.getItem("jwt_token"); // Replace with your actual token
    $.ajax({
      url: "/api/tasks",
      method: "GET",
      headers: {
        Authorization: "Bearer " + token,
      },
      success: function (tasks) {
        //console.log("Raw tasks data:", tasks); // Verify data structure

        // Clear all columns
        $("#todo-list, #inprogress-list, #done-list").empty();

        // Process each task
        tasks.forEach((task) => {
          //console.log("Processing task:", task); // Debug individual task

          // Determine which column this task belongs to
          const columnMap = {
            "To Do": "#todo-list",
            "In Progress": "#inprogress-list",
            Done: "#done-list",
          };

          const targetColumn = columnMap[task.status];

          if (targetColumn) {
            const cardHtml = createTaskCard(task);
            $(targetColumn).append(cardHtml);
          } else {
            console.warn("Task with unknown status:", task);
          }
        });

        // Initialize MDL components and drag/drop
        componentHandler.upgradeDom();
        initializeDragAndDrop();
      },
      error: function (error) {
        console.error("Error loading tasks:", error);
      },
    });
  }

  // Create task card HTML
  function createTaskCard(task) {
    // Safely handle all possible null/undefined values
    const safeTask = {
      id: task.id || "",
      title: task.title || "Untitled Task",
      description: task.description || "No description provided",
      created_date: task.created_date || "Unknown creation date",
      due_date: task.due_date
        ? new Date(task.due_date).toLocaleDateString()
        : "No due date",
      assignee: task.assignee || "Unassigned",
      status: task.status || "To Do",
      close_date: task.close_date
        ? new Date(task.close_date).toLocaleDateString()
        : "No close date",
      start_date: task.start_date
        ? new Date(task.start_date).toLocaleDateString()
        : "No start date",
      task_class: task.task_class || "No class",
      uc_name: task.uc_name || "No UC assigned",
    };

    return `
      <div class="task-card mdl-card mdl-shadow--2dp" data-id="${safeTask.id}" draggable="true">
          <div class="mdl-card__title">
              <h2 class="mdl-card__title-text">${safeTask.uc_name} - ${safeTask.title}</h2>
          </div>
          <div class="mdl-card__supporting-text">
              ${safeTask.description}
          </div>

          <div class="mdl-card__supporting-text">
              <strong>Created:</strong> ${safeTask.created_date}<br>
              <strong>Start date:</strong> ${safeTask.start_date}<br>
              <strong>Due date:</strong> ${safeTask.due_date}<br>
              <strong>Close date:</strong> ${safeTask.close_date}<br>
              <strong>Assignee:</strong> ${safeTask.assignee}<br>
              <strong>Task class:</strong> ${safeTask.task_class}<br>

          </div>
          <div class="mdl-card__actions mdl-card--border">
              <button class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect edit-btn"
                      data-id="${safeTask.id}">
                  Edit
              </button>
              <button class="mdl-button mdl-button--colored mdl-js-button mdl-js-ripple-effect delete-btn"
                      data-id="${safeTask.id}">
                  Delete
              </button>
          </div>
      </div>
      `;
  }
  // Save task function
  function saveTask() {
    const taskData = {
      title: $("#task-title").val(),
      description: $("#task-description").val(),
      due_date: $("#task-due-date").val(),
      assignee: $("#task-assignee").val(),
      task_start_date: $("#task-start-date").val(),
      task_close_date: $("#task-close-date").val(),
      task_class: $("#task-class").val(),
      uc_name: $("#uc-name").val(),
    };

    const taskId = $("#task-id").val();
    const url = taskId ? `/api/tasks/${taskId}` : "/api/tasks";
    const method = taskId ? "PUT" : "POST";
    const token = localStorage.getItem("jwt_token");
    $.ajax({
      url: url,
      type: method,
      contentType: "application/json",
      xhrFields: {
        withCredentials: true,
      },
      headers: {
        Authorization: "Bearer " + token,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      data: JSON.stringify(taskData),
      success: function (response) {
        dialog.close();
        loadTasks(); // Refresh the task list
      },
      error: function (error) {
        console.error("Error saving task:", error);
        alert("Failed to save task");
      },
    });
  }

  // Update task status
  function updateTaskStatus(taskId, newStatus) {
    const token = localStorage.getItem("jwt_token");

    $.ajax({
      url: `/api/tasks/${taskId}`,
      type: "PUT",
      contentType: "application/json",
      xhrFields: {
        withCredentials: true,
      },
      headers: {
        Authorization: "Bearer " + token,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      data: JSON.stringify({ status: newStatus }),
      success: loadTasks,
    });
  }

  $(document).on("click", ".edit-btn", function () {
    const taskId = $(this).data("id");
    console.log("Editing task ID:", taskId);

    const token = localStorage.getItem("jwt_token"); // Get your JWT token from storage

    // Show loading state
    $("#task-dialog .mdl-dialog__content").addClass("loading");

    $.ajax({
      url: `/api/tasks/${taskId}`,
      method: "GET",
      headers: {
        Authorization: "Bearer " + token,
      },
      success: function (task) {
        console.log("Task data received:", task);

        if (task.error) {
          alert("Error: " + task.error);
          return;
        }

        // Populate form fields
        $("#task-id").val(task.id);
        $("#task-title").val(task.title);
        $("#task-description").val(task.description);

        // Format date for input[type=date]
        const dueDate = task.due_date ? task.due_date.split(" ")[0] : "";
        $("#task-due-date").val(dueDate);
        const startDate = task.start_date ? task.start_date.split(" ")[0] : "";
        $("#task-start-date").val(startDate);
        const closeDate = task.close_date ? task.close_date.split(" ")[0] : "";
        $("#task-close-date").val(closeDate);
        $("#task-assignee").val(task.assignee);
        $("#task-class").val(task.task_class);
        $("#uc-name").val(task.uc_name);
        // Update dialog title
        $("#task-dialog .mdl-dialog__title").text("Edit Task");

        // Show dialog
        dialog.showModal();
        componentHandler.upgradeDom();
      },
      error: function (xhr, status, error) {
        console.error("Error loading task:", status, error);
        alert("Failed to load task. Please try again.");
      },
      complete: function () {
        $("#task-dialog .mdl-dialog__content").removeClass("loading");
      },
    });
  });

  // Delete button click (delegated event)
  $(document).on("click", ".delete-btn", function () {
    const taskId = $(this).data("id");

    if (confirm("Are you sure you want to delete this task?")) {
      token = localStorage.getItem("jwt_token");
      $.ajax({
        xhrFields: {
          withCredentials: true,
        },
        headers: {
          Authorization: "Bearer " + token,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        url: `/api/tasks/${taskId}`,
        type: "DELETE",
        success: loadTasks,
      });
    }
  });
});
// Call this after loading tasks or creating new ones
function setupDragAndDrop() {
  initializeDragAndDrop();
}

function loadDashboardData() {
  console.log("Loading dashboard data...");

  fetch("/api/dashboard/metrics")
    .then((response) => {
      console.log("API response status:", response.status);
      return response.json();
    })
    .then((data) => {
      console.log("Received dashboard data:", data);

      if (data.error) {
        console.error("Dashboard error:", data.error);
        return;
      }

      renderCompletionRate(data.completion_rate || { completed: 0, total: 0 });
      renderOnTimeDelivery(data.on_time_delivery || { on_time: 0, total: 0 });
      renderAvgCompletionTime(data.avg_completion_time || 0);
    })
    .catch((error) => {
      console.error("Error loading dashboard:", error);
    });
}
document.addEventListener("DOMContentLoaded", function () {
  // Initialize only when dashboard tab is clicked
  document
    .querySelector('a[href="#dashboard"]')
    ?.addEventListener("click", loadDashboardData);
});

// auth logi
