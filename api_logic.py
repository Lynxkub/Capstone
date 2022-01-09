import requests, json




def api_call(search_term):
    params = {'api_key': 'AA64FA32C802407CB60FC92CA4A08418',
    'type': 'search',
    'search_term': search_term,
    'customer_zipcode': '53220'
    }   

    call = requests.get('https://api.bluecartapi.com/request', params)
    results = json.dumps(call.json())
    starting_point = results.find('price')
    item_info = results[starting_point : (starting_point + 15)]
    list_of_nums = []
    for el in item_info:
        try:
            list_of_nums.append(int(el))
        except ValueError:
            pass
    s = [str(i) for i in list_of_nums]
    
    if len(s) < 3:
        res = int("".join(s))
        return (search_term, (res/10))
    else:
        res = int("".join(s))
        return (search_term , (res/100))

    
