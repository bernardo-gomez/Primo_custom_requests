#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
  Web service that produces an xml response with
  applicable request links corresponding to 
  a bibliographic alma record and an alma patron record.
  it holds two variables: doc_id and user_id.
  "doc_id" may be a list of alma mms_ids separated by commas.
  normally, the list of mms_ids refer to primo duplicate
  bibliographic records.
  "user_id" is the user's alma primary id. if
   the user has not logged in primo yet, user_id should be "0".

  this program expects a configuration file, as a command line argument, with the following lines:
  sys_email=
  api_host=https://api-na.hosted.exlibrisgroup.com/
  user_apikey=
  alma_request_map=/path_to/webserver/config/alma_request_table.txt
  get_record_url=https://libapiproxyprod1.library.emory.edu/cgi-bin/get_alma_record?doc_id=
  webserver=https://libapiproxyprod1.library.emory.edu/cgi-bin/
  linked_data_host=https://open-na.hosted.exlibrisgroup.com/alma/01GALI_EMORY/bibs/
  docdelivery=https://libapiproxyprod1.library.emory.edu/cgi-bin/document_delivery_primo_new?doc_id=&user_id=
  reserves=https://libapiproxyprod1.library.emory.edu/cgi-bin/process_reserves_primo_new?doc_id=&user_id=
  marbl_booking=https://libapiproxyprod1.library.emory.edu/cgi-bin/process_booking_primo_new?doc_id=&user_id=
  marbl_finding_aids=https://libapiproxyprod1.library.emory.edu/cgi-bin/booking_findingaids?doc_id=&user_id=

  xml output:
  <result>
   <code>OK</code>
   <link>
    <request_link>
     <reserves>url </reserves>
     <docdelivery>url</docdelivery>
     <marbl_booking>url</marbl_booking>
     <marbl_finding_aids>url</marbl_finding_aids>
    </request_link>
    <worldcat_identity>url</worldcat_identity>
   </link>
   <user_group> ...  </user_group>
  </result>


"""

__author__ = "bernardo gomez"
__date__ = " march 2017"

import os
import sys 
import re
import cgi
import cgitb; cgitb.enable(display=1, logdir="/tmp")
import requests
import json
import alma_request
import marcxml
import xml.etree.ElementTree as elementTree
from datetime import date, timedelta


def generate_link(request_list,booking,reserves,docdelivery,finding_aids,doc_id,user_id):
   """
    it produces the "<request_link>" section of the xml output.
    request_list is a list of applicable request types:
    reserves, docdelivery, marbl_booking, marbl_finding_aids.
   """
   combined_link="<request_link>"
   links=""
   if "reserves" in request_list:
      link=reserves
      link=link.replace("doc_id=&","doc_id="+str(doc_id)+"&")
      link=link.replace("user_id=","user_id="+str(user_id))
      links="<reserves>"+link+"</reserves>"
   if "marbl_booking" in request_list:
      link=booking
      link=link.replace("doc_id=&","doc_id="+str(doc_id)+"&")
      link=link.replace("user_id=","user_id="+str(user_id))
      links=links+"<marbl_booking>"+link+"</marbl_booking>"
   if "marbl_finding_aids" in request_list:
      link=finding_aids
      link=link.replace("doc_id=&","doc_id="+str(doc_id)+"&")
      link=link.replace("user_id=","user_id="+str(user_id))
      links=links+"<marbl_finding_aids>"+link+"</marbl_finding_aids>"
   if "docdelivery" in request_list:
      link=docdelivery
      link=link.replace("doc_id=&","doc_id="+str(doc_id)+"&")
      link=link.replace("user_id=","user_id="+str(user_id))
      links=links+"<docdelivery>"+link+"</docdelivery>"
   combined_link=combined_link+links+"</request_link>"
   return combined_link

def get_record(base_url,docid):
   """
     it invokes custom webservice to get alma's MARCXML, including
     items.
     it returns two objects: 
        marcxml string and outcome (0=success, 1= failure)
   """
   xml_string=""
   outcome=1
   request_string=base_url+str(docid)
   try:
      r=requests.get(request_string, timeout=15)
   except:
      sys.stderr.write("api request failed.couldn't get bib record:"+str(docid)+"\n")
      return xml_string,1
   status=r.status_code
   if status == 200:
       xml_string=r.content
   else:
       return xml_string,1
   return xml_string,0

def boundwith(xml_string):
     """
        It receives a MARCXML string; it parses
        the 773 field; and it captures the doc_id
        stored in the "w" subfield.
        the "w" subfield should contain the doc_id
        of the parent record.
        it returns the doc_id, if it exists.
     """
     doc_id=""
     in_string=xml_string.replace("\n","")
     try:
          record=marcxml.biblio(in_string)
     except:
          sys.stderr.write("failed\n")
          return doc_id,1
     field_773=record.get_field("773")
     if len(field_773) > 0:
        subfield=field_773[0].split("\\p")
        for sf in subfield:
           if sf != "":
              if sf[0:1] == "w":
                  doc_id=str(sf[1:])

     return doc_id,0




def print_result(result):
 """
  it sends xml string to the http client (browser). 
 """
 print '%s' % "Content-Type: text/xml; charset=utf-8"
 print '%s' % "Access-Control-Allow-Origin: *"
 print ""
 print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
 print "<result><code>OK</code>"+result+"</result>"
 return


def worldcat_identities_link(doc_id,linked_data_host):
   """
     it retrieves a json-lod (linked data) object from 
     the linked_data_host; it extracts the "creator" element,
     if it exists; and it returns the worldcar identity URL 
     for the creator's authority ID.
     note that the worldcat indentity base URL is hard-coded
     http://worldcat.org/identities/lccn-
   """

   link=""
   outcome=1
   url=linked_data_host+str(doc_id)+".jsonld"
   try:
      r=requests.get(url, timeout=10)
   except:
      return link,1
   status=r.status_code
   if status == 200:
       response=r.content
   else:
       return link,1
   lod_json=json.loads(response,encoding="utf-8")
   creator=""
   try:
      is_list=type (lod_json["creator"]) is list
      if is_list:
         creator=lod_json["creator"][0]["@id"]
      else:
        creator=lod_json["creator"]["@id"]
   except:
        #sys.stderr.write("jsonld doesn't have creator element\n")
        pass
# http://id.loc.gov/authorities/names/
   loc_number=re.compile("http://id.loc.gov/authorities/names/(.+)")
   m=loc_number.match(creator)
   if m:
       name_id=m.group(1)
       link="<worldcat_identity>"+"http://worldcat.org/identities/lccn-"+str(name_id)+"/"+"</worldcat_identity>"
       #sys.stderr.write("name_id:"+str(name_id)+"\n")
   else:
       link="<worldcat_identity></worldcat_identity>"
   #sys.stderr.write("link:"+str(link)+"\n")
   return link,0

def get_item_info(copies):
   """
     it extracts copy information from a list
     of "999" MARC fields. 
     the MARC field is in text format "999|  |\pa____\pb____ etc".
     it returns a list of items with the format
     library|location|material_type
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
      items.append(copy_info)

   return items,0

def get_user_group(api_host,apikey,user_id):
    """
       get_user_group retrieves user_group from ALMA via API.
       it receives the API hostname, the apikey and the user's
       primary ID.
       it returns a string with the user_group code.

    """
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



def print_notok_cors(result):
    """
     it prints xml as a response to a failed OPTIONS request.

    """
    print '%s' % "Content-Type: text/xml; charset=utf-8"
    print '%s' % "Access-Control-Allow-Methods: GET"
    print '%s' % "Access-Control-Allow-Headers: xxx"
    print ""
    print result

def print_ok_cors(result,origin):
 """
  it prints an xml response with the appropriate headers
  to indicate a successful OPTIONS request.
 """
 print '%s' % "Content-Type: text/xml; charset=utf-8"
 print "Access-Control-Allow-Origin: "+origin
 print '%s' % "Access-Control-Allow-Methods: GET"
 print '%s' % "Access-Control-Allow-Headers: EXLREQUESTTYPE,authorization,x-from-exl-api-gateway"
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


def main():
   """ It supports CGI. It expects a configuration file with the following variables:
       sys_email=
       api_host=https://api-na.hosted.exlibrisgroup.com/
       user_apikey=
       alma_request_map=
       get_record_url=
       webserver=
       linked_data_host=
       docdelivery=
       reserves=
       marbl_booking=
       marbl_finding_aids=
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
   #sys.stderr.write("http_method:"+http_method+"\n")
   doc_id=""
   user_id=""
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
   preflight_hostnames=""
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
         if m.group(1) == "preflight_hostnames":
            preflight_hostnames=m.group(2)
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
   if preflight_hostnames == "":
      print_error("preflight_hostnames is missing in configuration file.")
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
#docdelivery=
#reserves=
#marbl_booking=
#marbl_finding_aids=

   try:
       req_file=open(request_map,'Ur')
   except:
       print_error("System failure. alma_request_map doesn't exist.")
       return 1
   req_file.close()
   try:
      context=alma_request.table(request_map)
   except:
      print_error("System failure. couldn't call alma_request module.")
      sys.stderr.write("couldn't call alma_request module"+"\n")
      return 1

   if http_method == "OPTIONS":
       origin_rule=re.compile(r"(http://|https://)(.*)")
       try:
          origin=os.environ["HTTP_ORIGIN"]
       except:
          print_error("NO HTTP_ORIGIN")
          return  1
       try:
           preflight_list=preflight_hostnames.split(";")
       except:
           preflight_list=[]

       m=origin_rule.match(origin)
       if m:
          if m.group(2) in preflight_list:
             #sys.stderr.write("ok_cors medusa\n")
             print_ok_cors("<result><code>OK</code></result>",origin)
             access_control=os.environ["HTTP_ACCESS_CONTROL_REQUEST_HEADERS"]
          else:
             print_notok_cors("<result><code>ERROR</code></result>")
       return 0

   form = cgi.FieldStorage()
   if len(form) == 0:
       print_error("Expected doc_id and user_id")
       return 1
   if 'doc_id' in form:
        doc_id = form.getfirst("doc_id")
   if 'user_id' in form:
        user_id=form.getfirst('user_id')
   else:
      print_error("Expected doc_id and user_id")
      return 1
   #doc_id="990029881400302486" 
   #user_id="0036487"
   doc_id=doc_id.replace(" ","")

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
           #sys.stderr.write("not a number\n")
           return 1
        xml_string,outcome=get_record(get_record_url,docid)
        if outcome == 0:
             in_string=xml_string.replace("\n","")
             try:
                record=marcxml.biblio(in_string)
             except:
                print_error("failed to parse marcxml string.")
                sys.stderr.write("failed\n")
                return 1
             leader=record.get_field("000")
             #sys.stderr.write("leader:"+str(leader)+"\n")
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
             if outcome == 0:
                 if len(item) == 0:
###   title has no copies. it might be a bound-with title.
                    boundwith_docid,outcome=boundwith(in_string)
                    #sys.stderr.write("boundwith:"+str(boundwith_docid)+"\n")
                    if outcome == 0 and boundwith_docid != "":
                       xml_string,outcome=get_record(get_record_url,boundwith_docid)
                       if outcome == 0:
                          in_string=xml_string.replace("\n","")
                          try:
                             record=marcxml.biblio(in_string)
                          except:
                             print_error("failed to parse marcxml string.")
                             sys.stderr.write("failed\n")
                             return 1
                          leader=record.get_field("000")
                          archive="N"
                          if len(leader) > 0:
                             archive=leader[0][11:12]
                             if archive == "p":
                                archive="Y"
                             else:
                                archive="N"
                          copies=record.get_field("999")
                          item,outcome=get_item_info(copies)
                          doc_id=boundwith_docid
                          #sys.stderr.write("boundwith copies:"+str(item)+" "+archive+"\n")
             if len(item) > 0:
                req_type=[]
                for i_info in item:
                   i_field=i_info.split("|")
                   #sys.stderr.write(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|"+"\n")
                   found_it=context.match_it(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|")
                   if found_it:
                      menu=context.get_menu(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|")
                      if menu != "":
                         #sys.stderr.write(str(user_group)+"|"+i_field[0]+"|"+i_field[1]+"|"+i_field[2]+"|"+archive+"|"+" menu:"+str(menu)+"\n")
                         requestable=requestable+1
                         request_list=menu.split(",")
                         for req in request_list:
                             req_name=req.split("@")
                             req_type.append(req_name[0])
                         request_list=req_type    
        else:
              sys.stderr.write("get_item_id failed:"+doc_id+"\n")
              #print_error("unable to process request: system failure(1).")
              requestable=0
              #return 1

   # end of block
   if requestable > 0:
      combined_link=generate_link(request_list,marbl_booking,reserves,docdelivery,marbl_finding_aids,doc_id,user_id)
      #combined_link="<combined_link>"+menu+"</combined_link>"
   else:
      combined_link="<combined_link>"+"</combined_link>"
   identities_link,outcome=worldcat_identities_link(str(docid_list[0]),linked_data_host) 
   result_xml="<link>"+combined_link+identities_link+"</link>"
   result_xml+="<user_group>"+str(user_group)+"</user_group>"
   result_xml=result_xml.replace("&","&amp;")
   print_result(result_xml)
   return 0


if __name__=="__main__":
  sys.exit(main())
  
