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
    $.get("/api/tasks", function (tasks) {
      console.log("Raw tasks data:", tasks); // Verify data structure

      // Clear all columns
      $("#todo-list, #inprogress-list, #done-list").empty();

      // Process each task
      tasks.forEach((task) => {
        console.log("Processing task:", task); // Debug individual task

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
      //setupDragAndDrop();
      // Initialize Material Design Lite components for new elements
      componentHandler.upgradeDom();
      initializeDragAndDrop();
    }).fail(function (error) {
      console.error("Error loading tasks:", error);
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
    };

    return `
      <div class="task-card mdl-card mdl-shadow--2dp" data-id="${safeTask.id}" draggable="true">
          <div class="mdl-card__title">
              <h2 class="mdl-card__title-text">${safeTask.title}</h2>
          </div>
          <div class="mdl-card__supporting-text">
              ${safeTask.description}
          </div>
          <div class="mdl-card__supporting-text">
              <strong>Created:</strong> ${safeTask.created_date}<br>
              <strong>Due:</strong> ${safeTask.due_date}<br>
              <strong>Assignee:</strong> ${safeTask.assignee}
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
    };

    const taskId = $("#task-id").val();
    const url = taskId ? `/api/tasks/${taskId}` : "/api/tasks";
    const method = taskId ? "PUT" : "POST";

    $.ajax({
      url: url,
      type: method,
      contentType: "application/json",
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
    $.ajax({
      url: `/api/tasks/${taskId}`,
      type: "PUT",
      contentType: "application/json",
      data: JSON.stringify({ status: newStatus }),
      success: loadTasks,
    });
  }

  $(document).on("click", ".edit-btn", function () {
    const taskId = $(this).data("id");
    console.log("Editing task ID:", taskId);

    // Show loading state
    $("#task-dialog .mdl-dialog__content").addClass("loading");

    $.get(`/api/tasks/${taskId}`)
      .done(function (task) {
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

        $("#task-assignee").val(task.assignee);

        // Update dialog title
        $("#task-dialog .mdl-dialog__title").text("Edit Task");

        // Show dialog
        dialog.showModal();
      })
      .fail(function (xhr, status, error) {
        console.error("Error loading task:", status, error);
        alert("Failed to load task. Please try again.");
      })
      .always(function () {
        $("#task-dialog .mdl-dialog__content").removeClass("loading");
      });
  });

  // Delete button click (delegated event)
  $(document).on("click", ".delete-btn", function () {
    const taskId = $(this).data("id");

    if (confirm("Are you sure you want to delete this task?")) {
      $.ajax({
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
