import requests

#/ Set your API key and query
api_key = "a8addab5-a514-4e47-b7ce-25708ca5f81f"  # CHANGE WITH YOUR API KEY
phoneNumber = "(907) 947-0166"

#/ API endpoint
api_url = "https://app.scrapeak.com/v1/scrapers/people_search/search"

parameters = {"api_key": api_key, "search_by":"phone", "phone": phoneNumber}

#/ Make the API request
response = requests.get(api_url, params=parameters)
response_content = response.text

print(response_content)