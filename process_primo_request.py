#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
  Web service that receives an HTTP request
  and produces an openurl for a given target.
  web service holds two variables: doc_id and user_id.
  "doc_id" may be a list of alma mms_ids separated by commas.
  normally, the list of mms_ids refer to primo duplicate
  bibliographic records.
  "user_id" is the user's alma primary id. if
   the user has not logged in primo yet, user_id should be "0".

  this program expects a configuration file, 
  as a command line argument, with the following lines:

  request_map=path/alma_request_table.txt
  html_file=(html template used to display requestable copies)
  error_file=(html file used to display failed request)
  request_label=(docdelivery or reserves or marbl_booking)
  server_hostname=(illiad-server or ares-server or aeon-server)
  get_record_url=path/cgi-bin/get_alma_record?doc_id=
  get_user_url=path/cgi-bin/get_alma_patron_status?user_id=
  sys_email=


"""
__author__ = "bernardo gomez"
__date__ = " february 2016"
import os
import sys 
import re
import cgi
import urllib
import requests
import alma_request
import simple_urlencode
import marcxml
import xml.etree.ElementTree as elementTree
import cgitb; cgitb.enable(display=1, logdir="/tmp")
from datetime import date, timedelta

def is_archive(xml_string):
     """
        It receives a MARCXML string; it parses
        the 008 field; and it examines the 14th 
        byte. It the byte is "p" then the function
        return "Y", otherwise it returns "N".
     """
     archive="X"
     in_string=xml_string.replace("\n","")
     try:
          record=marcxml.biblio(in_string)
     except:
          sys.stderr.write("failed\n")
          return 1
     leader=record.get_field("000")
     #sys.stderr.write("leader:"+str(leader)+"\n")
     archive="X"
     if len(leader) > 0:
          archive=leader[0][13:14]

              ## find out whether BIB is an archive type
          if archive == "p":
              archive="Y"
          else:
              archive="N"
     return archive


def get_record(base_url,docid):
   """
     It receives two parameters:
       'base_url' is the custom webservice that runs
       on the API's proxy server.
       'docid' is the MMS_ID of a given record.
       'base_url' refers to 'get_alma_record' webservice
       that was written by bernardo gomez.
     It returns a MARCXML string and a return code.
     if request to webservice is successful, then
     return code is "0", otherwise is "1".
   """
   xml_string=""
   outcome=1
   request_string=base_url+str(docid)
   try:
      r=requests.get(request_string, timeout=15)
   except:
      sys.stderr.write("api request failed. \n")
      return response,1
   status=r.status_code
   if status == 200:
       xml_string=r.content
   else:
       return xml_string,1
   return xml_string,0


def get_patron_status(get_user_url,user_id):
   """
     It invokes webservice 'get_alma_patron_status'
     to retrieve the patron's ALMA 'user group'.
     It returns two variables:
        the user_group and the outcome.
     if request to webservice is successful, 
     outcome=0, otherwise outcome=1.
   """
   patron_status=""
   outcome=1
   request_string=get_user_url+str(user_id)
   sys.stderr.write(str(request_string)+"\n")
   try:
      r=requests.get(request_string, timeout=15)
   except:
      sys.stderr.write("api request failed. \n")
      return patron_status,1
   status=r.status_code
   if status == 200:
       xml_string=r.content
   else:
       return patron_status,1
       sys.stderr.write("api request failed. code:"+str(status)+"\n")
#user_element: user_group
#<result>
#<code>OK</code>
#<description>valid status</description>
#<patron_status>02</patron_status>
#</result>
   in_string=xml_string.replace("\n","")
   try:
       tree=elementTree.fromstring(in_string)
   except:
      sys.stderr.write("user xml parse failed."+"\n")
      return patron_status,outcome
   try:
      result_code=str(tree.find("code").text)
   except:
      sys.stderr.write("result code parse failed."+"\n")
   if result_code == "OK":
      patron_status=str(tree.find("patron_status").text)
   else:
      sys.stderr.write("failed to read patron_status."+"\n")
      return patron_status,1
   return patron_status,0


def get_items(xml_string):
   """
      it receives a MARCXML string.
      MARCXML contains item information
      in the "999" element.
      it returns a list of "999" elements.
      each element is a string of fields
      separated by "|".
   """
   items=[]
   outcome=1
   in_string=xml_string.replace("\n","")
   try:
       record=marcxml.biblio(in_string)
   except:
       sys.stderr.write("failed\n")
       return
   copies=record.get_field("999")
#01|holding-library|location|material-type|
   for copy in copies:
      subfield=copy.split("\\p")
      material_type="xxxx"
      location="xxxx"
      library="xxxx"
      callnumber="xxxx"
      barcode="xxxx"
      available="xxxx"
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "l":
                  location=str(sf[1:])
            elif sf[0:1] == "t":
                  material_type=str(sf[1:])
            elif sf[0:1] == "m":
                  library=(sf[1:])
            elif sf[0:1] == "a":
                  callnumber=(sf[1:])
            elif sf[0:1] == "i":
                  barcode=(sf[1:])
            elif sf[0:1] == "b":
                  available=(sf[1:])
      if available != "available":
         location="CHECKEDOUT"
      copy_info=library+"|"+location+"|"+material_type+"|"+callnumber+"|"+str(barcode)+"|"+available+"|"
      
      #print copy_info
      items.append(copy_info)
   return items,0

def redirect_to_target(requestable):

    """
      this function deals with a single request link.
      the list has only one element.
      the third field is the target's URL.
    """
    openurl=requestable[0][2].replace("&amp;","&")
    try:
       print "Location:"+openurl
    except:
       print "Location:"+"http://discovere.emory.edu"
    print ""
    return 0

def display_html_notrequestable(record_title,record_docid,message):
   """
     this function displays an error message when
     the request link doesn't have a failed target.
   """
   print '%s' % "Content-Type: text/html; charset=utf-8"
   #print '%s' % "Access-Control-Allow-Origin: *"
   print '%s' % "Access-Control-Allow-Origin: http://discovere.emory.edu"
   print ""

   print "<!DOCTYPE html>"
   print "<html lang=\"en-US\">"
   print "<head>"

   print "<title>Not requestable</title><h3>This title is not requestable.</h3>"
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
   print  "Title:"+record_title
   print  "<p>"
   print  "Record ID:"+" "+record_docid
   print  "<p>"
   print  message
   print "<p>"

   print "</body>"
   print  "</html>"

   return 
def display_html_failure(record_title,message):
   print '%s' % "Content-Type: text/html; charset=utf-8"
   print '%s' % "Access-Control-Allow-Origin: http://discovere.emory.edu"
   print ""

   print "<!DOCTYPE html>"
   print "<html lang=\"en-US\">"
   print "<head>"

   print "<title>No reserves allowed</title><h3>Title can't be placed on reserve.</h3>"
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

def display_html_page(record_title,requestable,html):
 
    print '%s' % "Content-Type: text/html; charset=utf-8"
    print '%s' % "Access-Control-Allow-Origin: http://discovere.emory.edu"
    print ""
    found_title=False
    current_libr="--"
    first_library=True
    if len(requestable) > 1:
          sorted_items=sorted(requestable,key=lambda library: library[0])

    else:
          sorted_items=requestable
    for line in html:
       line=line.rstrip("\n")
       table=re.search("<!--table_starts_here-->", line)
       found_title=re.search("<!--TITLE=-->", line)
       if table:
          print "<table>"
          for copy in sorted_items:
              if copy[0] <> current_libr:
                 if first_library:
                     print "<tr><td nowrap colspan=1 align=left>Items belonging to: <b>"+copy[0]+"</b></td></tr>"
                     first_library=False
                     current_libr=copy[0]
                     ####print "<tr><td nowrap align=left>"+copy[1]+"</td><td align=left><a href=\"javascript:open_win('"+copy[2]+"')\">Request it</a><td></tr>"
                     print "<tr><td nowrap align=left>"+copy[1]+"</td><td align=left><a href=\""+copy[2]+"\">Request it</a><td></tr>"
                 else:
                     print "<tr><td colspan=2><hr></td></tr>"
                     print "<tr><td></td></tr>"
                     print "<tr><td nowrap colspan=1 align=left>Items belonging to: <b>"+copy[0]+"</b></td></tr>"
                     current_libr=copy[0]
                     ###print "<tr><td nowrap align=left>"+copy[1]+"</td><td align=left><a href=\"javascript:open_win('"+copy[2]+"')\">Request it</a><td></tr>"
                     print "<tr><td nowrap align=left>"+copy[1]+"</td><td align=left><a href=\""+copy[2]+"\">Request it</a><td></tr>"
              else:
                     print "<tr><td nowrap align=left>"+copy[1]+"</td><td align=left><a href=\""+copy[2]+"\">Request it</a><td></tr>"
          print "</table>"
       elif found_title:
          line=line.replace("<!--TITLE=-->",record_title)
          print line
       else:
          print line
    return 0

def get_bib_title(xml_string):
   title=""
   outcome=0
   in_string=xml_string.replace("\n","")
   try:
       record=marcxml.biblio(in_string)
   except:
       sys.stderr.write("failed\n")
       return
   title_list=record.get_field("245")
   for title in title_list:
      title_part_a=""
      title_part_b=""
      subfield=title.split("\\p")
      title=""
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                  #title_part_a=str(sf[1:])
                  title_part_a=sf[1:]
                  if title_part_a.isdigit():
                      title_part_a=str(title_part_a)
                  
            if sf[0:1] == "b":
                  #title_part_b=str(sf[1:])
                  title_part_b=sf[1:]
                  if title_part_b.isdigit():
                      title_part_b=str(title_part_b)
      title=title_part_a+" "+title_part_b
      title=title.replace("/","")
      #print "title:"+title

   return title,0

def generate_openurl(xml_string,genre,item_info,illiad_site_list):
   sub_library=""
   item_location=""
   holding_library=""
   material=""
   item_id=""
   callnumber=""
   author_100=""
   author_110=""
   author_700=""
   isbn=""
   issn=""
   pub_place=""
   pub_date=""
   publisher=""
   universal_product_code=""
   title=""
   
   illiad_code={}
   for site in illiad_site_list:
       alma_name,ill_name=site.split(":")
       illiad_code[alma_name]=ill_name

   i_field=item_info.split("|")
   try:
       item_id=str(i_field[4])
       item_id=urllib.quote(item_id)
   except:
       pass
   doc_type=""
   try:
       callnumber=str(i_field[3])
       callnumber=urllib.quote(callnumber)
       if callnumber[0:2] == "XE":
          doc_type="EUARB"
       else:
          doc_type="RB"
   except:
       pass

   try:
       holding_library=str(i_field[0])
       holding_library=urllib.quote(holding_library)
   except:
       pass
   try:
      illiad_libr_code=illiad_code[holding_library]
   except:
      illiad_libr_code="EMU"
      sys.stderr.write("failed to get ILLIAD site code: "+str(holding_library)+"\n")
   #sys.stderr.write("ILLIAD site code: "+str(illiad_libr_code)+"\n")

   try:
       item_location=str(i_field[1])
       item_location=urllib.quote(item_location)
   except:
       pass
   item_location=holding_library+"%20"+item_location
   in_string=xml_string.replace("\n","")
   try:
       record=marcxml.biblio(in_string)
   except:
       sys.stderr.write("failed\n")
       return  "",1
   author_100_field=record.get_field("100")
   for this_author in author_100_field:
      author_part_a=""
      author_part_b=""
      subfield=this_author.split("\\p")
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                  author_part_a=sf[1:]
            if sf[0:1] == "b":
                  author_part_b=sf[1:]
      author_100=author_part_a+" "+author_part_b
      author_100=author_100.replace("/","")
      author_100=author_100.rstrip(" ")
      author_100=author_100.rstrip(",")
      author_100=simple_urlencode.encode(author_100)

   #print author_100
   author_700_field=record.get_field("700")
   for this_author in author_700_field:
      author_part_a=""
      author_part_b=""
      subfield=this_author.split("\\p")
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                  author_part_a=sf[1:]
            if sf[0:1] == "b":
                  author_part_b=sf[1:]
      author_700=author_part_a+" "+author_part_b
      author_700=author_700.replace("/","")
      author_700=author_700.rstrip(" ")
      author_700=author_700.rstrip(",")
      author_700=simple_urlencode.encode(author_700)

   author_110_field=record.get_field("110")
   for this_author in author_110_field:
      author_part_a=""
      author_part_b=""
      subfield=this_author.split("\\p")
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                 author_part_a=sf[1:]
            if sf[0:1] == "b":
                 author_part_b=sf[1:]
      author_110=author_part_a+" "+author_part_b
      author_110=author_110.replace("/","")
      author_110=author_110.rstrip(" ")
      author_110=author_110.rstrip(",")
      author_110=simple_urlencode.encode(author_110)
   #print author_110
   isbn_020=record.get_field("020")
   for field in isbn_020:
      isbn_part_a=""
      subfield=field.split("\\p")
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                  isbn_part_a=sf[1:]
      isbn=isbn_part_a
      isbn=isbn.rstrip(" ")
      isbn=str(isbn)

   #print "isbn:"+str(isbn)
   issn_022=record.get_field("022")
   for field in issn_022:
      issn_part_a=""
      subfield=field.split("\\p")
      for sf in subfield:
         if sf != "":
            if sf[0:1] == "a":
                  issn_part_a=sf[1:]
      issn=issn_part_a
      issn=issn.rstrip(" ")
      issn=str(issn)
   #print "issn:"+str(issn)

   title_info=record.get_field("245")
   title_part_a=""
   title_part_b=""
   for field in title_info:
         subfield=field.split("\\p")
         for sf in subfield:
            if sf != "":
               if sf[0:1] == "a":
                 title_part_a=sf[1:]
               if sf[0:1] == "b":
                 title_part_b=sf[1:]
         try:
            title=title_part_a+" "+title_part_b
            title=title.replace("/","")
            title=simple_urlencode.encode(title)
            title=title[0:100]
            title=title.rstrip("%")  ### truncated url-encoded character
         except:
            sys.stderr.write("failed to get title\n")

   code_024_info=record.get_field("024")
   for field in code_024_info:
      indicator1=str(field[4:5])
      if indicator1 == '1':
         subfield=field.split("\\p")
         for sf in subfield:
            if sf != "":
               if sf[0:1] == "a":
                 universal_product_code=sf[1:]
                 universal_product_code=universal_product_code.rstrip(" ")
                 universal_product_code=str(universal_product_code)
         
   pub_info=record.get_field("264")
   
   for field in pub_info:
      indicator2=str(field[5:6])
      if indicator2 == "1":
         subfield=field.split("\\p")
         for sf in subfield:
            if sf != "":
               if sf[0:1] == "a":
                    pub_place=sf[1:]
                    pub_place=pub_place.rstrip(" ")
                    pub_place=pub_place.rstrip(",")
                    pub_place=pub_place.replace("[","")
                    pub_place=pub_place.replace("]","")
                    pub_place=simple_urlencode.encode(pub_place)
               if sf[0:1] == "b":
                    publisher=sf[1:]
                    publisher=publisher.rstrip(" ")
                    publisher=publisher.rstrip(",")
                    publisher=simple_urlencode.encode(publisher)
               if sf[0:1] == "c":
                    pub_date=sf[1:]
                    pub_date=pub_date.rstrip(" ")
                    pub_date=pub_date.rstrip(",")

   pub_260_info=record.get_field("260")
   for field in pub_260_info:
         subfield=field.split("\\p")
         for sf in subfield:
            if sf != "":
               if sf[0:1] == "a":
                  pub_place=sf[1:]
                  pub_place=pub_place.replace("[","")
                  pub_place=pub_place.replace("]","")
                  pub_place=simple_urlencode.encode(pub_place)
               if sf[0] == 'b': 
                  publisher=sf[1:]
                  publisher=simple_urlencode.encode(publisher)
               if sf[0] == 'c': 
                  pub_date=sf[1:]
                  pub_date=pub_date.replace("[","")
                  pub_date=pub_date.replace("]","")
                  pub_date=simple_urlencode.encode(pub_date)

   #print "pub place:"+str(pub_place)
   #print "publisher:"+str(publisher)
   #print "pub_date:"+str(pub_date)
   try:
     int(pub_date)
     pub_date=str(pub_date)
   except:
     pass
   if isbn == "":
      isbn=issn
   if isbn == "":
      isbn=universal_product_code


   if author_100 <>  "":
          openurl="&amp;rft.genre="+genre+"&amp;rft.btitle="+title+"&amp;rft.title="+title+"&amp;rft.au="+author_100+"&amp;rft.date="+pub_date+"&amp;rft.place="+pub_place+"&amp;rft.pub="+publisher+"&amp;rft.edition="+"&amp;rft.isbn="+isbn+"&amp;rft.callnumber="+callnumber+"&amp;rft.item_location="+item_location+"&amp;rft.barcode="+item_id+"&amp;rft.doctype="+doc_type+"&amp;rft.lib="+illiad_libr_code
   elif author_110 <> "":
          openurl="&amp;rft.genre="+genre+"&amp;rft.btitle="+title+"&amp;rft.title="+title+"&amp;rft.au="+author_110+"&amp;rft.date="+pub_date+"&amp;rft.place="+pub_place+"&amp;rft.pub="+publisher+"&amp;rft.edition="+"&amp;rft.isbn="+isbn+"&amp;rft.callnumber="+callnumber+"&amp;rft.item_location="+item_location+"&amp;rft.barcode="+item_id+"&amp;rft.doctype="+doc_type+"&amp;rft.lib="+illiad_libr_code
   elif author_700 <> "":
          openurl="&amp;rft.genre="+genre+"&amp;rft.btitle="+title+"&amp;rft.title="+title+"&amp;rft.au="+author_700+"&amp;rft.date="+pub_date+"&amp;rft.place="+pub_place+"&amp;rft.pub="+publisher+"&amp;rft.edition="+"&amp;rft.isbn="+isbn+"&amp;rft.callnumber="+callnumber+"&amp;rft.item_location="+item_location+"&amp;rft.barcode="+item_id+"&amp;rft.doctype="+doc_type+"&amp;rft.lib="+illiad_libr_code
   else:
          openurl="&amp;rft.genre="+genre+"&amp;rft.btitle="+title+"&amp;rft.title="+title+"&amp;rft.date="+pub_date+"&amp;rft.place="+pub_place+"&amp;rft.pub="+publisher+"&amp;rft.edition="+"&amp;rft.isbn="+isbn+"&amp;rft.callnumber="+callnumber+"&amp;rft.item_location="+item_location+"&amp;rft.barcode="+item_id+"&amp;rft.doctype="+doc_type+"&amp;rft.lib="+illiad_libr_code

       #sys.stderr.write("openurl:"+openurl+"\n")

  
   return openurl,0


def main():
   """
     This CGI script receives two variables:
        'doc_id', a list of MMS_IDs; and
        'user_id' a patron's primary_id.
        when patron is not logged in, then
        user_id=0.
        This script relies on two webservices:
        'get_alma_record' and 'get_alma_patron_status'.
        It uses the alma_request_table to 
        analyze the items belonging to the bibiographic
        record and the user group and determines what
        it items should display the request link.
   """
   doc_id=""
   user_id=""
   server_hostname=""
   html_file=""
   request_map=""
   form_type="book"
   get_record_url=""
   get_user_url=""
   request_label=""
   illiad_site_codes="BUS:EMU;LAW:EMK;LSC:LSCMAIN;MUSME:EMU;OXFD:EMO;THEO:EMT;UNIV:EMU;CHEM:EMU;HLTH:EMM"

   if len(sys.argv) == 2:
      cfg_file=sys.argv[1]
      try:
         config=open(cfg_file,"r")
      except:
         sys.stderr.write("reserves_request: couldn't open config. file "+cfg_file+"\n")
         #report_failure("ERROR","system failure: wrong configuration file.",doc_id,user_id)
         display_html_failure("","unable to process request: wrong configuration file.")
         return 1
   else:
         sys.stderr.write("reserves_request: no  config. file\n")
         return 1

   try:
     http_method=os.environ["REQUEST_METHOD"]
   except:
     http_method=""


   form = cgi.FieldStorage()

   if len(form) == 0:
       display_html_failure("","unable to process request: doc_id and user_id are missing.")
       return 1
   if  'doc_id' not in form:
      display_html_failure("","unable to process request: doc_id variable is missing.")
      return 1
   if 'user_id' not in form:
      display_html_failure("","unable to process request: user_id variable is missing.")
#     #report_failure("ERROR","user_id variable is missing",doc_id,user_id)
      return 1

   #doc_id="990009263040302486,990009263040302486"
   #doc_id="990012003080302486,990012003080302486"
   #doc_id="990014197400302486"
   #doc_id="990021483420302486"

   try:
       doc_id=form.getfirst('doc_id')
       doc_id=doc_id.replace("emory_aleph","")
       doc_id=doc_id.replace("<","")
       doc_id=doc_id.replace(">","")
       doc_id=doc_id.replace("&","")
   except:
#      #report_failure("ERROR","doc_id variable is missing",doc_id,user_id)
       display_html_failure("","unable to process request: doc_id variable is missing.")
       return 1
   docid_list=[]
   docids=[]
   docid_list=doc_id.split(",")
   for this_id in docid_list:
     sys.stderr.write("doc_id:"+str(this_id)+"\n")
     try:
         int(this_id)
         sys.stderr.write("doc_id(1):"+str(this_id)+"\n")
         #this_id='{:09d}'.format(int(this_id))
         docids.append(this_id)
     except:
         display_html_failure("","unable to process request: this_id is invalid."+str(this_id))
         return 1
   try:
       user_id=form.getfirst('user_id')
   except:
       #report_failure("ERROR","doc_id variable is missing",doc_id,user_id)
       display_html_failure("","unable to process request: user_id variable is missing.")
       return 1


   cfg_pattern=re.compile("(.*?)=(.*)")
   for line in config:
       line=line.rstrip("\n")
       m=cfg_pattern.match(line)
       if m: 
          if m.group(1) == "request_map":
             request_map=m.group(2)
          if m.group(1) == "form_type":
             form_type=m.group(2)
          if m.group(1) == "server_hostname":
             server_hostname=m.group(2)
          if m.group(1) == "html_file":
             html_file=m.group(2)
          if m.group(1) == "get_record_url":
             get_record_url=m.group(2)
          if m.group(1) == "get_user_url":
             get_user_url=m.group(2)
          if m.group(1) == "request_label":
             request_label=m.group(2)
          if m.group(1) == "illiad_site_codes":
             illiad_site_codes=m.group(2)


   config.close()
   if request_map == "":
      display_html_failure("","unable to process request: request map is missing.")
      return 1
   if server_hostname == "":
      display_html_failure("","unable to process request: server_hostname is missing.")
      return 1
   if request_label == "":
      display_html_failure("","unable to process request: request label is missing.")
      return 1

   if get_record_url == "":
      display_html_failure("","unable to process request: get_record_url is missing.")
      return 1

   if get_user_url == "":
      display_html_failure("","unable to process request: get_user_url is missing.")
      return 1

   if html_file == "":
      display_html_failure("","unable to process request: html_file is missing.")
      return 1

   try:
      html=open(html_file,'r')
   except:
      display_html_failure("","unable to process request: no html page.")
      return 1

   try:
      req_file=open(request_map,"r")
   except:
      #report_failure("ERROR","doc_id variable is missing",doc_id,user_id)
      display_html_failure("","unable to process request: system failure (couldn't open request map).")
      sys.stderr.write("couldn't open request map:"+request_map+"\n")
      return 1
   req_file.close()
   illiad_site_list=illiad_site_codes.split(";")
   try:
      context=alma_request.table(request_map)
   except:
      sys.stderr.write("couldn't open request map:"+request_map+"\n")
      return 1

# patron_status|owning_libr|collection|material_type|==><genre>

   try:
      user_group,outcome=get_patron_status(get_user_url,user_id)
   except:
      sys.stderr.write("get_patron_status failed:\n")
      #report_failure("ERROR","get_patron_status failed",doc_id,user_id)
      display_html_failure("","unable to retrieve user information.")
      return 1
   if outcome != 0:
      sys.stderr.write("get_patron_status failed.\n")
      display_html_failure("","unable to retrieve user information.")
      return 1
   requestable=[]
   genre=""
   try:
        for doc_id in docids:
## get_record_url is the custom webservice that produces MARCXML
           xml_string,outcome=get_record(get_record_url,doc_id)
           if outcome == 0:
              archive=is_archive(xml_string)
              item,outcome=get_items(xml_string)
              if outcome == 0:
                for i_info in item:
                   i_field=i_info.split("|")
                   #request_context=str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"
                   #sys.stderr.write(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|"+"\n")
                   menu=context.get_menu(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|")
                   item_to_display=[]
                   if menu != "":
                       req_type=menu.split(",")
                       req_list=[]
                       for req in req_type:
                            req_field=req.split("@")
                            if len(req_field) < 2:
                                req_field.append("xxx")
                            req_list.append(req_field)
                       for req in req_list:
                          if request_label == req[0]:
                             genre=req[1]
                             try:
                                base_openurl,outcome=generate_openurl(xml_string,genre,i_info,illiad_site_list)
                             except:
                                display_html_failure("","unable to process request: generate_openurl failed .")
                                return 1
                             openurl="https://"+server_hostname+"ctx_ver=Z39.88-2004&amp;rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&amp;rfr_id=info:sid/primo%3A"+str(i_field[4])+base_openurl
                             if outcome == 0:
                                item_to_display.append(str(i_field[0]))
                                item_to_display.append(str(i_field[3]))
                                item_to_display.append(openurl)
                                requestable.append(item_to_display)
                                #sys.stderr.write("appended to requestable:"+str(normalized_item)+"\n")
           else:
              sys.stderr.write("get_item_id failed:"+doc_id+"\n")
              #report_failure("ERROR","No user netid exists",normalized_item,user_id)
              display_html_failure("","unable to retrieve item information.")
              return 1
   except:
      #report_failure("ERROR","oracle fetchone failed","",user_id)
      display_html_failure("","unable to get item information..")
      return 1
   item_list=[]
   delimiter="_|_"
   record_title,outcome=get_bib_title(xml_string)
   if outcome == 1:
      display_html_failure("","unable to process request: system failure(6).")
      return 1
   #sys.stderr.write(str(requestable)+"\n")
   if len(requestable) > 1:
       display_html_page(record_title,requestable,html)
      
   elif len(requestable) == 1:
       redirect_to_target(requestable)
       return 0

   else:
       error_message="ERROR"
       display_html_notrequestable(record_title,doc_id,error_message)
   html.close()
   return 0

if __name__=="__main__":
  sys.exit(main())
  
