// Might delete this, as it doesn't fullfill exactly what I need
function goBack() {
  window.history.back();
}

// Prompt the user whether or not they want to delete a student
function confirmDeletion() {
  const message = "Are you sure you want to delete this student?"
  return confirm(message);
}

// Prompt the user whether or not they want to archive a class
function confirmArchive() {
  const message = "Are you sure you want to archive this class?"
  return confirm(message);
}