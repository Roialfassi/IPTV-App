import requests


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def get_iptv_playlist(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the IPTV playlist: {e}")
        return None


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    iptv_url = "Your link here"
    # response = requests.get(url)
    playlist = get_iptv_playlist(iptv_url)
    if playlist:
        with open("request-answer.txt", "w", encoding="utf-8") as file:
            file.write(playlist)
