import urllib.request
import re
import os.path
from os import path
from os import mkdir
import time

DEBUG = 0
#Set the max number of pages to download without giving a warning
pages_total_warning = 5

#strings needed to build the website addresses
url_base = 'https://e621.net/'
url_tags_base = 'posts'
url_pool = 'pools/'
url_page = '?page='
url_tags = '&tags='

#strings neeeded to build the temporary files
tmp_file_base = "tmp_html_"
tmp_file_ext = ".txt"

list_of_urls = []

folder_exists = False
data_missing = False

type_of_media = 'unknown'

pool_page_counter = 1
media_type_counter = 3

###
# Method name: check_invalid_chars
# Arguments: string_to_check - string - string containing characters to check
# Return: string_to_check - string - updated string with replaced characters
###

def check_invalid_chars( string_to_check ):
   if any(i in string_to_check for i in '*."/\\[]:;|,'):
      print('Invalid character detected in directory name, replacing character with "-"')
      #Replace any invalid character in the string
      string_to_check = string_to_check.replace('*','-', len(string_to_check))
      string_to_check = string_to_check.replace('.','-', len(string_to_check))
      string_to_check = string_to_check.replace('"','-', len(string_to_check))
      string_to_check = string_to_check.replace('/','-', len(string_to_check))
      string_to_check = string_to_check.replace('\\','-', len(string_to_check))
      string_to_check = string_to_check.replace('[','-', len(string_to_check))
      string_to_check = string_to_check.replace(']','-', len(string_to_check))
      string_to_check = string_to_check.replace(':','-', len(string_to_check))
      string_to_check = string_to_check = string_to_check.replace(';','-', len(string_to_check))
      string_to_check = string_to_check.replace('|','-', len(string_to_check))
      string_to_check = string_to_check.replace(',','-', len(string_to_check))
   return string_to_check



###
#STEP 1, GET TAGS OR POOL NUMBER, CREATE DIRECTORY FOR TAGS, AND CREATE URL
###

#Get media type from user
while(True):

   #Get type of media to download from the user
   print("Type the character for the type of media to download and press enter ")
   print('"a" tag based media')
   print('"b" pool based media')
   media_type = input()
   #Check if the input is valid
   if (( "a" in media_type) or ( "b" in media_type)) and (len(media_type) is 1):
      break
   #
   media_type_counter -= 1
   if media_type_counter > 0:
      print("Error in input. Try again")
   else:
      print("Error limit exceeded. Exiting!")
      exit()

if media_type is "a":
   print("Introduce tags: ", end ='')
   tags = input()
   if DEBUG:
      print("TAGS: " + str(tags))

   #replace white spaces with plus signs   
   tags = tags.replace(" ", "+")
   #Check if proposed directory name contains a character that can't be used in directory names
   name_folder = check_invalid_chars(tags)
   tmp_file_name = name_folder
   #Check if tags directory exists. if not, create it
   if path.exists("tags") is False:
      print("Creating directory to store tag dumps")
      mkdir("tags")
   os.chdir("tags")
   #check if directory needs to be created
   if path.exists(name_folder) is False:
      print('Creating directory "' + name_folder + '"')
      mkdir(name_folder)
   folder_exists = True

   if DEBUG:
      print("TAGS MOD: " + str(tags))
elif media_type is "b":
   print("Introduce pool number: ", end ='')
   pool = input()
   #We use the pool id for our temporary file name since it's simpler and we won't get the real pool name until after one access to the website. Hence, the tags' directory name is known beforehand and can be set at this step, but the pool needs to be set in the next step.
   tmp_file_name = pool
   if DEBUG:
      print("POOL: " + str(pool))
else:
   print("Unknown media type. Exiting")
   exit()


   
   
   
   
   
   
   
###
#STEP 2, FETCH WEBSITE, IDENTIFY ELEMENTS, AND CREATE DIRECTORY FOR POOLS
###   

#set total pages as 1 to terminate after one iteration
pages_total = 1
pages_total_set = False
page = 1
skip_setting_total_pages = False

while True:   

   #create URL and start page at 1
   if media_type is "a":
      url_final = url_base + url_tags_base + url_page + str(page) + url_tags + tags
   elif media_type is "b":
      url_final = url_base + url_pool + str(pool) + url_page
   else:
      print("Unknown media type. Exiting")
      exit()

   if DEBUG:
      print("URL: " + str(url_final))


   req = urllib.request.Request(
      url_final, 
      data=None, 
      headers={
        'User-Agent': 'e621_dump/0.1 (By randomhusky13)'
        }
    )

   #open website
   f = urllib.request.urlopen(req)
   #open temporary file to dump the source code of the website
   file = open(tmp_file_base + tmp_file_name + tmp_file_ext, 'wb')
   #dump the source of the website. Decode and encode to prevent errors on windows.
   src = f.read().decode('iso8859-1')
   file.write(src.encode('utf-8'))
   #close the file
   file.close()
   #open the file for parsing
   file = open(tmp_file_base + tmp_file_name + tmp_file_ext, encoding="utf-8")
   lines = file.readlines()

   #check if line of html is for media and get max page number
   for line in lines:
      if DEBUG:
         print(line)
      #Check if this is the element for an image
      if ('article id=' in line) or (data_missing is True):
          counter = 0
          #Check for special cases where the element is split in multiple lines
          if ("data-file-url" in line) is False:
             data_missing = True
             continue
          #find the index where the url starts
          url_start = re.search(r'\b(data-file-url)\b',line)
          #Check for special cases where the element is split in multiple lines
          if ("data-large-file-url" in line) is False:
             data_missing = True
             continue
          #find the index where the url ends
          url_end = re.search(r'\b(data-large-file-url)\b',line)
          data_missing = False
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
          #Get pool name.
      if ("pool-category-series" in line) and (folder_exists is False):
         #Find the start of the pool name. The end of this line has 4 unwanted characters, hence the -5 (position of last wanted character)"
         pool_name = str(line[line.find('">')+2:-5])
         print("Pool name: " + pool_name)
   file.close()

   
   
   #If the directory hasn't been created at this point, then the media type is a pool.
   if folder_exists is False:
      #Check if pool directory exists. if not, create it
      if path.exists("pools") is False:
         print("Creating directory to store pools")
         mkdir("pools")
      os.chdir("pools")
      #Check if proposed directory name contains a character that can't be used in directory names
      name_folder = check_invalid_chars(pool_name)
      #Replace spaces with underscores
      name_folder = name_folder.replace(' ','_', len(name_folder))
      #Check if directory already exists
      if path.exists(name_folder) is False:
         print('Creating directory "' + name_folder + '"')
         mkdir(name_folder)
         #Create a file with the pool ID for easy tracking without browser
         if path.exists(name_folder + "/" + pool) is False:
            pool_id = open(name_folder + "/ID_" + pool, 'wb')
            pool_id.close()
            
      folder_exists = True
   file.close()
###
#STEP 3, DOWNLOAD MEDIA
###

   print("Downloading media from page " + str(page) + "...")
   while(len(list_of_urls) > 0):

      
      #create the name of the file based on the media type
      if media_type is "a":
         #get url from list last to first
         url_download = list_of_urls[-1]
         #remove last url from list
         list_of_urls.pop()
         #get name of media
         media_name = url_download[36:]
      elif media_type is "b":
         #get url from list first to last (pools are always in order. The fist link of page 1 will be pool element 1, the second element 2, and so on.)
         url_download = list_of_urls[0]
         #remove first url from list
         list_of_urls.pop(0)
         #get extension of media
         media_extension = url_download[56:]
         media_name = str(pool_page_counter) + str(media_extension[media_extension.find('.'):])
      else:
         print("Unknown media type. Exiting")
         exit()

      if DEBUG:
         print(str(media_name))
      #check if media exists to prevent redownloading it
      if path.exists(name_folder + "/" + str(media_name)) is False:
         with open( name_folder + "/" + str(media_name), 'wb') as media:
            with urllib.request.urlopen(url_download) as response_url:
               media.write(response_url.read())
      #increase page number for pools
      pool_page_counter += 1

###
#STEP 4, CHANGE PAGE NUMBER AND GO BACK TO STEP 2 IF THERE IS MORE MEDIA TO DOWNLOAD
###
   page += 1
   if page > pages_total:
      break;
   #Delay the next page request by 2 seconds
   time.sleep(2)
   
print("Finished downloading media")
#Check if temporary file exists in current directory (for dumps grater than 1 page)
if path.exists(tmp_file_base + tmp_file_name + tmp_file_ext):
   os.remove(tmp_file_base + tmp_file_name + tmp_file_ext)
os.chdir("../")
#Check if temporary file exists in script's directory (for dumps of at least 1 page)
if path.exists(tmp_file_base + tmp_file_name + tmp_file_ext):
   os.remove(tmp_file_base + tmp_file_name + tmp_file_ext)