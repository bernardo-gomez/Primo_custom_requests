#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
  booking_findingaids is a webservice that receives one 
  variable: an alma mms_id ( doc_id). this doc_id corresponds
  to a bibliographic record that is considered an "archive" based
  on the MARC leader field. the webservice looks for the
  URL in a 555 MARC field. this URL points at a finding aid record held
  by the Rose library.
  the webservice displays the URL on the HTTP client.
   
"""
__author__ = 'bernardo gomez'
__date__ = 'january 2016'

import os
import sys 
import re
import cgi
import cgitb; cgitb.enable(display=1, logdir="/tmp")
import requests
import alma_request
import marcxml
import xml.etree.ElementTree as elementTree
from datetime import date, timedelta


def display_html_page(html_file,record_title,record_docid,url):
   """
       it receives the filename of the html page, the record
       title, the mms_id and the finding aid record's URL and
       it builds the html page.
   """
   print '%s' % "Content-Type: text/html; charset=utf-8"
   print '%s' % "Access-Control-Allow-Origin: *"
   print ""
   link=re.compile("<!--LINK=-->")
   title=re.compile("<!--TITLE=-->")
   docid=re.compile("<!--RECORD_ID=-->")
   for line in html_file:
      s=link.search(line)
      if s:
         line=line.replace(r"<!--LINK=-->",url)
      s=title.search(line)
      if s:
         line=line.replace(r"<!--TITLE=-->","Title:"+record_title)
      s=docid.search(line)
      if s:
         line=line.replace(r"<!--RECORD_ID=-->","Record ID:"+str(record_docid))
      print line

   return 

def get_findingaids_url(xml_string):
   """
       it receives an MARCXML string
       of an "archive" record 
       and it looks for the URL stored
       in the MARC 555 field.
   """
   fa_url=""
   outcome=0
   in_string=xml_string.replace("\n","")
   try:
       record=marcxml.biblio(in_string)
   except:
       sys.stderr.write("failed to get findingaids url\n")
       return fa_url,1
   field_list=record.get_field("555")
   for field in field_list:
      subfield=field.split("\\p")
      fa_url=""
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "u":
                fa_url=sf[1:]
                break
   
   outcome=0
   if fa_url == "":
       outcome=1
   return fa_url,outcome


def display_html_failure(record_title,message):
   """
     it builds an html page to display an 
     error message. it also receives the 
     record title, which is not displayed.
   """
   print '%s' % "Content-Type: text/html; charset=utf-8"
   print ""

   print "<!DOCTYPE html>"
   print "<html lang=\"en-US\">"
   print "<head>"

   print "<title>Request failed</title><h3>Request failed.</h3>"
   print  "<style>a.menu_xml_http{font-weight:bold;}</style>"
   print  "<meta charset=\"utf-8\">"
   print  "<meta name=\"viewport\" content=\"width=device-width\">"
   print   "<meta name=\"Keywords\" content=\"\">"
   print   "<meta name=\"Description\" content=\"\">"
   print   "<link rel=\"icon\" href=\"/favicon.ico\" type=\"image/x-icon\">"

   print  "<style type=\"text/css\">"

   print  "</style>"


   print "</head>"

   print "<body>"
   print  "<hr>"
   print  "<p>"
   print  message
   print "<p>"


   print "</body>"
   print  "</html>"
   return 0



def get_bib_title(xml_string):
   """
       it receives an MARCXML string
       of an "archive" record 
       and it gets the record title
       based on the MARC 245 field.
   """
   title=""
   outcome=0
   in_string=xml_string.replace("\n","")
   try:
       record=marcxml.biblio(in_string)
   except:
       sys.stderr.write("failed\n")
       return "",1
   title_list=record.get_field("245")
   for title in title_list:
      title_part_a=""
      title_part_b=""
      subfield=title.split("\\p")
      title=""
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                  title_part_a=sf[1:]
                  if title_part_a.isdigit():
                      title_part_a=str(title_part_a)
            if sf[0:1] == "b":
                  title_part_b=sf[1:]
                  if title_part_b.isdigit():
                      title_part_b=str(title_part_b)
      title=title_part_a+" "+title_part_b
      title=title.replace("/","")
      #title=urllib.quote(title)
      #print "title:"+title

   return title,0



def get_record(base_url,docid):
   """
     it invokes the webservice that retrieves
     the record's MARCXML via ALMA's API.
     it holds two parameters: 
        base_url : the webservice's URL
        docid: the record's mms_id .
     it returns the record's MARCXML
   """
   xml_string=""
   outcome=1
   request_string=base_url+str(docid)
   try:
      r=requests.get(request_string, timeout=10)
   except:
      sys.stderr.write("api request failed. \n")
      return "",1
   status=r.status_code
   if status == 200:
       xml_string=r.content
   else:
       return xml_string,1
   return xml_string,0


def get_item_info(copies):
   """
     it receives a list of
     MARC "999" fields represented
     as text.
     it returns a list of items
     with subfields separated by "|"
   """
   items=[]
   outcome=1
   for copy in copies:
      subfield=copy.split("\\p")
      material_type="xxxx"
      location="xxxx"
      library="xxxx"
      checkedout="N"
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "b":
               if sf[1:] != "available":
                  checkedout="Y"
            elif sf[0:1] == "l":
                  location=str(sf[1:])
            elif sf[0:1] == "t":
                  material_type=str(sf[1:])
            elif sf[0:1] == "m":
                  library=(sf[1:])
      if checkedout == "Y":
         location="CHECKEDOUT"
      copy_info=library+"|"+location+"|"+material_type+"|"
      #print copy_info
      items.append(copy_info)

   return items,0

def get_user_group(api_host,apikey,user_id):
    """
      it invokes ALMA API server to retrieve
      user information. the parameter
      user_id receives the user ID.
      it returns the user's user_group. 
    """
# https://api-na.hosted.exlibrisgroup.com/almaws/v1/users/0036487?user_id_type=all_unique&view=full&expand=none&apikey=l7xxxxxxxxxxxxx
    user_status="xx"
    outcome=1
    request_string=api_host+"almaws/v1/users/"+str(user_id)+"?user_id_type=all_unique&view=full&expand=none&apikey="+apikey
    try:
        response,outcome=api_direct(request_string)
        if outcome != 0:
           return user_status,1
    except:
        sys.stderr.write("get user failed"+"\n")
        return user_status,1

    in_string=response.replace("\n","")
    try:
       tree=elementTree.fromstring(in_string)
    except:
      sys.stderr.write("user xml parse failed."+"\n")
      return user_status,outcome
    try:
      user_status=str(tree.find("user_group").text)
    except:
      sys.stderr.write("result code parse failed."+"\n")
      return user_status,outcome
    #sys.stderr.write("user_group:"+user_status+"\n")
    return str(user_status),0

def api_direct(url):

   """ it performs a GET request through the url. 
       a correct response from ALMA's api server 
       produces a '200' return code.
   """
   response=""
   outcome=1
   try:
      r=requests.get(url, timeout=10)
   except:
      sys.stderr.write("api request failed. \n")
      return response,1
   status=r.status_code
   if status == 200:
       response=r.content
   else:
       response="<result><code>ERROR</code></result>"
       return response,1
   return response,0



def print_error(description):
 """
  it prints an xml page with an error message.
 """
 print '%s' % "Content-Type: text/xml; charset=utf-8"
 print ""
 print '<?xml version="1.0"?>'
 print "<ListErrors>"
 print "<error>"+description+"</error>"
 print "</ListErrors>"
 return


def main():
   """ It supports CGI. It expects a configuration file with the following variables:
     sys_email=
     It supports Cross Origin Resource Sharing (CORS) by recognizing the HTTP "OPTIONS" REQUEST method.
     
   """
   os.environ["LANG"]="en_US.utf8"
   if len(sys.argv) < 2:
      sys.stderr.write("usage: config_file="+"\n")
      print_error("system failure: no configuration file.")
      return 1
   
#######
########

   http_method=os.environ["REQUEST_METHOD"]
   doc_id=""
   user_id="0"
   form = cgi.FieldStorage()
   if len(form) == 0:
       print_error("Expected doc_id and user_id")
       return 1
   if 'doc_id' in form:
        doc_id = form.getfirst("doc_id")
   if 'user_id' in form:
        user_id=form.getfirst('user_id')
   if doc_id == "":
      print_error("Expected doc_id")
      return 1
   doc_id=doc_id.replace(" ","")
   try:
     config=open(sys.argv[1],'r')
   except:
      print_error("system failure: couldn't open config. file:"+sys.argv[1])
      sys.stderr.write("couldn't open config. file:"+sys.argv[1]+"\n")
      return 1
   sys_email="bgomez@emory.edu"
   get_ser_status=""
   request_map=""
   linked_data_host=""
   non_requestable_page=""
   html_page=""
   param=re.compile("(.*?)=(.*)")
   for line in config:
      line=line.rstrip("\n")
      m=param.match(line)
      if m:
         if m.group(1) == "sys_email":
            sys_email=m.group(2)
         if m.group(1) == "get_record_url":
            get_record_url=str(m.group(2))
         if m.group(1) == "api_host":
            api_host=str(m.group(2))
         if m.group(1) == "user_apikey":
            user_apikey=str(m.group(2))
         if m.group(1) == "alma_request_map":
            request_map=str(m.group(2))
         if m.group(1) == "webserver":
            webserver=m.group(2)
         if m.group(1) == "linked_data_host":
            linked_data_host=m.group(2)
         if m.group(1) == "docdelivery":
            docdelivery=m.group(2)
         if m.group(1) == "reserves":
            reserves=m.group(2)
         if m.group(1) == "marbl_booking":
            marbl_booking=m.group(2)
         if m.group(1) == "marbl_finding_aids":
            marbl_finding_aids=m.group(2)
         if m.group(1) == "non_requestable_page":
             non_requestable_page=m.group(2)
         if m.group(1) == "html_page":
             html_file=m.group(2)

   config.close()

   if get_record_url == "":
      print_error("get_record_url url is missing in configuration file.")
      return 1
   if api_host == "":
      print_error("api_host url  is missing in configuration file.")
      return 1
   if user_apikey == "":
      print_error("user_apikey is missing in configuration file.")
      return 1
   if webserver == "":
      print_error("webserver is missing in configuration file.")
      return 1
   if linked_data_host == "":
      print_error("linked_data_host is missing in configuration file.")
      return 1
   if request_map == "":
      print_error("alma_request_map is missing in configuration file.")
      return 1
   if docdelivery == "":
      print_error("docdelivery is missing in configuration file.")
      return 1
   if marbl_booking == "":
      print_error("marbl_booking is missing in configuration file.")
      return 1
   if reserves == "":
      print_error("reserves is missing in configuration file.")
      return 1
   if marbl_finding_aids == "":
      print_error("marbl_finding_aids  is missing in configuration file.")
      return 1
   if html_file == "":
      print_error("html_file is missing in configuration file.")
      return 1
   if non_requestable_page == "":
      print_error("non_requestable_page is missing in configuration file.")
      return 1

   try:
       req_file=open(request_map,'Ur')
   except:
       print_error("System failure. alma_request_map doesn't exist.")
       return 1
   req_file.close()
   try:
      context=alma_request.table(request_map)
   except:
      sys.stderr.write("couldn't open request map:"+request_map+"\n")
      return 1

   try:
       html_f=open(html_file,'Ur')
   except:
       print_error("System failure:"+str(html_file)+" doesn't exist.")
       return 1
   #html_f.close()
   try:
       non_requestable_f=open(non_requestable_page,'Ur')
   except:
       print_error("System failure:"+str(non_requestable_page)+" doesn't exist.")
       return 1
   non_requestable_f.close()


   if doc_id == "":
        print_error("doc_id must be a number")
        #sys.stderr.write("not a number\n")
        return 1

   docid_list=doc_id.split(",")
   copies=[]
   archives=False
   requestable=0
   if user_id == "0":
       user_group="XX"
   else:
       user_group,outcome=get_user_group(api_host,user_apikey,user_id)
   for docid in docid_list:
        try:
           docid=int(docid)
        except:
           print_error("doc_id must be a number")
           return 1
        xml_string,outcome=get_record(get_record_url,docid)
        if outcome == 0:
             in_string=xml_string.replace("\n","")
             try:
                record=marcxml.biblio(in_string)
             except:
                sys.stderr.write("failed\n")
                return 1
             leader=record.get_field("000")
             archive="X"
             if len(leader) > 0:
                    archive=leader[0][11:12]

              ## find out whether BIB is an archive type
             if archive == "p":
                 archive="Y"
             else:
                 archive="N"
             copies=record.get_field("999")
             item,outcome=get_item_info(copies)
             if len(item) > 0:
                for i_info in item:
                   i_field=i_info.split("|")
                   found_it=context.match_it(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|")
                   if found_it:
                      menu=context.get_menu(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|")
                      if menu != "":
                         requestable=requestable+1
                         request_list=menu.split(",")
                         req_type=[]
                         for req in request_list:
                             req_name=req.split("@")
                             req_type.append(req_name[0])
                         request_list=req_type    
                      break
        else:
              sys.stderr.write("get_item_id failed:"+doc_id+"\n")
              #print_error("unable to process request: system failure(1).")
              requestable=0
              #return 1

   # end of block
   if requestable > 0:
       try:
           xml_string,outcome=get_record(get_record_url,doc_id)
       except:
             sys.stderr.write("item_info retrieval failed:"+"\n")
             report_failure("FAILURE","get_record failed:"+str(doc_id),"")
             return 1
       try:
          record_title,outcome=get_bib_title(xml_string)
       except:
          display_html_failure("","unable to process request: system failure..")
          return 1
       try:
          findingaids_url,outcome=get_findingaids_url(xml_string)
       except:
          display_html_failure("","unable to process request: failed to get finding aids URL")
          return 1
       if outcome == 0:
          display_html_page(html_f, record_title,doc_id,findingaids_url)

       else:
          findingaids_url="http://findingaids.library.emory.edu/"
          display_html_page(html_f, record_title,doc_id,findingaids_url)
       html_f.close()
      
   else:
       error_message="<p>Some material is not available for scanning. Please contact <a href=\"mailto:illiadmin-l@listserv.emory.edu\">ILL office</a> for additional information be sure to include the Title and Record ID above.</p>"
       display_html_page(html_f, "ERROR",doc_id,error_message)

   return 0


if __name__=="__main__":
  sys.exit(main())
  

