

async function deleteMenu(){
    const id = $(this).data('id')
    console.log(id)
    await axios.delete(`/api/menu/${id}`)
    $(this).parent().remove()
}

$('.menu_delete_button').click(deleteMenu)

async function addMenuItem(e){
    e.preventDefault();
    let menu_id = $(this).data('id')
    let item_count = $('.card').length
    let item_id = item_count + 1

    let menu_item_name =  $('#menu_item_name').val();
    let menu_description = $('#menu_description').val();
    let menu_price = $('#menu_price').val();
    let forwardSlash = '/'
    const menu_item = await axios.post(`/new_menu_items/${menu_id}`, {menu_item_name, menu_description, menu_price})
    
    $('#menu_item_name').val('');
    $('#menu_description').val('');
    $('#menu_price').val('');
    $('#menu_list').append(
        `<div class = 'card' style = 'width: 18rem;'>
        <a href = "/menu_item_page/${menu_id}/${menu_item_name}">
            <div class = 'card-body' data-id = ${menu_id}>
                <h5 class = 'card-title'>${menu_item_name}</h5>
                <h6 class = 'card-subtitle mb=2 text-muted'>${menu_description}</h6>
                <h6 class = 'card-subtitle mb=2 text-muted'>${menu_price}</h6>
                </a>
                <button data-id = '${menu_id}' data-name = ${menu_item_name} 
                class = 'btn btn-sm btn-outline-danger menu_item_delete'>X</button>
        </div>
        
        </div>`)
        
}


$('#add_menu_item').click(addMenuItem)

async function deleteMenuItem(e){
    e.preventDefault();
    const id = $(this).data('id');
    const name = $(this).data('name')
    console.log('clicked')
    await axios.delete(`/api/delete_menu_item/${id}/${name}`);
    $(this).parent().remove();
}

$('.menu_item_delete').click(deleteMenuItem)



async function delete_ingredient(){
    const id = $(this).data('id');
    console.log(id)
    await axios.delete(`/api/delete_product/${id}`);
    $(this).parent().remove();
}

$('.item_delete_button').click(delete_ingredient)




async function deleteEntry(){
    
    const id = $(this).data('id');
    await axios.delete(`/api/delete_entry/${id}`)
    $(this).parent().remove();
}

$('.delete_item').click(deleteEntry)




async function deletePurchase(e){
    e.preventDefault();
    const id = $(this).data('id');
    await axios.delete(`/api/delete_purchase/${id}`)
    $(`#${id}`).remove();
}

$('.delete_purchase').click(deletePurchase)



