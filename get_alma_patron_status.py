#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
    this RESTful webservice receives an alma user_id, retrieves the user status and
    returns it as part of an XML object.
    this webservice support Cross Origin Resource Sharing (CORS) via the OPTIONS request 
    because the HTTP client with a primo session may issue a request to this webservice.

"""
__author__='bernardo gomez'
__date__='january 2016'

import os
import sys 
import re
import cgi
import requests
import cgitb; cgitb.enable(display=1, logdir="/tmp")
import xml.etree.ElementTree as elementTree
from datetime import date, timedelta

def print_ok_cors(result,origin):
 """
  it prints xml or text page with a positive OPTIONS response.
 """
 print '%s' % "Content-Type: text/xml; charset=utf-8"
 print "Access-Control-Allow-Origin: "+origin
 print '%s' % "Access-Control-Allow-Methods: GET"
 print '%s' % "Access-Control-Allow-Headers: EXLREQUESTTYPE"
 print ""
 print result
 return 

def print_notok_cors(result):
    """
     it prints xml as a response to a failed OPTIONS request.

    """
    print '%s' % "Content-Type: text/xml; charset=utf-8"
    print '%s' % "Access-Control-Allow-Methods: GET"
    print '%s' % "Access-Control-Allow-Headers: xxx"
    print ""
    print result
    return 

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



def display_html_failure(code,description,status):
   """ 
        it displays an XML object with an error message.
   """
   print '%s' % "Content-Type: text/xml; charset=utf-8"
   print '%s' % "Access-Control-Allow-Origin: *"
   print ""
   print '<?xml version="1.0"?>'
   print "<result>"
   print "<code>"+code+"</code>"
   print "<description>"+description+"</description>"
   print "<patron_status>"+str(status)+"</patron_status>"
   print "</result>"
   return 0

def get_user_status(api_host,apikey,user_id):
    """
      it sends a RESTful request to ALMA API server to retrieve user information based
       on the user's primary_id.
    """
# https://api-na.hosted.exlibrisgroup.com/almaws/v1/users/0036487?user_id_type=all_unique&view=full&expand=none&apikey=l7xxxxxxxx
    user_status=""
    outcome=1
    request_string=api_host+"almaws/v1/users/"+str(user_id)+"?user_id_type=all_unique&view=full&expand=none&apikey="+apikey

    try:
        response,outcome=api_direct(request_string)
        if outcome != 0:
           return "",1
    except:
        sys.stderr.write("get user failed"+"\n")
        return "",1

    in_string=response.replace("\n","")
    try:
       tree=elementTree.fromstring(in_string)
    except:
      sys.stderr.write("user xml parse failed."+"\n")
      return patron_status,outcome
    try:
      user_status=str(tree.find("user_group").text)
    except:
      sys.stderr.write("result code parse failed."+"\n")
      return user_status,outcome

    return str(user_status),0

def report_success(code,description,status):
  """
     it sends an XML object as a response to 
     a successful GET request.
  """
  print '%s' % "Content-Type: text/xml; charset=utf-8"
  print '%s' % "Access-Control-Allow-Origin: *"
  print ""
  print '<?xml version="1.0"?>'
  print "<result>"
  print "<code>"+code+"</code>"
  print "<description>"+description+"</description>"
  print "<patron_status>"+str(status)+"</patron_status>"
  print "</result>"
  return


def main():
   """
        webservice expects a user primary_id in the HTTP request.
        script expects a configuration file in the command line.
        configuration file has "preflight_hostnames" variable that
        contains the authorized hostnames for the OPTIONS request.
        the OPTIONS request is part of CORS procedure, since the
        browser might generating a GET request.
   """
   user_id=""

   #sys.stderr.write("http_method:"+http_method+"\n")
   if len(sys.argv) < 2:
      sys.stderr.write("usage: config_file="+"\n")
      print_error("system failure: no configuration file.")
      return 1
   
   try:
     http_method=os.environ["REQUEST_METHOD"]
   except:
     http_method=""

   try:
     config=open(sys.argv[1],'r')
   except:
      print_error("system failure: couldn't open config. file:"+sys.argv[1])
      sys.stderr.write("couldn't open config. file:"+sys.argv[1]+"\n")
      return 1

   api_host=""
   apikey=""
   preflight_hostnames=""
   param=re.compile("(.*?)=(.*)")
   for line in config:
      line=line.rstrip("\n")
      m=param.match(line)
      if m:
         if m.group(1) == "api_host":
            api_host=str(m.group(2))
         if m.group(1) == "apikey":
            apikey=str(m.group(2))
         if m.group(1) == "preflight_hostnames":
            preflight_hostnames=str(m.group(2))

   if api_host == "":
      print_error("api_host is missing in configuration file.")
      return 1
   if apikey == "":
      print_error("apikey is missing in configuration file.")
      return 1
   if preflight_hostnames == "":
      print_error("preflight_hostnames is missing in configuration file.")
      return 1


   try:
       preflight_list=preflight_hostnames.split(";")
   except:
       preflight_list=[]

   if http_method == "OPTIONS":
       try:
          origin=os.environ["HTTP_ORIGIN"]
       except:
          display_html_failure("ERROR","NO OPTIONS","")
          return  1

       origin_rule=re.compile(r"(http://|https://)(.*)")
       m=origin_rule.match(origin)
       if m:
          if m.group(2) in preflight_list:
             #sys.stderr.write("ok_cors medusa\n")
             print_ok_cors("<result><code>OK</code></result>",origin)
             #access_control=os.environ["HTTP_ACCESS_CONTROL_REQUEST_HEADERS"]
          else:
             print_notok_cors("<result><code>ERROR</code></result>")
       return 0


   form = cgi.FieldStorage()

   if len(form) == 0:
       display_html_failure("ERROR","unable to process request: user_id is  missing.","")
       return 1
   if 'user_id' not in form:
      display_html_failure("ERROR","unable to process request: user_id is  missing.","")
      return 1

   try:
       user_id=form.getfirst('user_id')
       user_id=user_id.lower()    #### alma stores neitds in lower case.
       user_id=user_id.replace("<","")
       user_id=user_id.replace(">","")
       user_id=user_id.replace("&","")
   except:
       display_html_failure("ERROR","unable to process request: user_id variable is missing.","")
       return 1

#######
## user_id="0" correspond to primo queries where user has not logged in. no need to call alma API.
## it's safe to return user_group = "XX"
   if str(user_id) == "0":
	report_success("OK","valid status","XX")
        return 0
#######
   try:
      borrower_status,outcome=get_user_status(api_host,apikey,user_id)
   except:
      display_html_failure("ERROR","unable to retrieve user information for" +user_id,"")
      return 1
   if outcome <> 0:
      display_html_failure("ERROR","unable to process request: user " +user_id+" doesn't exist","")
      return 1

   report_success("OK","valid status",borrower_status)

   return 0

if __name__=="__main__":
  sys.exit(main())
  
