/*
 * Copy gamer's context plain text to user's clipboard.
 * @param {HTMLElement} button
 */
function handleCopy(button) {
  const originalContent = button.innerHTML;
  navigator.clipboard.writeText(button.nextElementSibling.value);

  button.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>`;

  button.classList.add("bg-green-100", "text-green-700");

  setTimeout(() => {
    button.innerHTML = originalContent;
    button.classList.remove("bg-green-100", "text-green-700");
  }, 700);
}

/*
 * Export gamer's context as a .md file.
 * @param {HTMLElement} button
 */
function handleExport(button) {
  // Get the content from the textarea
  const content = button
    .closest("div.relative")
    .querySelector("textarea").value;

  // Create a blob with the content
  const blob = new Blob([content], { type: "text/markdown" });

  // Create a temporary link to download the file
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "gamer-context.md";

  // Trigger the download
  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}
