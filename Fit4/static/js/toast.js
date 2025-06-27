;(function() {
  const toastElement = document.getElementById("toast-t")
  const toastBody = document.getElementById("toast-body-t")
  const toast = new bootstrap.Toast(toastElement, { delay: 2000 })

  htmx.on("showMessage", (e) => {
    toastBody.innerText = e.detail.value
    toast.show()
  })
})()
