import urllib.request
import re
import os.path
from os import path
from os import mkdir
import time

DEBUG = 0
#Set the max number of pages to download without giving a warning
pages_total_warning = 5

url_base = 'https://e926.net/posts?'
url_page = 'page='
url_tags = '&tags='

list_of_urls = []
###
#STEP 1, GET TAGS AND CREATE URL
###

print("Introduce tags: ", end ='')
tags = input()

if DEBUG:
   print("TAGS: " + str(tags))

#replace white spaces with plus signs   
tags = tags.replace(" ", "+")

if DEBUG:
   print("TAGS MOD: " + str(tags))
   
   
   
###
#STEP 2, FETCH WEBSITE AND IDENTIFY ELEMENTS
###   

#set total pages as 1 to terminate after one iteration
pages_total = 1
pages_total_set = False
page = 1
skip_setting_total_pages = False

while True:   

   #create URL and start page at 1
   url_final = url_base + url_page + str(page) + url_tags + tags

   if DEBUG:
      print("URL: " + str(url_final))

   req = urllib.request.Request(
      url_final, 
      data=None, 
      headers={
        'User-Agent': 'e926_dump/0.1 (By randomhusky13)'
        }
    )
   #open website
   f = urllib.request.urlopen(req)
   #open temporary file to dump the source code of the website
   file = open("tmp_html.txt", 'wb')
   #dump the source of the website. Decode and encode to prevent errors on windows.
   src = f.read().decode('iso8859-1')
   file.write(src.encode('utf-8'))
   #close the file
   file.close()
   #open the file for parsing
   file = open("tmp_html.txt", encoding="utf-8")
   lines = file.readlines()

   #check if line of html is for media and get max page number
   for line in lines:
      if DEBUG:
         print(line)
      if ('article id=' in line):
          #find the index where the url starts and ends
          url_start = re.search(r'\b(data-file-url)\b',line)
          url_end = re.search(r'\b(data-large-file-url)\b',line)
          if DEBUG:
             print(line[url_start.start()+15:url_end.start()-2])
          #Add url to list. We move 15 spaces to point to exact start of the url. we move 2 spaces to point to the exact end of the url.
          list_of_urls.append(line[url_start.start()+15:url_end.start()-2])
      #get total number of pages
      if ('div class="paginator"' in line) and (pages_total_set is False):
         pages_total_end = re.search(r'\b(next)\b',line)
         #Check if the string was found.
         if str(pages_total_end) != "None":
            pages_total_start = re.search('>',line[pages_total_end.start()-40:pages_total_end.start()-35])
            if DEBUG:
               print("pages_total: " + str(line[(pages_total_end.start()-(39-pages_total_start.start())):pages_total_end.start()-35]))
            pages_total_temp = int(line[(pages_total_end.start()-(39-pages_total_start.start())):pages_total_end.start()-35])
         #String not found. There is only one page.
         else:
            skip_setting_total_pages = True
            pages_total_set = True
         
         #Check if we need to set the page number. Only done the first iteration.
         if skip_setting_total_pages is False:
            #Check if the pages to download exceed our warning threshold. Ask user if we should continue or if user wishes to override the number of pages
            if pages_total_temp > pages_total_warning:
               print("Warning, the pages to download is " + str(pages_total_temp) + "...  Set how many pages to download and press enter, or press enter to continue downloading all pages: ", end='') 
               pages_override = input()
               #Check if user decided to continue downloading all pages.
               if not pages_override:
                  print("No input provided, downloading all pages")
                  pages_total = pages_total_temp
                  pages_total_set = True
               #Check if user overrode the pages to download.
               elif isinstance(int(pages_override), int):
                  #Check that new page number is valid
                  if (int(pages_override) > pages_total_temp) or (int(pages_override) < 1):
                      print("Error, number of pages grater than pages available to download OR less than 1")
                      exit()
                  print("Setting total of pages to download to " + str(pages_override))
                  pages_total = int(pages_override)
                  pages_total_set = True
               else:
                  print("Error, invalid page number")
                  exit()
            #Total pages does not exceed our warning threshold. Set flag and total pages to download.
            else:
               pages_total_set = True
               pages_total = pages_total_temp
   file.close()

###
#STEP 3, CREATE FOLDER AND DOWNLOAD MEDIA
###
   #Check if tags contain a character that can't be used in directory names
   name_folder = tags
   if '*' or '.' or '"' or '/' or "\\" or '[' or ']' or ':' or ';' or '|' or ',' in name_folder:
      print('Invalid character detected in directory name, replacing character with "-"')
      #Replace any invalid character in the string
      name_folder = name_folder.replace('*','-', len(name_folder))
      name_folder = name_folder.replace('.','-', len(name_folder))
      name_folder = name_folder.replace('"','-', len(name_folder))
      name_folder = name_folder.replace('/','-', len(name_folder))
      name_folder = name_folder.replace('\\','-', len(name_folder))
      name_folder = name_folder.replace('[','-', len(name_folder))
      name_folder = name_folder.replace(']','-', len(name_folder))
      name_folder = name_folder.replace(':','-', len(name_folder))
      name_folder = name_folder = name_folder.replace(';','-', len(name_folder))
      name_folder = name_folder.replace('|','-', len(name_folder))
      name_folder = name_folder.replace(',','-', len(name_folder))

  


   if path.exists(name_folder) is False:
      print('Creating directory "' + name_folder + '"')
      mkdir(name_folder)
   print("Downloading media from page " + str(page) + "...")
   while(len(list_of_urls) > 0):
      #get url from list
      url_download = list_of_urls[-1]
      #remove url from list
      list_of_urls.pop()
      #get name of file
      media_name = url_download[36:]
      if DEBUG:
         print(str(media_name))
      #check if media exists to prevent redownloading it
      if path.exists(name_folder + "/" + str(media_name)) is False:
         with open( name_folder + "/" + str(media_name), 'wb') as media:
            with urllib.request.urlopen(url_download) as response_url:
               media.write(response_url.read())

###
#STEP 4, CHANGE PAGE NUMBER AND GO BACK TO STEP 2 IF THERE IS MORE MEDIA TO DOWNLOAD
###
   page += 1
   if page > pages_total:
      break;
   #Delay the next page request by 2 seconds
   time.sleep(2)
   
print("Finished downloading media")