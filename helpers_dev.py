
str_test = "https://www.linkedin.com/search/results/people/?keywords=journalist&origin=SWITCH_SEARCH_VERTICAL&page=2&sid=Mqu"

def get_second_part_url(s, max_pages):
    # gets a str like "2&sid=Mqu" as input. (the second part of a url)
    # returns "3&sid=Mqu" if max_pages >= 3 else return None because there is no url that has "3&sid=Mqu"
    
    n_str=""
    for character in s:
        if character.isdigit():
            n_str += character
        else:
            break
    n = int(n_str)
    if (n+1) <= max_pages:
        return str(n + 1) + s[len(n_str):]
    else:
        return ""


def get_next_url(old_url, max_pages):
    url_splitted = old_url.split("page=")
    second_part_url = get_second_part_url(url_splitted[1], max_pages)
    print(second_part_url)
    
    if second_part_url != "":
        return url_splitted[0] + "page=" +  second_part_url
    else:
        return None
    
def get_first_n(s):
    n_str=""
    for character in s:
        if character.isdigit():
            n_str += character
        else:
            break
    return int(n_str)
    
    
