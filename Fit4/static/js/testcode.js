function dateDiffInDays(a, b) {
    const _MS_PER_DAY = 1000 * 60 * 60 * 24;
    // Discard the time and time-zone information.
    const utc1 = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
    const utc2 = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());

    return Math.floor((utc2 - utc1) / _MS_PER_DAY);
}

a=new Date('2025-10-22')
b=new Date('2024-09-22')

if(a > b)
{
    console.log("a is greater than b")
}
else{
    console.log("b is greater than a")
}

//console.log(new Date('2024-10-22') > new Date('2025-10-22'))


//const dtpicker1 = new Date('2024-10-22') //document.getElementById('dtPickerL1_Plan')
//console.log(dtpicker1)


// const dtpicker2 = document.getElementById('dtPickerL2_Plan')
// const dtpicker3 = document.getElementById('dtPickerL3_Plan')
// const dtpicker4 = document.getElementById('dtPickerL4_Plan')
// const dtpicker5 = document.getElementById('dtPickerL5_Plan')


// const toastL2 = document.getElementById('datetoast2')
// if (dtpicker2) {
//     const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastL2)
//     alert(dateDiffInDays(new Date(dtpicker2.value), new Date(dtpicker1.value)))
//     dtpicker2.addEventListener('change', () => {
//     if ((dateDiffInDays(new Date(dtpicker2.value), new Date(dtpicker1.value))) < 0) {
//     toastBootstrap.show()
//     }
// })
// }