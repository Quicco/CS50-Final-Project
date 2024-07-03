function handleAction(action) {
  let message = "";

  switch (action) {
    case "deleteStudent":
      message = "Are you sure you want to delete this student?";
      return confirm(message);
      
    case "archiveClass":
      message = "Are you sure you want to archive this class?";
      return confirm(message);

      case "deleteClass":
      message = "Are you sure you want to delete this class?";
      return confirm(message);
      
    default:
      return; 
  }
}

function search() {
  let input = document.querySelector('.search-input');

  input.addEventListener('input', async function() {
    let response = await fetch('/search?q=' + input.value);

    if (response.ok) {
      let archivedClasses = await response.json();
      
      let tbody = document.querySelector("tbody");
      tbody.innerHTML = "";

      // For each ahived class, insert the data onto the tables
      archivedClasses.forEach(archivedClass => {
        let tableRow = document.createElement("tr");
        // Create the cells for each data
        let classTypeCell = document.createElement("td");
        classTypeCell.textContent = archivedClass.class_type + "  #" + archivedClass.class_id;
        tableRow.appendChild(classTypeCell);

        let courseCell = document.createElement("td");
        courseCell.textContent = archivedClass.course;
        tableRow.appendChild(courseCell);

        let timeSlotCell = document.createElement("td");
        timeSlotCell.textContent = archivedClass.time_slot;
        tableRow.appendChild(timeSlotCell);

        let locationCell = document.createElement("td");
        locationCell.textContent = archivedClass.location;
        tableRow.appendChild(locationCell);
        
        let yearCell = document.createElement("td");
        yearCell.textContent = archivedClass.year;
        tableRow.appendChild(yearCell);

        tbody.appendChild(tableRow);
      })
    }  else {
      console.error('Search request failed:', response.statusText);
    }
  })
}