'''
This script allows the user to dump media from the website e621.net

This script is distributed free of charge. Please consider supporting
the authors of the media you are downloading and the website hosting
the media.

Copyright (C) 2020 Original author: randomhusky13

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''



import urllib.request
import re
import os.path
from os import path
from os import mkdir
import time

######################################
##### USER CONFIGURABLE SETTINGS #####
######################################

#Set to 1 if you wish to print debug information. Set to 0 to disable printing debug information.
DEBUG = 0
#Set the max number of pages to download without giving a warning
pages_total_warning = 5
#Set the max number of pages to download in an update by default
pages_update_default = 5

#############################################
##### END OF USER CONFIGURABLE SETTINGS #####
#############################################


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

folder_exists_flag = False
skip_setting_total_pages = False
pages_total = 1
pages_total_set = False

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

def fetch_data():
   ###
   # STEP 2, FETCH WEBSITE, IDENTIFY ELEMENTS, AND CREATE DIRECTORY FOR POOLS
   ###

   # set total pages as 1 to terminate after one iteration
   global pages_total
   global pages_total_set
   global skip_setting_total_pages
   global folder_exists_flag
   global pool_page_counter
   global name_folder

   page = 1
   data_missing = False
   media_downloaded = 0

   while True:

      # create URL and start page at 1
      if media_type == "a" or media_type == "c":
         url_final = url_base + url_tags_base + url_page + str(page) + url_tags + tags
      elif media_type == "b" or media_type == "d":
         url_final = url_base + url_pool + str(pool) + url_page + str(page)
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

      # open website
      f = urllib.request.urlopen(req)
      # open temporary file to dump the source code of the website
      file = open(tmp_file_base + tmp_file_name + tmp_file_ext, 'wb')
      # dump the source of the website. Decode and encode to prevent errors on windows.
      src = f.read().decode('iso8859-1')
      file.write(src.encode('utf-8'))
      # close the file
      file.close()
      # open the file for parsing
      file = open(tmp_file_base + tmp_file_name + tmp_file_ext, encoding="utf-8")
      lines = file.readlines()

      # check each line of html for media info, page info, and pool info.
      for line in lines:
         if DEBUG:
            print(line)
         ###
         # GET MEDIA INFO
         ###
         # Check if this is the element for an image
         if ('article id=' in line) or (data_missing is True):
            counter = 0
            # Check for special cases where the element is split in multiple lines
            if ("data-file-url" in line) is False:
               data_missing = True
               continue
            # find the index where the url starts
            url_start = re.search(r'\b(data-file-url)\b', line)
            # Check for special cases where the element is split in multiple lines
            if ("data-large-file-url" in line) is False:
               data_missing = True
               continue
            # find the index where the url ends
            url_end = re.search(r'\b(data-large-file-url)\b', line)
            data_missing = False
            if DEBUG:
               print(line[url_start.start() + 15:url_end.start() - 2])
            # Add url to list. We move 15 spaces to point to exact start of the url. we move 2 spaces to point to the exact end of the url.
            list_of_urls.append(line[url_start.start() + 15:url_end.start() - 2])
         ###
         # GET PAGE INFO
         ###
         # get total number of pages
         if ('div class="paginator"' in line) and (pages_total_set is False):
            pages_total_end = re.search(r'\b(next)\b', line)
            # Check if the string was found.
            if str(pages_total_end) != "None":
               pages_total_start = re.search('>', line[pages_total_end.start() - 40:pages_total_end.start() - 35])
               if DEBUG:
                  print("pages_total: " + str(
                     line[(pages_total_end.start() - (39 - pages_total_start.start())):pages_total_end.start() - 35]))
               pages_total_temp = int(
                  line[(pages_total_end.start() - (39 - pages_total_start.start())):pages_total_end.start() - 35])
            # String not found. There is only one page.
            else:
               skip_setting_total_pages = True
               pages_total_set = True
               pages_total = 1

            # Check if we need to set the page number. Only done the first iteration.
            if skip_setting_total_pages is False:
               # Check if the pages to download exceed our warning threshold. Ask user if we should continue or if user wishes to override the number of pages
               if pages_total_temp > pages_total_warning:
                  print("Warning, the pages to download is " + str(
                     pages_total_temp) + "...  Set how many pages to download and press enter, or press enter to continue downloading all pages: ",
                        end='')
                  pages_override = input()
                  # Check if user decided to continue downloading all pages.
                  if not pages_override:
                     print("No input provided, downloading all pages")
                     pages_total = pages_total_temp
                     pages_total_set = True
                  # Check if user overrode the pages to download.
                  elif isinstance(int(pages_override), int):
                     # Check that new page number is valid
                     if (int(pages_override) > pages_total_temp) or (int(pages_override) < 1):
                        print("Error, number of pages grater than pages available to download OR less than 1")
                        exit()
                     print("Setting total of pages to download to " + str(pages_override))
                     pages_total = int(pages_override)
                     pages_total_set = True
                  else:
                     print("Error, invalid page number")
                     exit()
               # Total pages does not exceed our warning threshold. Set flag and total pages to download.
               else:
                  pages_total_set = True
                  pages_total = pages_total_temp
         ###
         # GET POOL INFO
         ###
         # Get pool name.
         if ("pool-category-series" in line) and (folder_exists_flag is False):
            # Find the start of the pool name. The end of this line has 4 unwanted characters, hence the -5 (position of last wanted character)"
            pool_name = str(line[line.find('">') + 2:-5])
            print("Pool name: " + pool_name)
      file.close()

      # If the directory hasn't been created at this point, then the media type is a pool.
      if folder_exists_flag is False:
         # Check if pool directory exists. if not, create it
         if path.exists("pools") is False:
            print("Creating directory to store pools")
            mkdir("pools")
         os.chdir("pools")
         # Check if proposed directory name contains a character that can't be used in directory names
         name_folder = check_invalid_chars(pool_name)
         # Replace spaces with underscores
         name_folder = name_folder.replace(' ', '_', len(name_folder))
         # Check if directory already exists
         if path.exists(name_folder) is False:
            print('Creating directory "' + name_folder + '"')
            mkdir(name_folder)
            # Create a file with the pool ID for easy tracking without browser
            if path.exists(name_folder + "/" + pool) is False:
               pool_id = open(name_folder + "/ID_" + pool, 'wb')
               pool_id.close()

         folder_exists_flag = True
      file.close()

      ###
      # STEP 3, DOWNLOAD MEDIA
      ###
      print("Downloading media from page " + str(page) + "...")
      while (len(list_of_urls) > 0):
         # create the name of the file based on the media type
         if media_type == "a" or media_type == "c":
            # get url from list last to first
            url_download = list_of_urls[-1]
            # remove last url from list
            list_of_urls.pop()
            # get name of media
            media_name = url_download[36:]
         elif media_type == "b" or media_type == "d":
            # get url from list first to last (pools are always in order. The fist link of page 1 will be pool element 1, the second element 2, and so on.)
            url_download = list_of_urls[0]
            # remove first url from list
            list_of_urls.pop(0)
            # get extension of media
            media_extension = url_download[56:]
            media_name = str(pool_page_counter) + str(media_extension[media_extension.find('.'):])
         else:
            print("Unknown media type. Exiting")
            exit()

         if DEBUG:
            print(str(media_name))
         # check if media exists to prevent redownloading it
         if path.exists(name_folder + "/" + str(media_name)) is False:
            with open(name_folder + "/" + str(media_name), 'wb') as media:
               with urllib.request.urlopen(url_download) as response_url:
                  media_downloaded += 1
                  media.write(response_url.read())
         # increase page number for pools
         pool_page_counter += 1

      ###
      # STEP 4, CHANGE PAGE NUMBER AND GO BACK TO STEP 2 IF THERE IS MORE MEDIA TO DOWNLOAD
      ###
      page += 1
      if page > pages_total:
         break;
      # Delay the next page request by 2 seconds
      time.sleep(2)

   print("Finished downloading media")
   # Check if temporary file exists in current directory (for dumps grater than 1 page)
   if path.exists(tmp_file_base + tmp_file_name + tmp_file_ext):
      os.remove(tmp_file_base + tmp_file_name + tmp_file_ext)
   os.chdir("../")
   # Check if temporary file exists in script's directory (for dumps of at least 1 page)
   if path.exists(tmp_file_base + tmp_file_name + tmp_file_ext):
      os.remove(tmp_file_base + tmp_file_name + tmp_file_ext)


   print( str(media_downloaded) + " media was downloaded")
   return

def update_directories():

   global tmp_file_name
   global name_folder
   global skip_setting_total_pages
   global pages_total
   global pages_total_set
   global tags
   global folder_exists_flag
   total_number_of_directories = 0
   current_number_of_directories = 0
   list_of_directories = []

   if path.exists("tags") is False:
      print('Directory "tags" not found. Please download some media first')
      return

   skip_setting_total_pages = True
   pages_total_set = True
   folder_exists_flag = True


   print("Warning! I will download from the " + str(pages_update_default) + " most recent pages for all the existing tag directories")

   print("Do you want to continue? (type y and press enter to continue or type anything else and press enter to exit)")

   if input() != "y":
      print("Exiting!")
      exit()

   pages_total = pages_update_default


   #change to directory where the directories containing the media is
   os.chdir("tags")
   #get number of items
   for directory in os.listdir('.'):
      if "txt" in directory:
         continue
      #save information into a list as path might change in another part of the script during runtime
      list_of_directories.append(os.fsdecode(directory))
      total_number_of_directories += 1
   #iterate through each directory ang get its name
   for directory_name in list_of_directories:
      if "txt" in directory_name:
         continue
      current_number_of_directories += 1
      print("Downloading media... " + str(current_number_of_directories) + "/" + str(total_number_of_directories) + "   | " + directory_name)
      #path might not be right after returning from fetch_data. Change into right directory
      if "tags" not in os.getcwd():
         os.chdir("tags")
      name_folder = directory_name
      tags = name_folder
      tmp_file_name = name_folder
      fetch_data()

   return

def find_folder(list_of_tags, list_of_directories):

   if not list_of_tags:
      #No more tags left to check. return list_of_directories
      return list_of_directories

   if not list_of_directories:
      #There are still tags to check but there are no more existing directories.
      #Folder does not exist. return list_of_directories
      return list_of_directories

   new_list_of_directories = []

   #get last tag from the tags list
   tag_to_check = list_of_tags[-1]
   #remove last tag from the list
   del list_of_tags[-1]

   for name_of_directory in list_of_directories:
      #check if the tag exists in the name of the directory
      if tag_to_check in name_of_directory:
         #if it exists, then add the name of the directory to the new list.
         new_list_of_directories.append(name_of_directory)

   #the retuned list will be filtered out with the remaining tags
   new_list_of_directories = find_folder(list_of_tags, new_list_of_directories)

   #return the final list
   return new_list_of_directories


def folder_exists(directory_name):
   list_of_directories = []


   # get number of items
   for directory in os.listdir('.'):
      if "txt" in directory:
         continue
      # save information into a list
      list_of_directories.append(os.fsdecode(directory))

   #replace plus signs with spaces
   tags = directory_name.replace("+", " ")

   list_of_tags = tags.split()

   list_of_found_directores = find_folder(list_of_tags, list_of_directories)

   name_of_directory = ""

   for element in list_of_found_directores:
      #Final check. If we have multiple results, then there might be additional tags in the directory name.
      #Only choose the one directory that has the same size as the request.
      if len(directory_name) == len(element):
         name_of_directory = element
         break

   return name_of_directory


def update_pools():

   global pool
   global folder_exists_flag
   global tmp_file_name
   global pool_page_counter
   global pages_total_set
   global skip_setting_total_pages

   list_of_existing_pools = []
   list_of_existing_pools_IDs = []
   #check if the directory pools exist
   if path.exists("pools") is False:
      print("Pools directory not found. Please download some media first")
      return

   os.chdir("pools")

   #get a list of the existing directories. This list will contain the names of the pools.
   for directory in os.listdir('.'):
      list_of_existing_pools.append(os.fsdecode(directory))

   #check that the pools directory is not empty
   if not list_of_existing_pools:
      print("No existing pools found. Please download some media first")

   #make a list of pools IDs
   for element in list_of_existing_pools:
      #go into pool directory
      os.chdir(element)
      #find pool ID
      ID_found = False
      for file in os.listdir('.'):
         if "ID" in file:
            temp = os.fsdecode(file)
            list_of_existing_pools_IDs.append(temp[3:])
            ID_found = True
      #go up one directory so next iteration can go into another pool directory
      os.chdir("../")
      if ID_found == False:
         print("Error, a pool directory is missing the ID file. Please redownload the pool and do not remove the ID file")
         print("Directory missing ID: " + element)
         exit()

   # go up one directory so fetch code can do its normal check of pool directories
   os.chdir("../")
   #Iterate through the list of pool IDs and update each one
   for pool_id in list_of_existing_pools_IDs:
      #update the global variable that contains the pool ID for the URL
      pool = pool_id
      tmp_file_name = pool
      #get the name of the existing directory
      pool_directory_name = list_of_existing_pools[0]
      #delete the directory where the current pool media will be stored from the list.
      del list_of_existing_pools[0]

      print("----")
      print("Updating pool ID " + pool + " in directory " + pool_directory_name)
      #Reset variables and flags
      folder_exists_flag = False
      pool_page_counter = 1
      pages_total_set = False
      skip_setting_total_pages = False
      fetch_data()
      print("----")
      

   return

print("This script is distributed free of charge. Please consider supporting")
print("the authors of the media you are downloading and the website hosting")
print("the media.")
print("")
print("Copyright (C) 2020 Original author: randomhusky13")
print("")
print("This program comes with ABSOLUTELY NO WARRANTY")
print("This is free software, and you are welcome to redistribute it")
print("under certain conditions. By using this software, you are agreeing")
print("to the terms established in the license. For more information,")
print("check license GPLv3. <http://www.gnu.org/licenses/>")
print("")
print("")

#clean tmp files left behind to avoid problems
for elem in os.listdir("."):
   if "txt" in elem:
      os.remove(elem)

if path.exists("tags") is True:
   os.chdir("tags")
   for elem in os.listdir("."):
      if "txt" in elem:
         os.remove(elem)
   os.chdir("../")

if path.exists("pools") is True:
   os.chdir("pools")
   for elem in os.listdir("."):
      if ".txt" in elem:
         os.remove(elem)
   os.chdir("../")

###
#STEP 1, GET TAGS OR POOL ID, CREATE DIRECTORY FOR TAGS, AND CREATE URL
###

#Get media type from user
while(True):

   #Get type of media to download from the user
   print("Type the character for the desired operation and press enter ")
   print('"a" Download tag based media')
   print('"b" Download pool based media')
   print('"c" Update existing tag based media directories')
   print('"d" Update existing pool based media directories')
   media_type = input()
   #Check if the input is valid
   if (( "a" in media_type) or ( "b" in media_type) or ( "c" in media_type) or ( "d" in media_type)) and (len(media_type) == 1):
      break
   #
   media_type_counter -= 1
   if media_type_counter > 0:
      print("Error in input. Try again")
   else:
      print("Error limit exceeded. Exiting!")
      exit()

if media_type == "a":
   print("Introduce tags, each one separated by a single space: ", end ='')
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

   found_directory = folder_exists(name_folder)
   #check if directory needs to be created
   if found_directory == "":
      #directory does not exist. Create one
      print('Creating directory "' + name_folder + '"')
      mkdir(name_folder)
   else:
      #A directory was found, do not create a new one but update the name_folder to use the existing one.
      print("Directory already created: " + found_directory)
      name_folder = found_directory
   folder_exists_flag = True

   if DEBUG:
      print("TAGS MOD: " + str(tags))

   fetch_data()
elif media_type == "b":
   print("Introduce pool number: ", end ='')
   pool = input()
   #We use the pool id for our temporary file name since it's simpler and we won't get the real pool name until after one access to the website. Hence, the tags' directory name is known beforehand and can be set at this step, but the pool needs to be set in the next step.
   tmp_file_name = pool
   if DEBUG:
      print("POOL: " + str(pool))
   fetch_data()

elif media_type == "c":
   update_directories()

elif media_type == "d":
   update_pools()
else:
   print("Unknown media type. Exiting")
   exit()



