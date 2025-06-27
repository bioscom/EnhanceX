;(function(){
    const modal = new bootstrap.Modal(document.getElementById('modal'))

    htmx.on('htmx:afterSwap', (e) => {
      // Response targeting #dialog => show the modal
      if (e.detail.target.id === "dialog"){
        modal.show()
      }
    })

    htmx.on('htmx:beforeSwap', (e) => {
      // Empty response targeting #dialog => hide the modal
      if (e.detail.target.id === "dialog" && !e.detail.xhr.response){
        modal.hide()
        e.detail.shouldSwap = false
      }
    })

    // Remove dialog content after hiding
    htmx.on("hidden.bs.modal", () => {
      document.getElementById("dialog").innerHTML = ""
    })
})()



// function openRegisterEditModal(event, category_id) {
//     var modal = prepare_generic_modal(element);
//     var url = $(event.target).closest('a').attr('href');
//     $.ajax({
//         type: "GET",
//         url: url
//     }).done(function(data, textStatus, jqXHR) {
//         modal.find('.modal-body').html(data);
//         modal.modal('show');
//         formAjaxSubmit(modal, url, updateRegisterCalibrationChart);
//     }).fail(function(jqXHR, textStatus, errorThrown) {
//         alert(errorThrown);
//     });
// }


// $(document).ready(function openAddNewTopicModal(event, category_id) {
//   var modal = $('#modal_add_newtopic');
//   var url = $(event.target).closest('a')attr('href');
//   modal.find('.modal-body').html('').load(url, function() {
//       modal.modal('show');
//       formAjaxSubmit(popup, url);
//   });
// });


// async function getData(url, page, paginateBy) {
//     const urlWithParams = url + "?" + new URLSearchParams({
//         page: page,
//         per_page: paginateBy
//     })
//     const response = await fetch(urlWithParams);
//     return response.json();
// }

// class ScrollMorePaginator {
//     constructor(perPage) {
//         this.perPage = perPage
//         this.pageIndex = 1
//         this.lastPage = false
//         this.container = document.querySelector("#keywords")
//         this.elements = document.querySelectorAll("pre")
//         this.loader = document.querySelector("#loading")
//         this.options = {
//             root: null,
//             rootMargin: "0px",
//             threshold: 0.25
//         }
//         this.loadMore()
//         this.watchIntersection()
//     }

//     onIntersect() {
//         if (!this.lastPage) {
//             this.pageIndex++
//             this.loadMore()
//         }
//     }

//     addElement(keyword) {
//         const pre = document.createElement("pre")
//         pre.append(keyword)
//         this.container.append(pre)
//     }

//     watchIntersection() {
//         document.addEventListener("DOMContentLoaded", () => {
//             const observer = new IntersectionObserver(this.onIntersect.bind(this),
//                 this.options);
//             observer.observe(this.loader);
//         })
//     }

//     loadMore() {
//         getData(this.pageIndex, this.perPage)
//             .then(response => {
//                 response.data.forEach((el) => {
//                     this.addElement(el.name)
//                 });
//                 this.loader.style.opacity = !response.page.has_next ? "0" : "1"
//                 this.lastPage = !response.page.has_next
//             });
//     }
// }

// new ScrollMorePaginator(6);