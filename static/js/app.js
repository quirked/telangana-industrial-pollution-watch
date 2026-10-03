const imageInput = document.querySelector('#image');
const preview = document.querySelector('#image-preview');

if (imageInput && preview) {
  imageInput.addEventListener('change', () => {
    const file = imageInput.files?.[0];
    if (!file) {
      preview.hidden = true;
      return;
    }
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
  });
}

document.querySelectorAll('.flash').forEach((message) => {
  window.setTimeout(() => message.remove(), 5500);
});
