// Might delete this, as it doesn't fullfill exactly what I need
function goBack() {
  window.history.back();
}

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
  let input = document.querySelector('input');

  input.addEventListener('input', async function() {
    let response = await fetch('/search?q=' + input.value);
    let archivedClasses = response.text();
    
  })
}