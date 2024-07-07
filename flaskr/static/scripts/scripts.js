function handleAction(action) {
  let message = '';

  switch (action) {
    case 'deleteStudent':
      message = 'Are you sure you want to delete this student?';
      return confirm(message);

    case 'archiveClass':
      message = 'Are you sure you want to archive this class?';
      return confirm(message);

    case 'deleteClass':
      message = 'Are you sure you want to delete this class?';
      return confirm(message);

    default:
      return;
  }
}

function search() {
  const input = document.querySelector('.search-input');
  const tbody = document.querySelector('tbody');
  const templateRow = document.querySelector('#template-row');

  input.addEventListener('input', async function () {
    const response = await fetch('/search?q=' + input.value);

    if (response.ok) {
      const archivedClasses = await response.json();
      tbody.innerHTML = '';

      // Clone the template row and populate it with data
      archivedClasses.forEach((archivedClass) => {
        const tableRow = templateRow.content.cloneNode(true);

        tableRow.querySelector('.class-type').textContent =
          archivedClass.class_type + ' #' + archivedClass.class_id;

        tableRow.querySelector('.course').textContent = archivedClass.course;

        tableRow.querySelector('.time-slot').textContent =
          archivedClass.time_slot;

        tableRow.querySelector('.location').textContent =
          archivedClass.location;

        tableRow.querySelector('.year').textContent = archivedClass.year;

        // Update form actions dynamically
        const selectForm = tableRow.querySelector('.select-form');
        selectForm.action = `{{ url_for('actions.select_archived_class') }}`;
        selectForm.querySelector('input[name="class_id"]').value =
          archivedClass.class_id;

        const unarchiveForm = tableRow.querySelector('.unarchive-form');
        unarchiveForm.action = `{{ url_for('actions.unarchive') }}`;
        unarchiveForm.querySelector('input[name="class_id"]').value =
          archivedClass.class_id;

        tbody.appendChild(tableRow);
      });
    } else {
      console.error('Search request failed:', response.statusText);
    }
  });
}

search(); // Initialize search functionality
