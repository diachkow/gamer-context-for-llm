function handleCopy(button) {
  const originalText = button.textContent;
  navigator.clipboard.writeText(button.nextElementSibling.value);

  button.textContent = "✓ Copied";
  button.classList.add("bg-green-100", "text-green-700");

  setTimeout(() => {
    button.textContent = originalText;
    button.classList.remove("bg-green-100", "text-green-700");
  }, 1000);
}
