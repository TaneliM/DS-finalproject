# Sources:
# Using Wikipedia API               https://www.jcchouinard.com/wikipedia-api/
# multiprocessing                   https://www.youtube.com/watch?v=GT10PnUFLlE
# using multiprocessing pools       https://stackoverflow.com/questions/20190668/multiprocessing-a-for-loop
# Implementing graphs in python     https://www.python.org/doc/essays/graphs/

import json
import requests
from multiprocessing import Pool
import time


# Returns a list of all of the links in
# the wikipedia article with the provided title
def get_links(titles):

    links = []
    url = 'https://en.wikipedia.org/w/api.php'

    params = {
        'action': 'query',
        'format': 'json',
        'titles': titles,
        'prop': 'links',
        'pllimit': 'max',
        'redirects':''
    }
    
    # Making a request to the Wikipedia API and parsing the response
    print(f"GET: {url} - Title: {titles}")
    response = requests.get(url = url, params = params)
    data = response.json()

    try:
        pages = data['query']['pages']

        for key, val in pages.items():
            # If a page doesn't exist
            if key == -1:
                continue
            
            # Save the links into the list
            try:
                for link in val['links']:
                    links.append(link['title'])
            except:
                continue
        
        # If a continue flag is provided, continue the query to
        # get rest of the links until no continue flag is provided
        while 'continue' in data:
            plcontinue = data['continue']['plcontinue']
            params['plcontinue'] = plcontinue

            response = requests.get(url=url, params=params)
            data = response.json()
            pages = data['query']['pages']
        
            for key, val in pages.items():
                # If a page doesn't exist
                if key == -1:
                    continue
                
                # Save the links into the list
                try:
                    for link in val['links']:
                        links.append(link['title'])
                except:
                    continue

        return links

    except:
        return []


# A modified verion of an earlier version of get_links()
# returns False/True depending on if the page exists of Wikipedia
def page_exists(title):

    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "links"
    }

    # making the request and parsing the response
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    PAGES = DATA["query"]["pages"]

    # If page doesn't exist return None
    for key, value in PAGES.items():
        if key == "-1":
            return None

        # return correctly capitalized title
        else:
            return value["title"]


# Returns one of the paths with the shortest length from start to target
def find_shortest_path(graph, start, target, path = []):

    path = path + [start]

    if start == target:
        return path

    if start not in graph:
        return None

    shortest = None

    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, target, path)

            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest

# Unused. Not supported by the current implementation of get_links()
# string the titles together with "|" in between
def combineTitles (titles):
    combinedAmount = 50 # Maximum allowed by wikipedia API is 50 for normal users
    combined = []
    temp = ""

    for i in range(len(titles)):
        if temp == "":
            temp = temp + str(titles[i])
        else:
            temp = temp + "|" + str(titles[i])

        if i % combinedAmount == combinedAmount - 1:
            combined.append(temp)
            temp = ""

    if combined == []:
        return titles

    return combined


if __name__ == "__main__":

    print("Find the shortest path between two wikipedia pages\n")

    # Asking for user input
    startTopic = input("Give starting page: ")
    targetTopic = input("Give target page: ")

    # Testing that both pages exist before continuing
    # Takes the title from the API response to ensure
    # identical capitalization for future comparisons
    startTopic = page_exists(startTopic)
    targetTopic = page_exists(targetTopic)

    if startTopic == None:
        print("Start page doesn't exist. Check spelling.")
        exit(1)

    if targetTopic == None:
        print("Target page doesn't exist. Check spelling.")
        exit(1)

    graph = {}
    graph[startTopic] = []
    currentTitles = []

    # Options. Could be made to be changed using command line arguments
    workersAmount = 20
    workSegmentSize = 500
    saveGraph = False

    start = time.perf_counter()

    while True:

        # Get a new list of all of the titles with no links from the graph
        if currentTitles == []:
            currentTitles = [key for key, links in graph.items() if links == []]

        # Query parse to support queries with multiple titles is currently not implemented in get_links()
        # titles = combineTitles(titles)

        # Create child processes
        with Pool(workersAmount) as workers:
            # Get links to titles 500 titles at a time using the child processes
            links = workers.map(get_links, currentTitles[0:workSegmentSize])

        for i in range(len(links)):
            # Get rid of titles that are already included as keys in the graph
            # This gets rid of loops in the graph so there are no paths with infinite length
            # Greatly reduces the search time for paths from infinity to a more reasonable amount
            links[i][:] = [link for link in links[i] if link not in graph]
            # Save the links into the graph as values
            graph[currentTitles[i]] = links[i]
        
        # combines a list of lists into a single list
        links = sum(links, [])

        # Save the links into the graph as new Keys
        for title in links:
            if title not in graph:
                graph[title] = []

        # Save the graph structure into a file if specified
        if saveGraph:
            f = open("Graph.txt", "w")
            f.write(json.dumps(graph, indent = 4))
            f.close()

        # Stop searhing for new links if target is already in the graph
        if targetTopic in graph:
            break

        # Remove the processed titles from the list
        if len(currentTitles) > workSegmentSize:
            for i in range(workSegmentSize):
                currentTitles.pop(0)
        else:
            currentTitles = []
    
    # Print results to user
    if not (startTopic == targetTopic):
        print(f"\nTarget is one of {len(graph)} pages found. Searching for path between {startTopic} and {targetTopic}...")
    
    path = find_shortest_path(graph, startTopic, targetTopic)
    print(f"\npath: {path}, path length: {len(path) - 1} 'click(s)'")
    
    if len(path) > 2:
        print("Other paths of equal length may exist.")

    finish = time.perf_counter()

    print(f"Search finished in {round(100 * (finish - start)) / 100} second(s)\n")
    input("Press enter to exit.")
